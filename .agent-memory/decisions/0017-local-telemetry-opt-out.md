---
id: ADR-0017
date: 2026-05-04
status: accepted
supersedes: null
superseded_by: null
affects_features: [F-0014]
related: [ADR-0008, ADR-0013, ADR-0014, ADR-0016]
tags: [telemetry, observability, privacy, dogfooding]
---

# ADR-0017 · Telemetria local opt-out de aderência ao protocolo

## Contexto

A metodologia de memória persistente vive ou morre da disciplina de invocar `/memory-bootstrap` no início e `/memory-debrief` antes do commit. Hoje não há feedback sobre se isso de fato acontece. As skills existem, os hooks existem, o cross-check de F-0011 e o aviso staleness de F-0013 endereçam casos extremos — mas a pergunta básica "o agente realmente leu STATE.md hoje?" não tem resposta. Sem o sinal, o investimento em manter STATE.md vivo fica sem feedback.

O risco simétrico é igualmente concreto: investir num mecanismo de telemetria que ninguém usa ou (pior) que vaze dados além do projeto local.

A solução é localizada por construção: um arquivo append-only `.agent-memory/.telemetry.jsonl` no consumidor, sem qualquer rede, sem agregação central, sem dependência externa. Cada evento é uma linha JSON independente, format bem documentado, leitura trivial via `jq` ou `grep` ou um subcomando dedicado. O arquivo fica versionado no Git por padrão para que o histórico sobreviva clones. ADR-0013 já estabeleceu `.meta.yaml` no consumidor — telemetria reusa o mesmo padrão (metadata local, versionável, parsable).

A pergunta-chave de design é opt-in vs opt-out. Opt-in significa que ninguém ativa, ninguém vê o sinal, a feature é peso morto. Opt-out significa que o sinal aparece por padrão, e quem se incomoda desliga. ADR-0013 já reservou o campo `telemetry_enabled: true` no `.meta.yaml` antecipando esta decisão — opt-out é o caminho.

## Decisão

Novo módulo [src/agent_memory/telemetry.py](src/agent_memory/telemetry.py) com função `record(event: str, **fields)`. Comportamento:

- Lê `.agent-memory/.meta.yaml` via `audit.read_meta(root)`. Se `telemetry_enabled` for explicitamente `false`, retorna sem escrever. Se ausente ou `true`, prossegue.
- Anexa uma linha JSON em `.agent-memory/.telemetry.jsonl` com campos:
  - `ts` (ISO 8601 UTC do momento)
  - `version` (lido do `.meta.yaml`; `null` se ausente)
  - `event` (string passada pelo chamador)
  - `**fields` (qualquer dado adicional, serializável)
- Erros são silenciosos. Telemetria nunca pode quebrar um fluxo do usuário — capture exceção amplo, drop. Logging só em modo `--verbose` (futuro, fora deste ADR).

Novo subcomando `agent-memory log` lê e agrega. Comportamento:

- `agent-memory log` lista todos os eventos do JSONL (último primeiro), tabular curto.
- `agent-memory log --since 7d` filtra por janela. `7d` parseado como inteiro+sufixo.
- `agent-memory log --event session_start` filtra por evento específico.
- `agent-memory log --json` saída JSON (uma linha por evento, mantém o input format).
- `agent-memory log --summary` agrega: contagem por evento, taxa de adesão (`session_start_with_state_read=true / total session_start`).

Eventos canônicos (vocabulário inicial, expansível):

- `session_start` — emitido por `memory-bootstrap`. Campo `state_read: bool` indica se a skill chegou a ler `STATE.md` (vs. usuário pulou o ritual).
- `debrief_run` — emitido por `memory-debrief`. Campo `features_touched: list[str]` se disponível.

Skills atualizadas para invocar `agent-memory record <event> --field=value` ao final de cada execução. O subcomando `record` é interno (uso por skills, não documentado em help comum), aceita `--field key=value` arbitrário.

`.agent-memory/.telemetry.jsonl` entra no `.gitignore` template. **Telemetria é dado pessoal de adoção do dev, não memória do projeto.** Versionar em Git distribuiria padrões de uso individual entre colaboradores — vazamento desnecessário. O arquivo permanece local, sobrevive desligamento se não for limpo manualmente, e cada dev tem seu próprio fluxo.

Privacy contract resumido na primeira linha do arquivo (header em comentário JSON-line — ignorado por parsers, lido por humanos):

```jsonl
{"_": "agent-memory telemetry — local only, never sent over network. Disable: .agent-memory/.meta.yaml::telemetry_enabled=false"}
```

## Consequências

**Positivas**:

- Sinal de aderência fica disponível sem custo de rede ou serviço. `agent-memory log --summary` em qualquer ponto do projeto dá visibilidade imediata.
- Opt-out respeitando ADR-0013: o switch já existia no schema do `.meta.yaml`, esta decisão só adiciona o caminho de leitura.
- Erros silenciosos honram ADR-0008 (fail-open). Telemetria quebrada não pode bloquear nem alertar — é diagnóstico, não validação.
- Eventos como JSONL: parsing trivial, append O(1), file-system-friendly. Nenhuma necessidade de DB ou formato custom.
- `.gitignore` mantém o sinal ao usuário individual — versionar geraria conflitos de merge constantes e padrão de uso seria distribuído entre colaboradores, indesejado.
- Skills tornam-se chamadores diretos via `agent-memory record`, evitando acoplamento Python-só (qualquer agente que rodar shell consegue gravar).

**Negativas**:

- O arquivo `.telemetry.jsonl` cresce sem cap. Em projetos longevos, pode chegar a megabytes. Mitigado: append-only é barato; subcomando `log --since` filtra; `log --rotate` é TODO óbvio para versão futura.
- Telemetria local não permite agregação cross-projects nem feedback ao mantenedor da metodologia. Aceito — propósito é feedback ao usuário individual sobre seu projeto, não pesquisa.
- Skills precisam ser atualizadas para chamar `agent-memory record`. Adoção em projetos antigos exige re-deploy. Esperado.
- Eventos arbitrários sem validação de schema: chamador pode passar qualquer `**fields`. Rejeitado pôr validação porque inflaria a barreira para uso novo. Custo aceito: parsing posterior tolera campos opcionais.

## Alternativas rejeitadas

**Telemetria opt-in (default desligado)**. Tentador para conservadorismo de privacidade. Rejeitada porque dado é puramente local — ninguém ganha com privacidade contra si mesmo, e o feature vira peso morto sem ativação. Opt-out na privacidade local não tem custo de privacidade real (nada sai do disco do dev).

**Versionar `.telemetry.jsonl` no Git**. Rejeitada porque distribuiria padrões de uso individual entre colaboradores, geraria conflitos de merge constantes em projetos com múltiplos devs, e empilharia historia em quem clona. Local-only resolve sem perder o ponto.

**Schema validado para eventos via Pydantic / JSON Schema**. Rejeitada por overhead. Eventos são extensíveis e o consumo é tolerante (subcomando `log` exibe campos extra, ignora ausentes). Validação prematura aqui mata flexibilidade onde ela é o ponto.

**Backend remoto (mesmo opcional)**. Rejeitada absolutamente. Telemetria remota muda a natureza do contrato com o usuário. Local-only mantém previsibilidade total.

**Eventos como linhas YAML em vez de JSONL**. JSON é suportado por `jq` direto, parser nativo de Python sem dep extra (`json.loads`), e cada linha é independente. YAML não tem essas garantias. Rejeitada por ergonomia.
