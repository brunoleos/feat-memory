---
id: F-0003
name: propose-adr
status: shipped
introduced: 2026-04-28
version: 0.3.0
user_value: >
  Detecta automaticamente sinais de mudança arquitetural não-trivial no
  diff atual e gera draft de ADR pré-preenchido, reduzindo a barreira
  para registrar decisões importantes.
contracts:
  api: src/feat_memory/memory/propose_adr.py::run
  tests:
    - tests/test_cli.py
    - tests/test_entrypoint.py
acceptance:
  - id: A1
    pattern: event
    trigger: "feat-memory propose-adr é invocado"
    response: >
      examina diff (HEAD~1..HEAD por padrão) e aplica heurísticas de
      detecção: volume, dependências, múltiplos diretórios, padrões
      linguísticos em mensagens
  - id: A2
    pattern: state
    state: "sinais arquiteturais foram detectados no diff"
    response: >
      gera draft em decisions/proposals/NNNN-draft.md com seções TODO e
      sinais detectados anotados como contexto
  - id: A3
    pattern: optional
    feature: "a flag --staged for fornecida"
    response: "examina mudanças staged em vez de HEAD~1..HEAD"
  - id: A4
    pattern: optional
    feature: "a flag --base <sha> for fornecida"
    response: "compara contra commit específico em vez de HEAD~1"
  - id: A5
    pattern: optional
    feature: "a flag --prompt for fornecida"
    response: >
      emite prompt estruturado para agente LLM em vez de gerar template
      diretamente, separando detecção determinística de redação
  - id: A6
    pattern: optional
    feature: "a flag --force for fornecida"
    response: "gera draft mesmo na ausência de sinais detectados"
  - id: A7
    pattern: unwanted
    trigger: "nenhum sinal foi detectado e --force não foi fornecida"
    response: "sai sem escrever, com mensagem indicando ausência de sinais"
  - id: A8
    pattern: unwanted
    trigger: "base ref inválida (ex.: HEAD~1 sem commits suficientes)"
    response: "exit 1 com mensagem acionável sobre o estado do repositório"
depends_on: []
decisions: []
---

# F-0003 · propose-adr

## Comportamento

Subcomando `feat-memory propose-adr` da CLI, em [src/feat_memory/memory/propose_adr.py](src/feat_memory/memory/propose_adr.py). Drafts vivem em `decisions/proposals/`, subpasta que o `audit` ignora explicitamente para preservar a invariante de imutabilidade dos ADRs reais.

A separação entre detecção determinística (heurísticas no código) e redação (humano ou LLM) é deliberada — manter as duas etapas separadas evita gerar ADRs vazios automaticamente quando heurísticas disparam por acidente. Modo `--prompt` é apropriado quando há agente Claude disponível para redigir o draft completo.

Sinais detectados: cinco arquivos ou cem linhas de mudança; alterações em arquivos de manifesto de dependência; mudanças em três ou mais diretórios distintos; mensagens de commit com padrões como "switched from", "instead of", "deprecated".
