"""deploy.py — Deploy idempotente da metodologia em um projeto.

Subcomando da CLI: `agent-memory deploy <target>`. Copia templates,
instala hooks e configura .gitignore/.gitattributes no target.

Comportamento por arquivo:
    AGENTS.md            → bloco com sentinelas markdown, refrescado a cada
                            deploy; conteúdo do usuário fora do bloco nunca
                            é tocado
    CLAUDE.md            → copia se ausente; deixa quieto se existe
    .agent-memory/STATE.md → pula se existe (conteúdo é volátil)
    skills/              → sempre atualizadas (conteúdo de metodologia)
    .gitattributes       → bloco com sentinelas, refrescado a cada deploy
    .gitignore           → bloco com sentinelas garantindo .agent-memory-deploy/
    pastas               → cria se não existem
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from importlib.resources import as_file, files
from importlib.resources.abc import Traversable
from pathlib import Path

from agent_memory.governance import install_hooks


SENTINEL_BEGIN = "# >>> agent-memory >>>"
SENTINEL_END = "# <<< agent-memory <<<"

# Sentinelas markdown (HTML comments) para o bloco da metodologia em AGENTS.md.
# Diferentes das sentinelas shell-style usadas em .gitignore/.gitattributes
# porque `#` em markdown é heading, não comentário.
MD_SENTINEL_BEGIN = "<!-- >>> agent-memory >>> -->"
MD_SENTINEL_END = "<!-- <<< agent-memory <<< -->"


def _data_path(*parts: str) -> Traversable:
    """Retorna um Traversable em data/<parts>.

    F-0017 / ADR-0021 moveu data/ para o topo do package agent_memory:
    - templates/, skills/  → agent_memory/data/
    - hooks/               → agent_memory.governance/data/

    Esta função roteia automaticamente baseado no primeiro componente.
    """
    if parts and parts[0] == "hooks":
        base = files("agent_memory.governance") / "data"
    else:
        base = files("agent_memory") / "data"
    p = base
    for part in parts:
        p = p / part
    return p


def _copy_resource(src: Traversable, dst: Path) -> None:
    """Copia um arquivo do package data para um path de filesystem."""
    with as_file(src) as src_path:
        shutil.copy2(src_path, dst)


def _copy_template(src: Traversable, dst: Path) -> None:
    """Copia um template fazendo substituições (`{VERSION}` → versão atual).

    Usado para AGENTS.md/CLAUDE.md/STATE.md, onde o frontmatter referencia
    a doutrina por URL ancorada na tag da versão. Templates sem
    placeholders passam intactos.
    """
    from agent_memory import __version__
    content = src.read_text(encoding="utf-8")
    content = content.replace("{VERSION}", __version__)
    dst.write_text(content, encoding="utf-8")


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

    O conteúdo retornado é o que vai entre `<!-- >>> agent-memory >>> -->`
    e `<!-- <<< agent-memory <<< -->` no template (sem as sentinelas em si).
    Usado para refrescar o bloco em arquivos AGENTS.md já existentes sem
    sobrescrever o resto do conteúdo do usuário.
    """
    if MD_SENTINEL_BEGIN not in template_text or MD_SENTINEL_END not in template_text:
        raise ValueError(
            "template AGENTS.md não contém sentinelas markdown agent-memory"
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

    from agent_memory import __version__
    template_text = src.read_text(encoding="utf-8").replace(
        "{VERSION}", __version__
    )

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
        had_block = MD_SENTINEL_BEGIN in existing and MD_SENTINEL_END in existing
        new_content, changed = _replace_sentinel_block(
            existing, block_payload,
            begin=MD_SENTINEL_BEGIN, end=MD_SENTINEL_END,
        )
        if changed:
            dst.write_text(new_content, encoding="utf-8")
            verb = "atualizado" if had_block else "atualizado (bloco anexado)"
            print(f"  {verb}: AGENTS.md (bloco agent-memory)")
        else:
            print("  já contém: AGENTS.md (bloco agent-memory atualizado)")

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
    "# Metadata de instalação do agent-memory.\n"
    "#\n"
    "# Regenerado a cada `agent-memory deploy`. Versionado no Git do consumidor\n"
    "# para que ferramentas externas e a própria CLI (audit, telemetria) saibam\n"
    "# contra qual versão a estrutura foi produzida.\n"
    "#\n"
    "# Schema documentado em ADR-0013. Não edite manualmente — re-rode deploy.\n"
    "\n"
)


def deploy_meta(target: Path) -> None:
    """Grava .agent-memory/.meta.yaml com versão, timestamp e cli_path.

    Idempotente por construção: cada deploy sobrescreve o arquivo com os
    valores correntes. Schema definido em ADR-0013.
    """
    print("Metadata (.agent-memory/.meta.yaml):")

    import shutil as _shutil
    from datetime import datetime, timezone

    import yaml

    from agent_memory import __version__

    cli_path = _shutil.which("agent-memory") or sys.executable

    data = {
        "schema_version": 1,
        "version": __version__,
        "deployed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "cli_path": str(Path(cli_path).resolve()),
        "telemetry_enabled": True,
    }

    agent_memory_dir = target / ".agent-memory"
    agent_memory_dir.mkdir(parents=True, exist_ok=True)
    dst = agent_memory_dir / ".meta.yaml"

    existed = dst.exists()
    body = yaml.safe_dump(data, sort_keys=False, default_flow_style=False)
    dst.write_text(META_HEADER + body, encoding="utf-8")

    verb = "atualizado" if existed else "criado"
    print(f"  {verb}: .agent-memory/.meta.yaml (v{__version__})")


def deploy_state(target: Path, force: bool) -> None:
    """Deploy de STATE.md em .agent-memory/ (sempre pula se existe; conteúdo é volátil)."""
    print("Estado (.agent-memory/STATE.md):")
    src = _data_path("templates", "STATE.md")
    agent_memory_dir = target / ".agent-memory"
    agent_memory_dir.mkdir(parents=True, exist_ok=True)
    dst = agent_memory_dir / "STATE.md"

    if not dst.exists():
        _copy_template(src, dst)
        print("  criado: .agent-memory/STATE.md")
    elif force:
        _copy_template(src, dst)
        print("  sobrescrito: .agent-memory/STATE.md (--force)")
    else:
        print("  pulado: .agent-memory/STATE.md (já existe; foco da sessão é volátil)")


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
        print(f"  {verb}: .gitattributes (bloco agent-memory)")
    else:
        print("  já contém: .gitattributes (bloco agent-memory atualizado)")

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

    `.agent-memory-deploy/` — diretório transiente do deploy legado.
    `.agent-memory/.telemetry.jsonl` — telemetria local opt-out (F-0014,
    ADR-0017): dado pessoal de adoção do dev, não memória do projeto;
    versionar distribuiria padrões de uso individual.
    """
    print("Gitignore (.agent-memory-deploy/, .telemetry.jsonl ignorados):")
    dst = target / ".gitignore"
    payload = ".agent-memory-deploy/\n.agent-memory/.telemetry.jsonl\n"
    existing = dst.read_text(encoding="utf-8") if dst.exists() else ""
    new_content, changed = _replace_sentinel_block(existing, payload)

    if changed:
        dst.write_text(new_content, encoding="utf-8")
        verb = "atualizado" if existing else "criado"
        print(f"  {verb}: .gitignore (bloco agent-memory)")
    else:
        print("  já contém: .gitignore (bloco agent-memory presente)")


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
    print("A partir de v0.4.0, os artefatos de memória ficam em .agent-memory/.")
    print("Os seguintes paths legados foram detectados no Git:")
    for p in tracked:
        print(f"  - {p}/" if p != "STATE.md" else f"  - {p}")
    print()
    print("Execute a migração manual ANTES de prosseguir:")
    print()
    print("  # 1. Crie a nova estrutura")
    print("  mkdir -p .agent-memory/manifest/features")
    print("  mkdir -p .agent-memory/decisions/proposals")
    print()
    print("  # 2. Mova os artefatos (preserva histórico via git mv)")
    if "manifest" in tracked:
        print("  git mv manifest/* .agent-memory/manifest/")
        print("  rmdir manifest")
    if "decisions" in tracked:
        print("  git mv decisions/* .agent-memory/decisions/")
        print("  rmdir decisions")
    if "STATE.md" in tracked:
        print("  git mv STATE.md .agent-memory/STATE.md")
    print()
    print('  # 3. Ajuste .gitattributes (padrões de merge=ours)')
    print('  # As linhas de STATE.md, manifest/INDEX.md, decisions/INDEX.md')
    print('  # devem incluir o prefixo .agent-memory/')
    print()
    print('  git commit -m "chore: migrate to agent-memory v0.4 layout"')
    print()
    print("=" * 60)
    return True


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
    """Cria estrutura de pastas .agent-memory/manifest/, decisions/, checkpoints/."""
    print("Estrutura de pastas:")
    base = target / ".agent-memory"
    for rel in ("manifest/features", "decisions/proposals", "checkpoints"):
        full = base / rel
        if full.exists():
            print(f"  já existe: .agent-memory/{rel}/")
        else:
            full.mkdir(parents=True, exist_ok=True)
            (full / ".gitkeep").touch()
            print(f"  criado: .agent-memory/{rel}/")


def install_git_hooks(target: Path) -> None:
    """Instala git hooks no target."""
    print("Git hooks:")
    install_hooks.install(target)


def run_audit(target: Path) -> None:
    """Roda primeira auditoria via subprocess (cwd=target)."""
    print("Auditoria inicial:")
    try:
        result = subprocess.run(
            ["agent-memory", "audit"],
            cwd=target, capture_output=True, text=True, check=False,
        )
        for line in result.stdout.splitlines():
            print(f"  {line}")
        if result.returncode != 0:
            print(f"  AVISO: auditoria retornou {result.returncode}")
    except FileNotFoundError:
        print("  AVISO: 'agent-memory' não encontrado no PATH; "
              "pulando auditoria inicial")


def print_next_steps(target: Path) -> None:
    """Imprime próximos passos para o usuário."""
    print("Próximos passos:")
    print(f"  1. Edite o frontmatter de {target}/AGENTS.md "
          "(project, stack, constraints)")
    print(f"  2. Edite {target}/.agent-memory/STATE.md (Current, Next)")
    print("  3. (Opcional) Adicione seções específicas do projeto à AGENTS.md "
          "fora do bloco agent-memory")
    print("  4. Crie sua primeira feature em .agent-memory/manifest/features/")
    print("  5. Faça commit: git add . && git commit -m 'adopt agent memory'")


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "deploy",
        help="Instala templates, skills e hooks da metodologia num projeto",
    )
    p.add_argument("target", type=str,
                   help="caminho para a raiz do projeto consumidor")
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

    from agent_memory import __version__
    print(f"Versão: {__version__}")
    print(f"Target: {target}")
    print()

    if check_v03_layout(target):
        return 1

    deploy_dir = target / ".agent-memory-deploy"
    # Remove o diretório transiente legado (de versões anteriores que tinham
    # merge queue para AGENTS.md). v0.4+ resolve a constituição direto via
    # bloco com sentinelas, sem handoff intermediário.
    if deploy_dir.exists():
        shutil.rmtree(deploy_dir, ignore_errors=True)

    deploy_constitution(target, args.force, not args.no_merge)
    print()

    deploy_meta(target)
    print()

    deploy_state(target, args.force)
    print()

    deploy_gitattributes(target)
    print()

    ensure_gitignore(target)
    print()

    deploy_skills(target, args.force)
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
