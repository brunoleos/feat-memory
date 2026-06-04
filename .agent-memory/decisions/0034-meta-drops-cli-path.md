---
id: ADR-0034
date: 2026-06-04
status: accepted
version: 0.14.0
supersedes: null
superseded_by: null
affects_features: [F-0030]
related: [ADR-0013]
tags: [meta, privacy, deploy, cleanup]
---

# ADR-0034 · `.meta.yaml` deixa de versionar `cli_path`

## Contexto

ADR-0013 definiu `.agent-memory/.meta.yaml` para registrar contra qual versão da
metodologia a estrutura foi produzida. Entre os campos estava `cli_path`: o caminho
absoluto resolvido do binário `agent-memory` na máquina de quem rodou o deploy
(ex.: `C:\Users\brunols\pipx\venvs\...`).

Dois problemas, levantados no relatório da Tensegrams:

1. **Vaza layout local.** É um caminho absoluto da home de um dev específico, indo para
   o Git do consumidor (mesmo com `merge=ours`), sem valor algum para outros clones.
2. **Ninguém lê.** Varredura no código confirma: `cli_path` é **escrito** pelo
   `deploy_meta` e nunca lido por nenhum consumidor (nem audit, nem telemetria, nem
   version-check). É dado morto.

## Decisão

Remover `cli_path` do dict gravado em `deploy_meta`. O `.meta.yaml` versionado passa a
conter apenas `schema_version`, `version`, `deployed_at` e `telemetry_enabled` (+ flags
opcionais como `version_check_enabled`).

## Consequências

Positivas: nada de caminho absoluto local no Git do consumidor; o arquivo fica
inteiramente portável entre clones; remove um campo que enganava (parecia significativo,
não era usado).

Negativas: nenhuma funcional — nada consumia o campo. Quem tinha um `.meta.yaml` antigo
com `cli_path` o perde no próximo `deploy` (idempotente, regrava o arquivo).

## Alternativas rejeitadas

- **Manter `cli_path` só num cache local não-versionado:** adiciona maquinário (segundo
  arquivo, `.gitignore`) para um valor que nenhum código lê. Remover é mais simples e
  honesto.
- **Manter como está:** preserva o vazamento de path local e o campo morto que o
  feedback apontou.
