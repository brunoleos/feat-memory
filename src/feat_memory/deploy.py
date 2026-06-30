"""deploy.py — Deploy idempotente da metodologia em um projeto.

Subcomando da CLI: `feat-memory deploy <target>`. Copia templates,
instala hooks e configura .gitignore/.gitattributes no target.

Comportamento por arquivo:
    AGENTS.md            → bloco com sentinelas markdown, refrescado a cada
                            deploy; conteúdo do usuário fora do bloco nunca
                            é tocado
    CLAUDE.md            → copia se ausente; deixa quieto se existe
    .feat-memory/changelog/UNRELEASED.md → pula se existe (volátil)
    skills/              → sempre atualizadas (conteúdo de metodologia)
    .claude/agents/      → subagents do Claude Code, sempre atualizados
                            (wrapper fino que pré-carrega a skill homônima)
    .gitattributes       → bloco com sentinelas, refrescado a cada deploy
    .gitignore           → bloco com sentinelas garantindo .feat-memory-deploy/
    pastas               → cria se não existem
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from importlib.resources import as_file, files
from importlib.resources.abc import Traversable
from pathlib import Path

from feat_memory.governance import install_hooks


SENTINEL_BEGIN = "# >>> feat-memory >>>"
SENTINEL_END = "# <<< feat-memory <<<"

# Sentinelas markdown (HTML comments) para o bloco da metodologia em AGENTS.md.
# Diferentes das sentinelas shell-style usadas em .gitignore/.gitattributes
# porque `#` em markdown é heading, não comentário.
MD_SENTINEL_BEGIN = "<!-- >>> feat-memory >>> -->"
MD_SENTINEL_END = "<!-- <<< feat-memory <<< -->"


def _data_path(*parts: str) -> Traversable:
    """Retorna um Traversable em data/<parts>.

    F-0017 / ADR-0021 moveu data/ para o topo do package feat_memory:
    - templates/, skills/  → feat_memory/data/
    - hooks/               → feat_memory.governance/data/

    Esta função roteia automaticamente baseado no primeiro componente.
    """
    if parts and parts[0] == "hooks":
        base = files("feat_memory.governance") / "data"
    else:
        base = files("feat_memory") / "data"
    p = base
    for part in parts:
        p = p / part
    return p


def _copy_resource(src: Traversable, dst: Path) -> None:
    """Copia um arquivo do package data para um path de filesystem."""
    with as_file(src) as src_path:
        shutil.copy2(src_path, dst)


def _substitute_tokens(content: str) -> str:
    """Substitui placeholders de template (`{VERSION}`, `{DEPLOY_DATE}`).

    `{VERSION}` → versão atual do pacote (URLs ancoradas na tag da doutrina).
    `{DEPLOY_DATE}` → instante UTC do deploy em ISO-8601, disponível para
    artefatos gerados que precisem de um timestamp real. Templates sem
    placeholders passam intactos.
    """
    from datetime import datetime, timezone
    from feat_memory import __version__
    content = content.replace("{VERSION}", __version__)
    content = content.replace(
        "{DEPLOY_DATE}", datetime.now(timezone.utc).isoformat()
    )
    return content


def _copy_template(src: Traversable, dst: Path) -> None:
    """Copia um template aplicando `_substitute_tokens`.

    Usado para AGENTS.md/CLAUDE.md.
    """
    dst.write_text(_substitute_tokens(src.read_text(encoding="utf-8")),
                   encoding="utf-8")


def _ensure_frontmatter(existing: str) -> tuple[str, bool]:
    """Prepende um esqueleto de frontmatter se o arquivo não tiver nenhum.

    Em adoção legacy a AGENTS.md já existe — quase sempre uma constituição em
    prosa, sem YAML frontmatter. O deploy só refresca o bloco com sentinelas e
    nunca tocava o topo do arquivo, então a auditoria pós-deploy falhava com
    "campo ausente: schema_version/project/constraints/..." e a conformidade de
    schema ficava 0.00 — exatamente o usuário diligente (que escreveu uma boa
    constituição em prosa) sendo recebido com erros. Aqui fechamos a assimetria
    com greenfield: se não há frontmatter, injetamos o esqueleto mínimo
    (campos mecânicos preenchidos; `project`/`stack`/`constraints` como TODO
    para o mantenedor migrar a prosa). Não é autorar identidade — é dar a mesma
    estrutura que o template greenfield já entrega. Ver ADR-0029.

    A detecção espelha `shared.parsing.parse_frontmatter`: frontmatter é
    reconhecido só quando o arquivo começa exatamente com `---\\n`. Retorna
    (novo_conteúdo, injetou).
    """
    if existing.startswith("---\n"):
        return existing, False
    skeleton_src = _data_path("templates", "AGENTS.frontmatter-skeleton.md")
    if not skeleton_src.is_file():
        # Defensivo: sem o template não injeta, mas não quebra o deploy.
        return existing, False
    skeleton = _substitute_tokens(skeleton_src.read_text(encoding="utf-8"))
    return skeleton.rstrip() + "\n\n" + existing, True


def _replace_sentinel_block(existing: str, payload: str,
                            begin: str = SENTINEL_BEGIN,
                            end: str = SENTINEL_END) -> tuple[str, bool]:
    """Substitui ou insere um bloco delimitado por sentinelas.

    Retorna (novo_conteúdo, mudou). Se o bloco já existir e for idêntico,
    mudou=False. Caso contrário, substitui (ou anexa, se ausente).
    """
    block = f"{begin}\n{payload.rstrip()}\n{end}\n"

    if begin in existing and end in existing:
        # Pega a PRIMEIRA ocorrência da sentinela de abertura e a ÚLTIMA da
        # sentinela de fechamento. Defesa contra menções literais às strings
        # das sentinelas no conteúdo do bloco (raro mas catastrófico).
        before, _, rest = existing.partition(begin)
        _, _, after = rest.rpartition(end)
        if after.startswith("\n"):
            after = after[1:]
        new_content = before + block + after
    else:
        sep = "" if not existing or existing.endswith("\n") else "\n"
        new_content = existing + sep + ("\n" if existing else "") + block

    return new_content, new_content != existing


def _extract_methodology_block(template_text: str) -> str:
    """Extrai o conteúdo entre sentinelas markdown no template AGENTS.md.

    O conteúdo retornado é o que vai entre `<!-- >>> feat-memory >>> -->`
    e `<!-- <<< feat-memory <<< -->` no template (sem as sentinelas em si).
    Usado para refrescar o bloco em arquivos AGENTS.md já existentes sem
    sobrescrever o resto do conteúdo do usuário.
    """
    if MD_SENTINEL_BEGIN not in template_text or MD_SENTINEL_END not in template_text:
        raise ValueError(
            "template AGENTS.md não contém sentinelas markdown feat-memory"
        )
    # Defesa contra menções literais às sentinelas no conteúdo: usa primeira
    # abertura e última fechamento (cf. _replace_sentinel_block).
    _, _, rest = template_text.partition(MD_SENTINEL_BEGIN)
    block, _, _ = rest.rpartition(MD_SENTINEL_END)
    return block.strip()


def deploy_constitution(target: Path, force: bool, merge: bool) -> None:
    """Deploy de AGENTS.md (via bloco com sentinelas) e CLAUDE.md.

    Para AGENTS.md, a única mudança que o deploy faz num arquivo existente
    é substituir o bloco delimitado por sentinelas markdown. O resto do
    conteúdo (frontmatter, seções específicas do projeto autoradas pelo
    mantenedor) nunca é tocado. Em arquivo ausente, copia o template
    completo.

    Para CLAUDE.md (redirect mínimo `@AGENTS.md`), copia se ausente e
    deixa quieto se existe — não há merge nem refresh.
    """
    print("Constituição (AGENTS.md, CLAUDE.md):")

    src = _data_path("templates", "AGENTS.md")
    dst = target / "AGENTS.md"
    if not src.is_file():
        print("  ERRO: template ausente no pacote: AGENTS.md", file=sys.stderr)
        sys.exit(1)

    template_text = _substitute_tokens(src.read_text(encoding="utf-8"))

    if not dst.exists():
        dst.write_text(template_text, encoding="utf-8")
        print("  criado: AGENTS.md")
    elif force:
        dst.write_text(template_text, encoding="utf-8")
        print("  sobrescrito: AGENTS.md (--force)")
    elif not merge:
        print("  pulado: AGENTS.md (já existe; --no-merge)")
    else:
        block_payload = _extract_methodology_block(template_text)
        existing = dst.read_text(encoding="utf-8")
        existing, fm_added = _ensure_frontmatter(existing)
        had_block = MD_SENTINEL_BEGIN in existing and MD_SENTINEL_END in existing
        new_content, changed = _replace_sentinel_block(
            existing, block_payload,
            begin=MD_SENTINEL_BEGIN, end=MD_SENTINEL_END,
        )
        if changed or fm_added:
            dst.write_text(new_content, encoding="utf-8")
            verb = "atualizado" if had_block else "atualizado (bloco anexado)"
            print(f"  {verb}: AGENTS.md (bloco feat-memory)")
            if fm_added:
                print("  injetado: AGENTS.md (esqueleto de frontmatter — "
                      "preencha os campos TODO)")
        else:
            print("  já em dia: AGENTS.md (bloco feat-memory sem mudanças)")

    src = _data_path("templates", "CLAUDE.md")
    dst = target / "CLAUDE.md"
    if not src.is_file():
        print("  ERRO: template ausente no pacote: CLAUDE.md", file=sys.stderr)
        sys.exit(1)

    if not dst.exists():
        _copy_template(src, dst)
        print("  criado: CLAUDE.md")
    elif force:
        _copy_template(src, dst)
        print("  sobrescrito: CLAUDE.md (--force)")
    else:
        print("  pulado: CLAUDE.md (já existe)")


META_HEADER = (
    "# Metadata de instalação do feat-memory.\n"
    "#\n"
    "# Regenerado a cada `feat-memory deploy`. Versionado no Git do consumidor\n"
    "# para que ferramentas externas e a própria CLI (audit, telemetria) saibam\n"
    "# contra qual versão a estrutura foi produzida.\n"
    "#\n"
    "# Schema documentado em ADR-0013. Não edite manualmente — re-rode deploy.\n"
    "\n"
)


def deploy_meta(target: Path) -> None:
    """Grava .feat-memory/.meta.yaml com versão e timestamp.

    Idempotente por construção: cada deploy sobrescreve o arquivo com os
    valores correntes. Schema definido em ADR-0013; `cli_path` removido em
    ADR-0034 (era caminho absoluto, local, da máquina do autor, versionado no
    Git sem nenhum consumidor que o lesse).
    """
    print("Metadata (.feat-memory/.meta.yaml):")

    from datetime import datetime, timezone

    import yaml

    from feat_memory import __version__

    data = {
        "schema_version": 1,
        "version": __version__,
        "deployed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "telemetry_enabled": True,
    }

    feat_memory_dir = target / ".feat-memory"
    feat_memory_dir.mkdir(parents=True, exist_ok=True)
    dst = feat_memory_dir / ".meta.yaml"

    existed = dst.exists()
    body = yaml.safe_dump(data, sort_keys=False, default_flow_style=False)
    dst.write_text(META_HEADER + body, encoding="utf-8")

    verb = "atualizado" if existed else "criado"
    print(f"  {verb}: .feat-memory/.meta.yaml (v{__version__})")


def deploy_changelog(target: Path) -> None:
    """Cria changelog/UNRELEASED.md em .feat-memory/ (pula se existe).

    Substitui o antigo STATE.md: o foco da sessão e o orçamento de retomada
    vivem nas entradas do UNRELEASED (ADR-0043). Conteúdo volátil — nunca
    sobrescreve um existente.
    """
    from feat_memory.memory import changelog
    print("Changelog vivo (.feat-memory/changelog/UNRELEASED.md):")
    up = changelog.unreleased_path(target)
    if up.exists():
        print("  já existe: .feat-memory/changelog/UNRELEASED.md")
    else:
        changelog.ensure_scaffold(target)
        print("  criado: .feat-memory/changelog/UNRELEASED.md")


_IDEAS_MARKER = "<!-- Entradas"


def _ideas_entries(text: str) -> str:
    """Entradas (`## ...`) de um ideas.md/suggestions.md, sem o cabeçalho."""
    i = text.find(_IDEAS_MARKER)
    if i >= 0:
        eol = text.find("\n", i)
        return text[eol + 1:].strip() if eol >= 0 else ""
    m = re.search(r"^## ", text, re.MULTILINE)
    return text[m.start():].strip() if m else ""


def deploy_ideas(target: Path) -> None:
    """Cria/refresca .feat-memory/ideas.md — funil do futuro (ADR-0047).

    O **cabeçalho** (descrição + tabela de triagem) é conteúdo de metodologia e
    é refrescado a cada deploy, como o bloco do AGENTS.md; as **entradas** do
    usuário (`## ...`) são preservadas.
    """
    print("Funil do futuro (.feat-memory/ideas.md):")
    fm_dir = target / ".feat-memory"
    fm_dir.mkdir(parents=True, exist_ok=True)
    dst = fm_dir / "ideas.md"

    header = _substitute_tokens(
        _data_path("templates", "ideas.md").read_text(encoding="utf-8")
    ).rstrip("\n") + "\n"
    entries = _ideas_entries(dst.read_text(encoding="utf-8")) if dst.exists() else ""
    content = header + (f"\n{entries}\n" if entries else "")

    before = dst.read_text(encoding="utf-8") if dst.exists() else None
    if before != content:
        dst.write_text(content, encoding="utf-8")
    if before is None:
        print("  criado: .feat-memory/ideas.md")
    elif before != content:
        print("  header refrescado: .feat-memory/ideas.md (entradas preservadas)")
    else:
        print("  já atualizado: .feat-memory/ideas.md")


def deploy_gitattributes(target: Path) -> None:
    """Deploy do .gitattributes (bloco com sentinelas) + driver de merge."""
    print("Configuração de merge (.gitattributes):")
    src = _data_path("templates", ".gitattributes")
    dst = target / ".gitattributes"

    if not src.is_file():
        return

    payload = src.read_text(encoding="utf-8").strip() + "\n"
    existing = dst.read_text(encoding="utf-8") if dst.exists() else ""
    new_content, changed = _replace_sentinel_block(existing, payload)

    if changed:
        dst.write_text(new_content, encoding="utf-8")
        verb = "atualizado" if existing else "criado"
        print(f"  {verb}: .gitattributes (bloco feat-memory)")
    else:
        print("  já em dia: .gitattributes (bloco feat-memory sem mudanças)")

    if (target / ".git").exists():
        try:
            subprocess.check_call(
                ["git", "config", "merge.ours.driver", "true"],
                cwd=target, stdout=subprocess.DEVNULL,
            )
            print("  configurado: merge.ours.driver")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("  AVISO: não foi possível configurar merge.ours.driver")


def ensure_gitignore(target: Path) -> None:
    """Garante que paths transientes/locais estão no .gitignore.

    `.feat-memory-deploy/` — diretório transiente do deploy legado.
    `.feat-memory/.telemetry.jsonl` — telemetria local opt-out (F-0014,
    ADR-0017): dado pessoal de adoção do dev, não memória do projeto;
    versionar distribuiria padrões de uso individual.
    """
    print("Gitignore (.feat-memory-deploy/, .telemetry.jsonl ignorados):")
    dst = target / ".gitignore"
    payload = ".feat-memory-deploy/\n.feat-memory/.telemetry.jsonl\n"
    existing = dst.read_text(encoding="utf-8") if dst.exists() else ""
    new_content, changed = _replace_sentinel_block(existing, payload)

    if changed:
        dst.write_text(new_content, encoding="utf-8")
        verb = "atualizado" if existing else "criado"
        print(f"  {verb}: .gitignore (bloco feat-memory)")
    else:
        print("  já contém: .gitignore (bloco feat-memory presente)")


def check_v03_layout(target: Path) -> bool:
    """Detecta layout v0.3.x na raiz e aborta com instrução de migração.

    Retorna True se layout legado detectado (não pode continuar).
    Retorna False se layout já é novo ou não há Git.
    """
    if not (target / ".git").exists():
        return False

    legacy_paths = ["manifest", "decisions", "STATE.md"]
    tracked = []
    try:
        for p in legacy_paths:
            result = subprocess.run(
                ["git", "ls-files", "--error-unmatch", p],
                cwd=target, capture_output=True, text=True, check=False,
            )
            if result.returncode == 0:
                tracked.append(p)
    except FileNotFoundError:
        return False

    if not tracked:
        return False

    print()
    print("=" * 60)
    print("ATENÇÃO: layout v0.3.x detectado na raiz do projeto")
    print("=" * 60)
    print()
    print("A partir de v0.4.0, os artefatos de memória ficam em .feat-memory/.")
    print("Os seguintes paths legados foram detectados no Git:")
    for p in tracked:
        print(f"  - {p}/" if p != "STATE.md" else f"  - {p}")
    print()
    print("Execute a migração manual ANTES de prosseguir:")
    print()
    print("  # 1. Crie a nova estrutura")
    print("  mkdir -p .feat-memory/manifest/features")
    print("  mkdir -p .feat-memory/decisions/proposals")
    print()
    print("  # 2. Mova os artefatos (preserva histórico via git mv)")
    if "manifest" in tracked:
        print("  git mv manifest/* .feat-memory/manifest/")
        print("  rmdir manifest")
    if "decisions" in tracked:
        print("  git mv decisions/* .feat-memory/decisions/")
        print("  rmdir decisions")
    if "STATE.md" in tracked:
        print("  git mv STATE.md .feat-memory/STATE.md")
    print()
    print('  # 3. Ajuste .gitattributes (padrões de merge=ours)')
    print('  # As linhas de STATE.md, manifest/INDEX.md, decisions/INDEX.md')
    print('  # devem incluir o prefixo .feat-memory/')
    print()
    print('  git commit -m "chore: migrate to feat-memory v0.4 layout"')
    print()
    print("=" * 60)
    return True


def migrate_legacy_layout(target: Path) -> bool:
    """Migra o layout legado `.agent-memory/` → `.feat-memory/` (rename do projeto).

    Caminho de upgrade para consumidores que adotaram a metodologia quando ela se
    chamava `agent-memory` (ADR-0036). Idempotente: no-op se já está no layout novo.
    Não-destrutivo: se `.agent-memory/` E `.feat-memory/` coexistem, não sobrescreve
    — deixa o legado para revisão manual e avisa. Retorna True se migrou.

    O `deploy` que chama isto em seguida reinstala o pre-commit hook (passa a chamar
    `feat-memory`) e refresca o bloco em AGENTS.md, completando a transição.
    """
    legacy = target / ".agent-memory"
    current = target / ".feat-memory"

    # Diretório transiente legado do deploy antigo: descartável sempre.
    legacy_deploy = target / ".agent-memory-deploy"
    if legacy_deploy.exists():
        shutil.rmtree(legacy_deploy, ignore_errors=True)

    if not legacy.is_dir():
        return False

    if current.exists():
        print("AVISO: existem .agent-memory/ E .feat-memory/ — não vou "
              "sobrescrever.")
        print("  Reconcilie manualmente e remova .agent-memory/.")
        return False

    try:
        legacy.rename(current)
    except OSError as e:
        print(f"AVISO: não foi possível migrar .agent-memory/ → .feat-memory/: {e}",
              file=sys.stderr)
        print("  Renomeie o diretório manualmente e rode `feat-memory deploy` de novo.",
              file=sys.stderr)
        return False

    print("Migração de layout: .agent-memory/ → .feat-memory/ (rename para feat-memory)")
    print("  O pre-commit hook será reinstalado para chamar `feat-memory`.")
    print("  Se houver um pacote pipx antigo, remova: pipx uninstall agent-memory")
    return True


def deploy_agents(target: Path) -> None:
    """Deploy do(s) subagent(s) do Claude Code em .claude/agents/.

    Cada arquivo é um wrapper fino que pré-carrega a skill homônima (fonte
    única da lógica) via o campo `skills:` do frontmatter, dando ao agente um
    contexto isolado. Sempre sobrescreve — conteúdo de metodologia, como as
    skills. No-op silencioso se o pacote não traz a pasta agents/.
    """
    agents_src = _data_path("agents")
    if not agents_src.is_dir():
        return

    print("Subagents (Claude Code):")
    agents_dst = target / ".claude" / "agents"
    agents_dst.mkdir(parents=True, exist_ok=True)

    for agent_path in sorted(agents_src.iterdir(), key=lambda e: e.name):
        if not (agent_path.is_file() and agent_path.name.endswith(".md")):
            continue
        dst_file = agents_dst / agent_path.name
        existed = dst_file.exists()
        _copy_resource(agent_path, dst_file)
        verb = "atualizado" if existed else "deployado"
        print(f"  {verb}: {agent_path.name}")

    print("  → se .claude/ está no seu .gitignore, rastreie os subagents "
          "(ex.: troque `.claude/` por `.claude/*` + `!.claude/agents/`)")


def deploy_skills(target: Path, force: bool) -> None:
    """Deploy de skills (sempre sobrescreve; conteúdo de metodologia)."""
    print("Skills:")
    skills_dst = target / "skills"
    skills_dst.mkdir(parents=True, exist_ok=True)

    skills_src = _data_path("skills")
    if not skills_src.is_dir():
        print("  AVISO: pasta skills/ ausente no pacote")
        return

    for skill_path in sorted(skills_src.iterdir(), key=lambda e: e.name):
        if not skill_path.is_dir():
            continue
        skill_name = skill_path.name
        src_file = skill_path / "SKILL.md"
        dst_dir = skills_dst / skill_name
        dst_file = dst_dir / "SKILL.md"

        if not src_file.is_file():
            print(f"  pulado: {skill_name} (sem SKILL.md no source)")
            continue

        dst_dir.mkdir(parents=True, exist_ok=True)
        existed = dst_file.exists()
        _copy_resource(src_file, dst_file)
        verb = "atualizada" if existed else "deployada"
        print(f"  {verb}: {skill_name}")


def create_directories(target: Path) -> None:
    """Cria estrutura de pastas .feat-memory/manifest/, decisions/, changelog/."""
    print("Estrutura de pastas:")
    base = target / ".feat-memory"
    for rel in ("manifest/features", "decisions/proposals", "changelog"):
        full = base / rel
        if full.exists():
            print(f"  já existe: .feat-memory/{rel}/")
        else:
            full.mkdir(parents=True, exist_ok=True)
            (full / ".gitkeep").touch()
            print(f"  criado: .feat-memory/{rel}/")


def install_git_hooks(target: Path) -> None:
    """Instala git hooks no target."""
    print("Git hooks:")
    install_hooks.install(target)


def run_audit(target: Path) -> None:
    """Roda primeira auditoria via subprocess (cwd=target)."""
    print("Auditoria inicial:")
    try:
        result = subprocess.run(
            ["feat-memory", "audit"],
            cwd=target, capture_output=True, text=True, check=False,
        )
        for line in result.stdout.splitlines():
            print(f"  {line}")
        if result.returncode != 0:
            print(f"  AVISO: auditoria retornou {result.returncode}")
    except FileNotFoundError:
        print("  AVISO: 'feat-memory' não encontrado no PATH; "
              "pulando auditoria inicial")


def print_next_steps(target: Path) -> None:
    """Imprime próximos passos para o usuário."""
    print("Próximos passos:")
    print(f"  1. Preencha/aprove o frontmatter de {target / 'AGENTS.md'} "
          "(project, stack, constraints) — a skill memory-deploy propõe a partir "
          "do código e você aprova; `feat-memory schema` mostra a forma dos campos")
    print(f"  2. Registre o trabalho em voo em "
          f"{target / '.feat-memory' / 'changelog' / 'UNRELEASED.md'}")
    print("  3. (Opcional) Adicione seções específicas do projeto à AGENTS.md "
          "fora do bloco feat-memory")
    print("  4. Crie sua primeira feature em .feat-memory/manifest/features/ "
          "(`feat-memory schema` lista os campos)")
    print('  5. Faça commit: git add + git commit -m "adopt feat-memory"')


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "deploy",
        help="Instala templates, skills e hooks da metodologia num projeto",
    )
    p.add_argument("target", type=str, nargs="?", default=".",
                   help="caminho para a raiz do projeto consumidor "
                        "(default: diretório atual)")
    p.add_argument("--force", action="store_true",
                   help="sobrescreve TUDO sem merge")
    p.add_argument("--no-merge", action="store_true",
                   help="pula arquivos existentes em vez de mesclar")
    p.add_argument("--no-hooks", action="store_true",
                   help="pula instalação de git hooks")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    target = Path(args.target).resolve()
    if not target.exists():
        print(f"ERRO: target não existe: {target}", file=sys.stderr)
        return 1
    if not target.is_dir():
        print(f"ERRO: target não é um diretório: {target}", file=sys.stderr)
        return 1

    print("=" * 38)
    print("Deploy da metodologia de memória")
    print("=" * 38)

    from feat_memory import __version__
    print(f"Versão: {__version__}")
    print(f"Target: {target}")
    print()

    if check_v03_layout(target):
        return 1

    if migrate_legacy_layout(target):
        print()

    deploy_dir = target / ".feat-memory-deploy"
    # Remove o diretório transiente legado (de versões anteriores que tinham
    # merge queue para AGENTS.md). v0.4+ resolve a constituição direto via
    # bloco com sentinelas, sem handoff intermediário.
    if deploy_dir.exists():
        shutil.rmtree(deploy_dir, ignore_errors=True)

    deploy_constitution(target, args.force, not args.no_merge)
    print()

    deploy_meta(target)
    print()

    deploy_changelog(target)
    print()

    deploy_ideas(target)
    print()

    deploy_gitattributes(target)
    print()

    ensure_gitignore(target)
    print()

    deploy_skills(target, args.force)
    print()

    deploy_agents(target)
    print()

    create_directories(target)
    print()

    if not args.no_hooks:
        install_git_hooks(target)
    else:
        print("Git hooks: pulado (--no-hooks)")
    print()

    run_audit(target)
    print()

    print("=" * 38)
    print("Deploy concluído.")
    print("=" * 38)
    print()

    print_next_steps(target)

    return 0
