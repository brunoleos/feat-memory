# Changelog

Todas as mudanças notáveis a esta metodologia são registradas neste arquivo.

O formato segue [Keep a Changelog](https://keepachangelog.com/) e o projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Unreleased]

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

Quatro artefatos versionados (`AGENT.md`, `STATE.md`, `manifest/`, `decisions/`) com schemas validados e separação por ciclo de mutação.

Notação EARS completa para critérios de aceitação, com seis padrões (cinco canônicos mais `complex` como escape) validados pelo `audit.py`.

Pre-commit hook que bloqueia commits violando o protocolo, com `--no-verify` como válvula de escape.

Gerador de propostas de ADR (`propose-adr.py`) com detecção de sinais de mudança arquitetural não-trivial e modo `--prompt` para integração com agentes LLM.

Três skills cobrindo os fluxos críticos: `memory-deploy` para instalação adaptativa (greenfield/legacy/merge), `memory-bootstrap` para início de sessão, `memory-debrief` para fim de unidade de trabalho.

Suporte multi-agente via convenção `AGENT.md` com `CLAUDE.md` como redirect mínimo para o Claude Code.

Workflow de merge e rebase com `.gitattributes` configurando driver `ours` para artefatos voláteis e detecção de colisões de IDs via `audit.py --check-collisions`.

Manual do usuário (`USER_GUIDE.md`) cobrindo instalação, fluxo típico, comandos importantes, resolução de problemas e trabalho em time.

Versionamento semântico com `VERSION` e `CHANGELOG.md`.
