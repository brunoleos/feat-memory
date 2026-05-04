---
id: ADR-0008
date: 2026-04-29
version: v0.3.0
status: accepted
supersedes: null
superseded_by: null
affects_features: [F-0005]
related: []
tags: [hooks, audit, ux]
---

# ADR-0008 · Pre-commit hook chama `agent-memory audit` diretamente; fail-open quando ausente do PATH

## Contexto

Antes do redesenho da v0.3.0, o pre-commit hook procurava `audit.py` em paths fixos relativos ao projeto consumidor — frágil, dependia da estrutura interna de `.agent-memory/`. Com a CLI `agent-memory` no PATH (ADR-0007), o hook pode chamar diretamente `agent-memory audit --strict`, eliminando a busca por path.

Surge então uma sub-pergunta: o que fazer quando o binário `agent-memory` **não** está no PATH? Esse cenário acontece quando um desenvolvedor clona o projeto mas ainda não fez `pipx install` da tool, ou quando o ambiente CI roda hooks sem ter a tool instalada. Duas opções com trade-offs reais: bloquear o commit (consistente com o espírito strict) ou liberar com warning (fail-open).

## Decisão

O pre-commit hook chama `agent-memory audit --strict --no-index` diretamente. Quando o binário `agent-memory` não está no PATH, o hook emite um warning com instruções de instalação e libera o commit (fail-open). Quando o binário está presente e a auditoria falha, o commit é bloqueado normalmente, conforme esperado em modo strict. A válvula de escape `git commit --no-verify` continua disponível para casos excepcionais.

## Consequências

O hook funciona ergonomicamente para quem tem a tool instalada — auditoria roda automática, falhas bloqueiam commit, fluxo é transparente. Quem ainda não instalou recebe um nudge informativo em vez de um bloqueio frustrante, alinhado com o princípio de "nudge, não coerção" documentado em METHODOLOGY. O hook não vira obstáculo para quem está apenas começando a explorar o projeto.

Custo: em ambientes onde a tool *deveria* estar instalada (e.g., CI), o fail-open mascara o problema — o build passa sem auditoria mesmo quando deveria falhar. Mitigação: a CI deve rodar `agent-memory audit --strict` explicitamente como step separado e bloquear o merge no exit code, sem confiar apenas no hook como rede de segurança.

## Alternativas rejeitadas

Bloquear o commit quando o binário está ausente foi rejeitado porque hooks que falham por estado do ambiente acabam sendo desinstalados (`rm .git/hooks/pre-commit`) por usuários frustrados. Hook desinstalado não protege ninguém. Fail-open mantém o nudge no caminho feliz e a proteção quando a tool está disponível, sem criar atrito que destrói o hábito.

Manter o hook procurando `audit.py` em paths fixos foi rejeitado pela fragilidade óbvia — qualquer reorganização interna do pacote quebra o hook. Chamar a CLI no PATH desacopla o hook da estrutura interna da tool.
