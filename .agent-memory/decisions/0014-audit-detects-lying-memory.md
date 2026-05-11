---
id: ADR-0014
date: 2026-05-04
status: accepted
supersedes: null
superseded_by: null
affects_features: [F-0011]
related: [ADR-0002, ADR-0008, ADR-0013]
tags: [audit, schema, validation, freshness, dogfooding]
---

# ADR-0014 · Audit detecta memória mentirosa via cross-check de STATE.md e staleness opcional

## Contexto

A `validate_state()` em [audit.py:170](src/agent_memory/audit.py#L170) hoje só valida o frontmatter de `STATE.md` — schema_version, updated_at, active_features presentes, dentro do orçamento de bytes. Não verifica se as listas `active_features` e `active_decisions` apontam para artefatos que existem. Já vimos casos similares onde [validate_feature():281](src/agent_memory/audit.py#L281) detecta drift quando um caminho em `contracts.api|tests` não existe — bom precedente da mesma classe de defeito.

O risco concreto: se um ADR for renomeado/removido sem atualizar STATE.md, ou se uma feature for arquivada mas continuar listada como ativa, o agente confia em `STATE.md` na retomada e tenta carregar arquivos inexistentes. A skill `memory-bootstrap` é especialmente sensível porque ela materializa só os IDs listados em `active_*`. Memória que aponta para o vazio é pior do que memória ausente — ela parece confiável.

Há também uma classe de defeito mais branda: o repositório recebeu commits de código relevante nos últimos N dias, mas `STATE.md` não foi tocado no mesmo período. Isso sinaliza que a skill `memory-debrief` foi pulada — o foco da sessão registrado em STATE provavelmente não reflete mais a realidade. Não dá para cravar como erro (o agente pode legitimamente ter esquecido um detalhe sem mentir), mas é sinal forte o bastante para warning.

ADR-0008 estabeleceu que o pre-commit hook é fail-open. ADR-0002 estabeleceu severities `hard`/`soft` para restrições. Esta decisão honra ambos: cross-check de existência é fato (hard), staleness é sinal (soft, e opt-in para não inflar a barra de qualidade do hook).

## Decisão

A `validate_state()` ganha duas extensões, separadas por nível de confiança:

**1. Cross-check de existência (hard, default-on).** Para cada `F-NNNN` em `active_features`, exige que exista arquivo `F-NNNN-*.md` em `.agent-memory/manifest/features/` ou `.agent-memory/manifest/archive/` (esta última prevista por F-0012 — busca em ambos os diretórios desde já, mesmo que `archive/` ainda não exista). Para cada `ADR-NNNN` em `active_decisions`, exige arquivo `NNNN-*.md` em `.agent-memory/decisions/`. Falhas viram `Issue` com severity `error` — bloqueia o pre-commit hook (que já fail-fast no exit code da audit).

A implementação fica em uma nova `validate_state_crosscheck(state_fm, features, decisions)` separada de `validate_state()`, porque depende de features/decisions já carregadas. É invocada em `run_audit()` após `validate_feature` e `validate_decision` terem populado as listas. Isso evita duplicar I/O e mantém a função original com responsabilidade única (frontmatter shape).

**2. Staleness check (soft, opt-in via `--check-staleness`).** Nova função `validate_state_freshness(repo_root, days=7)` invocada apenas quando `agent-memory audit --check-staleness` for chamado explicitamente. NÃO roda no pre-commit hook por padrão, NÃO roda no `agent-memory audit` sem flag — é diagnóstico para o usuário.

Heurística: roda `git log --since="<days> days ago" --name-only --pretty=format:` para listar arquivos tocados em commits recentes. Se algum commit no período tocou arquivos "de código" (heurística: arquivos fora dos prefixos `.agent-memory/`, `tests/`, `docs/`, e fora dos paths exatos `README.md`, `CHANGELOG.md`, `METHODOLOGY.md`, `USER_GUIDE.md`, `FUTURE_IMPROVEMENTS.md`, `LICENSE`) e nenhum commit no período tocou `.agent-memory/STATE.md`, emite `Issue` com severity `warning`: "STATE.md não foi atualizado nos últimos N dias enquanto código foi tocado — considere `/memory-debrief`".

A janela é parametrizada por flag (`--check-staleness=N`, default 7). Se o repositório não tem commits no período (greenfield/dormente), a verificação retorna sem warning.

## Consequências

**Positivas**:

- Memória mentirosa via referência quebrada vira erro mecânico — o pre-commit pega antes do push, não 2 semanas depois quando o agente tenta retomar.
- Reaproveita a infraestrutura existente: `Issue` dataclass, `_init_paths()`, glob de features/decisions já carregada por `run_audit()`. Diff focado, sem novo módulo.
- Staleness opt-in respeita o princípio do hook fail-open (ADR-0008): comportamento default não fica mais barulhento. Quem quer o sinal pede explicitamente.
- Contagem em ambos `features/` e `archive/` antecipa a chegada de F-0012 sem custo agora — quando o arquivamento existir, IDs ativos já recém-arquivados não vão falsamente quebrar a auditoria.
- Heurística de "código" é estável e auditável — paths bem conhecidos do projeto. Falsos positivos esperados (ex: edição massiva de testes sem código): aceitos como custo do sinal.

**Negativas**:

- Quebra retrocompat para projetos consumidores cujo STATE.md já lista IDs órfãos. Mitigação: a mensagem de erro diz exatamente qual ID não tem arquivo — o usuário corrige em segundos. E é o tipo de "quebra" que sinaliza problema real (era memória mentirosa).
- O cross-check duplica leitura de diretórios já varridos por `run_audit()`. Custo desprezível em projetos típicos (dezenas de features, não milhares).
- A heurística de "arquivo de código" via blacklist é frágil para projetos com layouts atípicos (ex: monorepo com `apps/`, `packages/`). Fica como TODO claro: no horizonte próximo, se virar fricção, expomos a lista via configuração no frontmatter de `AGENTS.md` (ex: `audit.code_paths`). Por ora, paths fixos minimizam superfície e atendem o repo deste projeto.
- `--check-staleness` exige `git log`, então não funciona fora de repositório Git. Fail-soft: se git não responde, retorna sem warning (não promove a erro).

## Alternativas rejeitadas

**Cross-check como warning em vez de error**. Soaria conservador, mas memória mentirosa é exatamente o defeito que esta tool existe para combater. Suavizar transformaria o sinal em ruído. Rejeitada por dissolver o valor.

**Cross-check opt-in em vez de default-on**. Mesma crítica: a maioria dos usuários não saberia que existe a flag, e os casos onde quebra o status quo (IDs órfãos) são exatamente onde o defeito mora. Default-on é o ponto. Rejeitada.

**Staleness como erro hard**. Tentador, mas falsifica o que a métrica mede: o sinal é correlativo (commit sem update de STATE), não dedutivo (não dá para provar que o agente esqueceu de debriefar — talvez o commit foi trivial e o foco não mudou). Erro hard quebraria fluxos legítimos. Rejeitada por mismatch entre força do sinal e força da resposta.

**Detectar staleness via mtime do STATE.md em vez de git log**. Mais simples, mas mtime não persiste em clones frescos e não tem semântica de commit. `git log` é a fonte de verdade da atividade do projeto. Rejeitada por fragilidade.

**Embutir lista de "code paths" no frontmatter de AGENTS.md já agora**. Configuração antes de necessidade real é overhead. Espera-se um caso concreto de fricção (ex: monorepo) para justificar. Rejeitada por YAGNI.
