---
id: ADR-0022
date: 2026-05-05
status: accepted
supersedes: null
superseded_by: null
affects_features: [F-0018]
related: [ADR-0008, ADR-0013, ADR-0020, ADR-0021]
tags: [governance, observability, consumer-notice, soft-warning]
---

# ADR-0022 · Notificação soft ao consumidor quando CLI difere de `.meta.yaml::version`

## Contexto

ADR-0013 firmou que o `agent-memory deploy` grava `.agent-memory/.meta.yaml::version` no consumidor com a versão do CLI no momento do deploy. ADR-0020 introduziu um guard hard que bloqueia commits com código sem bumpar `VERSION`, garantindo que `__version__` evolua honestamente.

Falta o elo de feedback: **o consumidor não sabe quando a sua estrutura foi produzida por uma versão antiga do CLI**. As skills evoluem aqui (memory-bootstrap, memory-debrief, etc.); novos templates ou novos blocos de sentinela em `AGENTS.md` chegam via `agent-memory deploy` re-rodado. Sem notificação, o usuário descobre desatualização tarde — quando uma skill faz algo inesperado ou um manifest field novo aparece sem suporte do agente local.

Quando o usuário foi questionado sobre o que o projeto resolve, ele disse explicitamente: "as skills aqui evoluem, então tenho que saber quando os projetos consumidores precisam se atualizar". Esta feature endereça exatamente esse pedido.

A pergunta de design não é "notificar?", é "**onde, com qual severidade, e com que frequência**?":

- **Onde**: subcomando dedicado, integrado no audit, em todo subcomando, no boot da CLI?
- **Severidade**: hard (bloqueia), soft (warning), ou notice (informativo)?
- **Frequência**: toda invocação, uma vez por sessão, uma vez por dia, opt-in?

ADR-0008 estabeleceu fail-open como princípio do hook. ADR-0020 abriu uma exceção justificada (release discipline). Aqui não há justificativa para hard — atualizar não é obrigatório, e bloquear seria fricção excessiva. Soft+ruidoso treinaria a ignorar. Notice integrado ao audit é o sweet spot: aparece quando o usuário já está olhando, não interrompe outros fluxos.

## Decisão

Novo módulo `src/agent_memory/governance/version_check.py` com função `consumer_version_notice(root: Path) -> str | None`:

- Lê `.agent-memory/.meta.yaml::version` via `shared.parsing.read_meta()`.
- Compara a `agent_memory.__version__`.
- Se diferentes (qualquer direção — incluindo CLI mais antigo que consumer, raro mas possível), retorna texto do notice.
- Se iguais, ou `.meta.yaml` ausente, ou `version_check_enabled: false` no `.meta.yaml`, retorna `None`.

**Texto do notice** (proposta):

```
ℹ agent-memory CLI 0.7.0 vs deployed 0.6.0
  re-rode `agent-memory deploy .` para sincronizar skills/templates
  (mudanças nesta versão podem afetar como o agente carrega contexto).
```

Cor amarela quando `stderr.isatty()`; plain em CI.

**Integração:**

1. **Em `governance.audit.run`**: após `print_report()`, invoca `version_check.consumer_version_notice(_paths.ROOT)` e imprime na stderr se houver. **Não muda exit code.**
2. **Subcomando standalone `agent-memory version-check`**: para invocação direta (CI, scripts). Imprime notice ou "atualizado" e sai com 0.

**Disable**: `.agent-memory/.meta.yaml::version_check_enabled: false`. Default `true`. Coerente com `telemetry_enabled` (ADR-0017). Schema bump implícito do `.meta.yaml` (de v1 para v1+versão_check_enabled, retro-compatível — leitores antigos ignoram campos desconhecidos).

**Direção da diferença**: emitimos notice em qualquer diff (consumer < CLI ou consumer > CLI). Esperado raro o segundo caso (CLI antigo num consumer atualizado), mas o sinal é correto: algo está fora de sincronia, o usuário decide.

**Distinção semver**: a primeira versão **não distingue** patch/minor/major. Qualquer diff dispara notice. Justificativa: simplicidade primeiro; se houver fricção real (ex: consumer recebe N notices/dia por bumps de patch que não exigem re-deploy), evolução natural é distinguir e suprimir patch-only.

**Não fazemos auto-redeploy.** Atualizar toca arquivos do consumidor (templates, skills, hook, .meta.yaml) — decisão do humano. Notice apenas informa.

## Consequências

**Positivas**:

- Fecha o loop de feedback que F-0010 (`.meta.yaml::version`) e ADR-0020 (VERSION-bump-on-code) criaram. Sem F-0018, esses dois investimentos em versão honesta ficam meio órfãos.
- Time pequeno com vários agentes (perfil declarado pelo usuário) recebe notificação coletiva quando alguém atualiza o agent-memory CLI — todos os colegas vêm o notice na próxima vez que rodam audit.
- Soft + integrado em audit é caminho de menor fricção. Roda no pre-commit hook (que invoca audit), aparece em CI logs, fica visível sem ser interrompedor.
- Subcomando standalone (`agent-memory version-check`) dá API clara para integração externa (ex: dashboard mostrando "X projetos com versão Y").
- Disable explícito via `.meta.yaml` respeita o princípio de "controles configuráveis" (mesma porta de `telemetry_enabled`).
- Não introduz nova superfície de hook nem de schema — reusa `.meta.yaml` e a infraestrutura existente.

**Negativas**:

- Notice em toda invocação de audit pode virar ruído em CI com muitos audits/dia. Mitigação: `version_check_enabled: false` em CI environments. Avaliar depois se vale auto-suprimir em CI (heurística: `CI=true` no env).
- Notice direção-agnóstica pode confundir em transições (developer A bumpou local, developer B ainda com versão antiga — ambos vêm notices opostos). Aceitável; o sinal é correto, só precisa ser interpretado.
- Adiciona uma micro-leitura de YAML por audit. Custo desprezível (.meta.yaml < 200 bytes).
- Schema do `.meta.yaml` ganha campo opcional sem bump explícito de schema_version. Leitores antigos ignoram campo desconhecido → backward-compatível, mas vale documentar como Convenção Aditiva.

## Alternativas rejeitadas

**Hard (bloqueia commit/audit) quando desatualizado**. Forçaria atualização. Rejeitada — atualizar não é obrigatório (consumer pode estar deliberadamente em versão antiga por motivos válidos: pin de produção, dependência de skill removida em versão nova, etc.). Hard é ferramenta errada para "informar".

**Notice em TODOS os subcomandos** (cli.main no início). Mais agressivo. Rejeitada — repete a mesma info N vezes, vira ruído de fundo. Audit é o lugar natural ("estou vendo o estado do projeto, mostre tudo relevante").

**Distinguir patch/minor/major no momento de emitir o notice**. Mais inteligente. Rejeitada na primeira versão por complexidade prematura: requer parsear semver, definir política (ex: só warna em minor+), manter regra. Simples primeiro; evolui se houver fricção real.

**Embutir minimum_required_version no próprio template de AGENTS.md** (sentinel block). Skill files declaram que versão mínima do CLI esperam. Mais rigoroso. Rejeitada por overhead de manutenção (cada release precisaria atualizar sentinels) sem ganho claro vs notice simples baseado em diff.

**Notice apenas quando consumer < CLI** (não no caso oposto). Mais limpo na maioria dos casos. Rejeitada — a regra simétrica "qualquer diff = notice" é mais fácil de raciocinar e captura o caso raro (CLI rodando contra consumer mais novo, sintoma de pipx desatualizado em algum colega).

**Auto-redeploy quando detectar diff**. Tentador (simétrico a `pip install --upgrade`). Rejeitada — redeploy toca arquivos do consumidor (templates, hooks, .meta.yaml) e deve ser decisão explícita, especialmente em times pequenos com vários agentes onde colega B pode estar testando uma versão antiga deliberadamente.
