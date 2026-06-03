# Changelog

Todas as mudanças notáveis a esta metodologia são registradas neste arquivo.

O formato segue [Keep a Changelog](https://keepachangelog.com/) e o projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Unreleased]

## [0.12.0] - 2026-06-03

Primeiro passo do posicionamento estratégico do projeto como **a melhor camada de "constitution"** do spec-driven development (SDD): tornar as restrições da constituição *enforced* em vez de só declarativas. Uma constituição verificada a cada commit supera uma que é apenas lida.

### Adicionado

**F-0024 (constraint-enforcement) + ADR-0028.** Cada constraint em `AGENTS.md` pode declarar um bloco `check` opcional que o `agent-memory audit` **executa** contra o repositório. Novo módulo `governance/constraints.py` com um **conjunto fechado** de cinco checkers genéricos — `forbid_paths`, `require_paths`, `forbid_pattern`, `require_pattern`, `dependencies` — compostos via YAML sem escrever Python (o antídoto à razão que adiava o item: "cada regra exige um validador"). A violação herda a severity da constraint (hard→error/bloqueia o build, soft→warning); `check` malformado (type desconhecido, param faltando, regex inválido, dependencies sem allow/forbid) é error de schema. Vive em `governance/` e não em `memory/schemas.py` porque executar checker varre a árvore — governança, não schema (ADR-0021). Tudo stdlib + pyyaml (C2 preservada), agnóstico de linguagem: `dependencies` cobre `pyproject.toml`/`requirements.txt`/`package.json`. Novo indicador "Conformidade de constraints" no relatório e no JSON do audit. **Dogfood (C3/ADR-0009):** C1 (`forbid_paths` sobre `*.sh`/`*.bash`) e C2 (`dependencies` sobre `pyproject.toml`, allow `pyyaml`) deste repo passam a ser checadas a cada audit. C3 ("segue a metodologia") e C4 ("docs em pt-br") ficam declarativas — sem checker barato e confiável, limitação honesta.

## [0.11.0] - 2026-06-03

Implementa os itens do roadmap (FUTURE_IMPROVEMENTS) com valor real e aderência à identidade do projeto, descartando explicitamente o que acopla linguagem/domínio ou é especulativo na escala atual.

### Adicionado

**F-0021 (pypi-distribution) + ADR-0025.** Distribuição via PyPI: `.github/workflows/release.yml` builda sdist+wheel e publica a cada tag `vX.Y.Z` via trusted publishing (OIDC, sem token persistente). Corrigido bug latente de `package-data` — o pre-commit hook, movido para `governance/data/hooks/` no split F-0017, era omitido do wheel (editable install mascarava). `tests/test_packaging.py` valida que todo arquivo de runtime está coberto por algum glob, sem precisar buildar. Metadados ajustados a PEP 639 (license SPDX, sem classifier de licença); `keywords`/`classifiers` adicionados.

**F-0022 (ci-pipeline) + ADR-0026.** `.github/workflows/ci.yml` roda `pytest` + `agent-memory audit --strict` em push/PR, na matriz {ubuntu, macos, windows} × {3.11, 3.12}. A matriz cross-OS torna a constraint C1 verificável por execução (antes só declarada); o `audit --strict` no CI é a segunda linha de defesa para commits que pularam o pre-commit via `--no-verify`.

**F-0023 (adr-version-field) + ADR-0027.** O campo `version` em ADRs vira opcional formalizado: `validate_decision` valida o formato `X.Y.Z` quando presente mas nunca exige; `propose-adr` pré-preenche o campo em novos drafts (`SEMVER_RE` é a fonte única de formato); METHODOLOGY documenta a semântica (release de aceite). Sem backfill — ADRs antigos sem o campo seguem válidos. Fecha um drift conhecido.

### Notas

FUTURE_IMPROVEMENTS marca explicitamente os itens **adiados** (query, linting de constraints, multi-agente, snapshot de State, federação, migrations de schema, drift dashboard) e **rejeitados** (coverage via pytest-cov, OpenAPI, busca semântica, feature flags) com a razão de cada um.

## [0.10.0] - 2026-06-03

Sessão de saneamento: a auditoria do próprio repo revelou drift acumulado (11 features `in_progress` já released, STATE 23 dias velho, `CLAUDE.md` com import quebrado para `AGENT.md` após o rename para `AGENTS.md`). Corrigido o estado **e** adicionado enforcement para que esse tipo de drift não passe mais clean.

### Adicionado

**F-0020 (audit-release-status) + ADR-0024.** `agent-memory audit` passa a confrontar status de feature contra releases reais. Novo `validate_release_status`: feature com `status: in_progress` cujo `version` consta como released (seção `## [X.Y.Z]` do CHANGELOG **ou** tag `vX.Y.Z`, derivadas por `released_versions`, fail-soft) gera warning — promovido a error sob `audit --strict`, bloqueando commit de feature que mente sobre o próprio status. Em `print_report`, o frescor do STATE acima de `STALENESS_WARN_HOURS` (14 dias) ganha aviso visual; deliberadamente **não** vira Issue (staleness no commit é F-0013, soft/fail-open — ADR-0024 explica a assimetria).

### Corrigido

- `CLAUDE.md` importava `@AGENT.md` (inexistente após o rename `AGENT.md → AGENTS.md`) — a constituição não carregava no Claude Code. Agora `@AGENTS.md`.
- Constituição (`AGENTS.md`), `README.md`, `FUTURE_IMPROVEMENTS.md` e `METHODOLOGY.md` referenciavam caminhos pré-split F-0017 (`src/agent_memory/audit.py`, `propose_adr.py`, `data/hooks/`) e o layout flat antigo do pacote — atualizados para `governance/`, `memory/` e `governance/data/hooks/`.
- CHANGELOG da v0.7.0 afirmava que templates/skills migraram para `memory/data/`; na verdade permaneceram em `agent_memory/data/` (só hooks foram para `governance/data/`) — corrigido.
- Adicionadas as seções faltantes `[0.8.1]` e `[0.9.0]` (releases sem entrada no changelog).
- Features F-0009..F-0019 marcadas `shipped` com `version` = release de entrega (F-0018→0.8.0, F-0019→0.9.0) e arquivadas para `manifest/archive/`.

## [0.9.0] - 2026-05-11

ADRs `superseded` ganham casa própria, espelhando o que F-0012 fez para features arquivadas. Desonera o INDEX principal de decisões carregado por `memory-bootstrap`.

### Adicionado

**F-0019 (superseded-decisions-folder) + ADR-0023.** ADRs com `status: superseded` passam a viver em `.agent-memory/decisions/superseded/` com INDEX próprio (mesmas colunas do INDEX principal). `agent-memory audit` varre `decisions/` e `decisions/superseded/` para validação de schema e crosscheck de `active_decisions`; regenera ambos os INDEXes. `propose_adr.next_adr_number` agrega IDs de `decisions/` + `superseded/` + `proposals/` — colisão de número impossível. Movimentação para superseded é manual via `git mv` (sem subcomando dedicado). Novo helper `paths.SUPERSEDED_DIR`, `indexing.gen_superseded_decisions_index`.

## [0.8.1] - 2026-05-10

### Adicionado

**F-0019 (parcial).** `agent-memory audit` passa a emitir warning quando o tamanho dos artefatos de retomada (resumption budget) excede o orçamento declarado em `AGENTS.md::budgets`, antes que o estouro degrade silenciosamente o briefing de `memory-bootstrap`.

## [0.8.0] - 2026-05-05

Notificação ao consumidor quando o CLI está em versão diferente da que produziu sua estrutura. Fecha o loop de feedback que F-0010 (`.meta.yaml::version`) e F-0016 (VERSION-bump-on-code) abriram.

### Adicionado

**F-0018 (consumer-version-notice) + ADR-0022.** Novo módulo `governance/version_check.py` com `consumer_version_notice(root)` que compara `.agent-memory/.meta.yaml::version` a `agent_memory.__version__`. Se diferentes, retorna texto sugerindo `agent-memory deploy .`.

Integração em `agent-memory audit`: após o relatório, imprime o notice na stderr (amarelo com `isatty`, plain em CI). **Não muda o exit code** — soft sempre, ADR-0008 fail-open preservado para o sinal de notificação.

Subcomando standalone `agent-memory version-check`: invoca a função direto, útil para CI/scripts. Imprime o notice ou `✓ agent-memory atualizado (vX.Y.Z)`. Sai com 0 sempre.

Disable via `.agent-memory/.meta.yaml::version_check_enabled: false` (default `true`). Coerente com `telemetry_enabled` de F-0014.

## [0.7.0] - 2026-05-05

Refactor arquitetural: separação completa entre **memória de agente** e **governança** em três subpacotes hierarquicamente desacoplados (`shared`, `memory`, `governance`). Sem mudança de comportamento observável — mesmo CLI, mesmos subcomandos, mesmo hook. A separação vive na estrutura de código e no `--help` agrupado por categoria.

### Mudado

**BREAKING** (interno, para consumidores que importavam módulos diretamente). O pacote `agent_memory` agora expõe três subpacotes públicos:

- `agent_memory.shared.{paths, parsing}` — utilitários sem dependências do projeto (lazy-init de paths, parse_frontmatter, read_meta).
- `agent_memory.memory.{schemas, indexing, archive, checkpoints, propose_adr, migrate}` — artefatos canônicos da metodologia, validação de schema, geração de INDEX, ciclo de vida.
- `agent_memory.governance.{audit, telemetry, check_staleness, check_version_bump, install_hooks}` — enforcement, métricas, telemetria, hooks.

Regra de dependência hierárquica: `shared ⇐ memory ⇐ governance`. **Memória nunca importa governança** — é o invariante que torna `deploy --no-hooks` uma operação puramente memória. Verificável mecanicamente.

Templates e skills permanecem em `src/agent_memory/data/` (data compartilhado no topo do pacote); hooks migraram para `src/agent_memory/governance/data/`. `deploy.py` resolve automaticamente via `_data_path` baseado no primeiro componente do path solicitado (`hooks` → governance, resto → topo).

CLI mesmo binário (`agent-memory`), mesmos subcomandos. O `--help` agora descreve subcomandos agrupados por categoria (Memória / Governança) na descrição do parser raiz.

ADR-0021 documenta a política. F-0017 declara o invariante e os critérios de aceitação.

### Adicionado

**F-0017 (memory-governance-split) + ADR-0021.** Separação arquitetural acima.

## [0.6.0] - 2026-05-04

Sete features novas (F-0010..F-0016) cobrindo lacunas onde o ritual da metodologia ainda dependia de boa vontade do agente. Sete ADRs novos (ADR-0013..ADR-0020) registram as decisões. Conjunto entregue em uma sessão intensiva, dogfooded na própria estrutura deste repo (7 features iniciais arquivadas para `manifest/archive/`, STATE.md migrado para o modelo de checkpoints append-only).

### Adicionado

**F-0010 (version-meta) + ADR-0013.** Flag `--version` no parser raiz (`agent-memory --version`) e gravação de `.agent-memory/.meta.yaml` no consumidor a cada deploy, registrando `version`, `deployed_at`, `cli_path` e `telemetry_enabled`. Habilita audit reportar contra versão e telemetria anotar eventos com a versão real. `audit.read_meta(root)` é o helper compartilhado, tolerante a ausência (consumidores pré-v0.6).

**F-0011 (audit-state-crosscheck) + ADR-0014.** Cross-check (hard, default-on) que verifica se cada `F-NNNN` em `STATE.md::active_features` tem arquivo correspondente em `manifest/features/` ou `manifest/archive/`, e cada `ADR-NNNN` em `active_decisions` tem arquivo em `decisions/`. Falhas viram errors que bloqueiam o pre-commit hook — captura "memória mentirosa" antes que o agente confie em IDs órfãos. Plus: `agent-memory audit --check-staleness[=N]` (soft, opt-in) emite warning se commits dos últimos N dias tocaram código sem atualizar STATE.md.

**F-0012 (archive-shipped) + ADR-0015.** Novo subcomando `agent-memory archive [--apply]` move features `shipped` (e fora de `STATE.md::active_features`) para `.agent-memory/manifest/archive/` via `git mv` (fallback `shutil.move`). Reduz o orçamento de retomada que `memory-bootstrap` carrega. Default dry-run para evitar movimentação acidental. ADRs nunca são arquivados (registro histórico imutável). Audit valida e gera INDEX separado para o archive.

**F-0013 (hook-staleness-staged) + ADR-0016.** Novo subcomando `agent-memory check-staleness-staged` invocado pelo pre-commit hook após o audit. Inspeciona `git diff --cached --name-only` e emite warning amarelo na stderr (sempre exit 0, soft) quando o commit toca código sem incluir `.agent-memory/STATE.md`. Captura debrief esquecido no momento de máxima alavancagem.

**F-0014 (local-telemetry) + ADR-0017.** `agent-memory record EVENT [k=v ...]` anexa eventos JSONL em `.agent-memory/.telemetry.jsonl` (gitignored). `agent-memory log [--since 7d] [--summary]` lê e agrega; `--summary` deriva taxa de adesão (`session_start` com `state_read=true` / total). Default ligado, kill switch via `.meta.yaml::telemetry_enabled=false`. Skills `memory-bootstrap` e `memory-debrief` atualizadas para invocar `agent-memory record` ao final dos rituais. 100% local, nunca enviado pela rede.

**F-0015 (state-from-checkpoints) + ADR-0018 + ADR-0019.** Inverte o modelo de `STATE.md`: deixa de ser autorado em-place, vira view derivada de checkpoints append-only em `.agent-memory/checkpoints/YYYY-MM-DD-HHMMSS.md`. Cada sessão grava um arquivo imutável; `STATE.md` é regerado pelos N últimos (window configurável via `.meta.yaml::state_view_window`, default 1). `memory-bootstrap` continua lendo o mesmo arquivo, mesmo schema (Liskov-safe). Reescrita destrutiva fica impossível por construção. Comandos novos: `agent-memory checkpoint --summary "..."`, `agent-memory state-rebuild` (recovery), `agent-memory migrate --to=checkpoints` (migração não-destrutiva e idempotente do STATE.md legado). Skill `memory-debrief` reescrita para invocar `checkpoint`.

**F-0016 (check-version-bump) + ADR-0020.** Novo subcomando `agent-memory check-version-bump-staged` invocado pelo pre-commit hook após `check-staleness-staged`. Bloqueia (hard, exit 1) commits que tocam código sem incluir `VERSION` no staging. Auto opt-in: no-op em projetos sem arquivo `VERSION` na raiz. Bypass deliberado via `git commit --no-verify`. Exceção justificada à fail-open de ADR-0008 — soft tornaria a versão mentirosa silenciosa, quebrando F-0010, F-0014 e F-0018 (em planejamento).

### Mudado

`audit` ganha cross-check de IDs ativos (default-on, hard) e flag `--check-staleness[=N]` (opt-in, soft). Templates `.gitattributes` ganham regras `merge=ours` para `.agent-memory/.meta.yaml` e geração separada de `.agent-memory/manifest/archive/INDEX.md`. Pre-commit hook agora invoca três checks em sequência (`audit`, `check-staleness-staged`, `check-version-bump-staged`).

Skill `memory-debrief` passa a invocar `agent-memory checkpoint` em vez de reescrever `STATE.md` diretamente. Skill `memory-bootstrap` e `memory-debrief` invocam `agent-memory record` ao final para alimentar telemetria de adesão. Templates `.gitignore` ganham `.agent-memory/.telemetry.jsonl` (telemetria é local, nunca versionada). Deploy cria `.agent-memory/checkpoints/.gitkeep` na inicialização.

`compute_metrics` em audit conta features ativas e arquivadas no denominador de cobertura, refletindo a separação introduzida por F-0012. INDEX principal lista só ativas (menor, mais rápido para `memory-bootstrap`); archive INDEX lista as arquivadas (discoverability preservada).

## [0.5.0] - 2026-04-30

### Adicionado

Quarta skill `memory-pull-brief` (F-0009) cobre o gap cognitivo pós-pull em projetos cliente. Quando o desenvolvedor faz `git pull` e recebe commits de colegas, a skill examina o diff trazido, identifica mudanças semânticas em `manifest/features/`, `decisions/` e no bloco metodológico de `AGENTS.md`, e propõe ajustes em `STATE.md` (remoção de IDs em `active_*` cuja semântica upstream invalida o foco local, entrada nova no buffer `Recent`). É read-only sobre `manifest/` e `decisions/` por design — esses já vieram corretos do pull, escrever neles seria reverter trabalho de colegas. Trigger duplo: manual (frases como "o que veio do pull", "brifa as mudanças do main") e por delegação a partir de `memory-bootstrap` quando o último commit é merge que tocou artefatos.

Decisão formalizada em [ADR-0012](.agent-memory/decisions/0012-skill-memory-pull-brief.md).

### Mudado

Skill `memory-bootstrap` (F-0007) ganha passo de detecção de merge tocando artefatos: após o `agent-memory audit` regenerar índices, se o merge moveu `manifest/features/`, `decisions/` ou o bloco sentinela de `AGENTS.md`, a bootstrap delega para `memory-pull-brief` antes do briefing tático. Sem esse trigger, comportamento prévio é preservado.

Bloco "Skills disponíveis" do template `AGENTS.md` atualizado de "três skills" para "quatro skills" e ganha parágrafo sobre `memory-pull-brief`. Refresh automático no próximo `agent-memory deploy` em projetos consumidores.

## [0.4.0] - 2026-04-30

### Mudado

**BREAKING.** O `agent-memory deploy` passa a gerenciar a metodologia em `AGENTS.md` exclusivamente dentro de um bloco delimitado por sentinelas markdown (`<!-- >>> agent-memory >>> -->` / `<!-- <<< agent-memory <<< -->`). Refresh é idempotente: re-deploy substitui só o bloco, todo o resto do arquivo é preservado byte-a-byte. Identidade, restrições, convenções e qualquer outro conteúdo específico do projeto vivem fora do bloco e nunca são tocados pelo deploy ou pela skill `memory-deploy`. O comportamento anterior de "merge inteligente" baseado em comparação de headings (introduzido em v0.3.1) é abandonado em favor desta abordagem mais simples.

A skill `memory-deploy` perde a Etapa 3 (merge) e a Etapa 4 (personalização) inteiras. Em greenfield, a skill apenas roda o deploy mecânico — não pergunta sobre identidade/stack/restrições nem popula o frontmatter. Em legacy, conduz três fases de gênese retroativa: ADRs do git log, Manifest dos entrypoints, e `STATE.md::Current` descrevendo a gênese. A skill nunca toca em `AGENTS.md` fora do bloco.

Decisão formalizada em [ADR-0011](.agent-memory/decisions/0011-deploy-replaces-agent-md-block-via-sentinels.md), que supersede [ADR-0010](.agent-memory/decisions/0010-merge-separates-methodology-from-project-sections.md).

### Removido

Mecanismo de merge-queue (`<projeto>/.agent-memory-deploy/merge-queue` e `pending/`) eliminado. O deploy resolve o bloco da `AGENTS.md` diretamente via sentinelas, sem handoff intermediário. Diretório legado é removido automaticamente na primeira execução pós-upgrade.

### Migração de 0.3.x → 0.4.0

Para projetos consumidores que estão na v0.3.x:

```bash
agent-memory deploy /caminho/projeto
```

O bloco com sentinelas é anexado ao fim do `AGENTS.md` existente. O conteúdo de metodologia que estava em seções H2 separadas (`## Skills disponíveis`, `## Como retomar trabalho`) e no parágrafo introdutório fica duplicado — agora dentro do bloco e ainda nas seções antigas. Remova manualmente as seções antigas (basta deletar tudo entre `## Skills disponíveis` e `## Como retomar trabalho` inclusive, se essas eram as únicas seções de metodologia preexistentes).

## [0.3.1] - 2026-04-30

### Corrigido

Skill `memory-deploy` (Etapa 3) tinha bug de concatenação no merge do `AGENTS.md`: quando o template novo carregava `## Identidade` como placeholder e o existente já tinha conteúdo real, a heurística "adiciona seções novas ao final" produzia arquivo com seções duplicadas. O algoritmo de merge foi reescrito para separar seções de metodologia (sincronizadas a partir do template) de seções de projeto (preservadas a partir do existente), com ordem fixa do resultado: intro → projeto → Skills → Como retomar trabalho.

### Mudado

Template `AGENTS.md` deixa de carregar placeholders para as seções de projeto (`## Identidade`, `## Restrições não-negociáveis`, `## Convenções de código`) — apenas um comentário HTML marca o ponto de inserção. A skill `memory-deploy` escreve essas seções a partir da investigação do repositório durante a Etapa 4 (personalização ou gênese retroativa). Decisão formalizada em [ADR-0010](.agent-memory/decisions/0010-merge-separates-methodology-from-project-sections.md).

## [0.3.0] - 2026-04-29

**BREAKING CHANGE.** Modelo de instalação muda de "clonar para `.agent-memory/`" para "instalar como pacote Python via pipx". A CLI vira `agent-memory <subcomando>` no PATH, eliminando duplicação de scripts em cada projeto consumidor e permitindo que edições no clone reflitam imediatamente em todos os projetos via editable install.

### Adicionado

`pyproject.toml` define o pacote `agent-memory` com entry point `agent-memory = "agent_memory.cli:main"` e package data (`templates/`, `skills/`, `hooks/`) sob `src/agent_memory/data/`. Versão é lida dinamicamente de `VERSION`.

Quatro subcomandos da CLI: `agent-memory deploy <target>`, `agent-memory audit`, `agent-memory propose-adr`, `agent-memory migrate`.

Suite de testes com `pytest` em `tests/`, cobrindo a função de sentinel block, a superfície da CLI, e o fluxo end-to-end de deploy. Dev deps declarados em `pyproject.toml::[project.optional-dependencies] dev`.

Seção "Implicações do editable install" no [USER_GUIDE.md](USER_GUIDE.md) explicando o que muda em `pipx install -e <clone>` vs `pipx install agent-memory` (futuro).

### Mudado

Layout do código move de top-level (`deploy.py`, `tools/`, `templates/`, `skills/`) para `src/agent_memory/` com src layout padrão de packaging Python. Templates, skills e hooks ficam em `src/agent_memory/data/` para serem acessíveis via `importlib.resources`.

`deploy.py` agora aceita o caminho do projeto consumidor como argumento explícito (`agent-memory deploy <target>`), em vez de inferir pela localização do script.

Pre-commit hook agora chama `agent-memory audit --strict --no-index` em vez de procurar `audit.py` em paths fixos. Se o `agent-memory` não está no PATH, emite warning e libera o commit (não bloqueia).

Estado transiente do deploy moveu de `.agent-memory/.merge-queue` e `.agent-memory/.pending-merge/` (dentro do clone-into-project) para `<target>/.agent-memory-deploy/{merge-queue,pending/}` (no projeto consumidor, gitignored).

Skills (`memory-deploy`, `memory-bootstrap`, `memory-debrief`) e documentação atualizadas para usar a nova superfície de CLI.

### Removido

Modelo de "clone para `.agent-memory/`" não é mais suportado. Quem está em v0.1.0/v0.2.0 deve seguir o caminho de migração na seção abaixo.

Subcomando `agent-memory audit --init` (que apenas criava as pastas `manifest/features/` e `decisions/proposals/`) — sobreposição funcional com `agent-memory deploy <projeto>`, que faz o mesmo e mais. Usuários que dependiam de `--init` devem migrar para `agent-memory deploy`.

### Migração de 0.2.0 → 0.3.0

```bash
# 1. Instalar a nova CLI (uma vez na máquina)
git clone https://github.com/brunoleos/agent-memory.git ~/dev/agent-memory
cd ~/dev/agent-memory && git checkout v0.3.0
pipx install -e ~/dev/agent-memory

# 2. Em cada projeto consumidor, rodar deploy (idempotente)
cd /caminho/projeto
agent-memory deploy /caminho/projeto

# 3. Limpar o legado .agent-memory/ (instruções impressas pelo deploy)
git rm -r --cached .agent-memory/
rm -rf .agent-memory
git commit -m "chore: drop .agent-memory/ (agent-memory v0.3.0)"
```

Os artefatos da metodologia (`AGENTS.md`, `STATE.md`, `manifest/`, `decisions/`, `skills/`, `.gitattributes`) ficam preservados. Apenas a pasta `.agent-memory/` (que continha a tool clonada) é descartada — a tool agora vive na sua máquina, fora do projeto.

## [0.2.0] - 2026-04-29

Modelo de instalação minimalista: `.agent-memory/` agora é gitignored no projeto consumidor e re-clonado em fresh checkouts, eliminando duplicação no histórico Git. O ciclo de update vira três comandos de shell, sem configuração persistente.

### Mudado

`deploy.py` agora adiciona `.agent-memory/` ao `.gitignore` do projeto consumidor automaticamente (bloco delimitado por sentinelas, idempotente).

`deploy.py` agora sempre atualiza as skills em `skills/` a cada execução (eram puladas se já existiam). Skills são conteúdo de metodologia, não de usuário; quem precisa customizar deve copiar a skill para um nome diferente.

`deploy.py` agora gerencia o `.gitattributes` via bloco com sentinelas, permitindo refresh idempotente do conteúdo da metodologia sem destruir regras locais adicionadas fora do bloco.

### Removido

`update.py`, `.upstream.example`, `.upstream` e `.installed-version`. O fluxo de atualização agora é `rm -rf .agent-memory && git clone --branch <tag> ... .agent-memory && python .agent-memory/deploy.py`.

### Migração de 0.1.0 → 0.2.0

Para projetos que instalaram a v0.1.0 e versionavam `.agent-memory/`, a migração tem quatro passos. O `deploy.py` da v0.2.0 detecta o cenário e imprime as instruções automaticamente quando rodado:

```bash
rm -rf .agent-memory
git clone --depth 1 --branch v0.2.0 \
  https://github.com/brunoleos/agent-memory.git .agent-memory
python .agent-memory/deploy.py
git rm -r --cached .agent-memory/
git commit -m "chore: untrack .agent-memory/ (agent-memory v0.2.0)"
```

Os arquivos da pasta continuam no disco; só saem do índice do Git para que mudanças futuras na tool não apareçam como diff no projeto consumidor.

## [0.1.0] - 2026-04-28

Versão inicial pública. Estabelece a fundação da metodologia.

### Adicionado

Quatro artefatos versionados (`AGENTS.md`, `STATE.md`, `manifest/`, `decisions/`) com schemas validados e separação por ciclo de mutação.

Notação EARS completa para critérios de aceitação, com seis padrões (cinco canônicos mais `complex` como escape) validados pelo `audit.py`.

Pre-commit hook que bloqueia commits violando o protocolo, com `--no-verify` como válvula de escape.

Gerador de propostas de ADR (`propose-adr.py`) com detecção de sinais de mudança arquitetural não-trivial e modo `--prompt` para integração com agentes LLM.

Três skills cobrindo os fluxos críticos: `memory-deploy` para instalação adaptativa (greenfield/legacy/merge), `memory-bootstrap` para início de sessão, `memory-debrief` para fim de unidade de trabalho.

Suporte multi-agente via convenção `AGENTS.md` com `CLAUDE.md` como redirect mínimo para o Claude Code.

Workflow de merge e rebase com `.gitattributes` configurando driver `ours` para artefatos voláteis e detecção de colisões de IDs via `audit.py --check-collisions`.

Manual do usuário (`USER_GUIDE.md`) cobrindo instalação, fluxo típico, comandos importantes, resolução de problemas e trabalho em time.

Versionamento semântico com `VERSION` e `CHANGELOG.md`.
