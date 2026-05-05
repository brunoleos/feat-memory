---
id: ADR-0020
date: 2026-05-04
status: accepted
supersedes: null
superseded_by: null
affects_features: [F-0016]
related: [ADR-0008, ADR-0014, ADR-0016]
tags: [hooks, semver, release, fail-open-exception]
---

# ADR-0020 · Pre-commit hook bloqueia (hard) commits que tocam código sem bumpar VERSION

## Contexto

Após F-0013 introduzir o aviso staleness (soft, sempre exit 0) sobre commits que tocam código sem atualizar STATE.md, ficou exposto o caso simétrico mais arriscado: commits que tocam código sem bumpar `VERSION`. Os sintomas são piores que staleness:

- Releases sem bump → consumidores via `pipx upgrade` recebem código novo com mesma versão visível, frustrando rastreabilidade.
- F-0010 grava `__version__` em `.agent-memory/.meta.yaml` no consumidor; sem bump, o `meta.yaml` fica congelado mesmo após mudanças relevantes.
- F-0014 (telemetria) anota `version` em todo evento; eventos diferentes ficam indistinguíveis.
- F-0018 (em planejamento — notificação ao consumidor) depende de versão honesta para detectar drift.

A pergunta de design é se este check segue a política soft de F-0013/ADR-0016 ou abre exceção para hard (bloqueia o commit). ADR-0008 firmou fail-open como princípio do hook, mas explicitamente para "binário ausente no PATH". O caso aqui é diferente — não há ambiguidade sobre o que deveria acontecer: se há código novo, há bump. Soft treinaria bypass habitual. Hard fica defensável **se** o usuário tem caminho fácil de bypass deliberado quando ele realmente quer (ex: WIP commits).

`git commit --no-verify` cobre o caso WIP. O hook já documenta esse escape na mensagem de erro do audit. Faz sentido reusar a mesma convenção.

## Decisão

Novo subcomando `agent-memory check-version-bump-staged`, invocado pelo pre-commit hook após `agent-memory check-staleness-staged`. Comportamento:

- Lê `git diff --cached --name-only` para listar paths em staging.
- Se nenhum path for "código" (heurística importada de `audit._is_code_path`, mesma de F-0011/F-0013), retorna 0 sem bloquear.
- Se há paths de código E `VERSION` não está em staging, retorna 1 com mensagem em vermelho na stderr explicando: bump conforme SemVer (patch/minor/major) e como contornar com `--no-verify`.
- Se `VERSION` (arquivo na raiz) **não existe**, é no-op (exit 0). Projetos que não adotam o arquivo `VERSION` ficam imunes ao guard automaticamente. Auto opt-in: basta criar o arquivo.

O hook propaga o exit code via `result.returncode or bump_check.returncode` — qualquer um falhando bloqueia, mas a falha do audit toma precedência semântica (ela carrega a instrução de `--no-verify` mais detalhada).

A heurística de "código" é compartilhada com F-0011 e F-0013: importa `_is_code_path`, `STALENESS_NONCODE_PREFIXES`, `STALENESS_NONCODE_EXACT` de `audit.py`. Uma única definição vale para todos os três sinais.

## Consequências

**Positivas**:

- Releases sempre rastreáveis. Mesma versão visível ⇔ mesmo código (módulo bypass deliberado via `--no-verify`).
- Habilita F-0010 (`.meta.yaml::version`), F-0014 (telemetria com versão) e F-0018 (notificação de update) com fundamento honesto: a versão registrada reflete a versão real.
- Auto opt-in via existência do arquivo `VERSION`. Projetos que ainda não adotam SemVer estrito não pagam custo. Projetos que adotam ganham proteção sem configuração.
- Heurística unificada de "código" entre F-0011, F-0013 e F-0016: ajuste em um único lugar (`audit.STALENESS_NONCODE_*`) propaga para todos os sinais.
- Reusa o caminho de bypass já conhecido (`--no-verify`); não introduz nova superfície de configuração.

**Negativas**:

- Quebra o princípio fail-open de ADR-0008 — agora há um caminho onde o hook **bloqueia** o commit. Mitigação: ADR-0008 cobria especificamente "binário ausente no PATH" (ambíguo, fora do controle do dev); aqui o sinal é determinístico (código vs ausência de bump) e o bypass deliberado existe.
- Falsos positivos esperados em workflows com refactors em vários commits que vão acumular bump no commit final. Bypass via `--no-verify` em commits intermediários é o caminho aceito.
- O check só sabe que `VERSION` está em staging, não que o conteúdo foi de fato bumpado para algo coerente. Alguém pode `echo "0.5.0" > VERSION && git add VERSION` e enganar. Aceito como custo de simplicidade — validação semântica de SemVer fica para horizonte futuro se houver fricção real.
- Hook agora roda 3 subcomandos em sequência (audit, staleness, version-bump), aumentando latência marginal de cada commit. Cada um é centenas de ms; total ainda subsegundo.

## Alternativas rejeitadas

**Manter soft (warning, exit 0) como F-0013**. Discutido acima. Soft treinaria a ignorar — versão se tornaria mentirosa silenciosamente, exatamente o que F-0010 e F-0018 não podem tolerar. Rejeitada por incoerência com features dependentes.

**Validar conteúdo de VERSION (parse SemVer + comparação contra HEAD)**. Mais robusto, mas adiciona complexidade significativa: precisa parsear SemVer, conhecer regra (qualquer bump? só major/minor?), tratar pre-releases, build metadata. Rejeitada por escopo — verificar staging cobre 95% dos casos com 5% da complexidade.

**Configurar via flag em `.meta.yaml::version_bump_required`**. Defensável (alguns projetos podem querer hard, outros soft). Rejeitada por inflar superfície sem caso real pedindo. Auto opt-in via existência de `VERSION` já segmenta o caso "não me importo agora".

**Rodar o check fora do hook, só na CI**. Funciona, mas perde o ponto de máxima alavancagem (commit em curso, dev pode reagir imediatamente). Rejeitada — hook captura cedo, CI captura tarde.

**Bloquear apenas em branch `main`/`master`**. Reduziria fricção em feature branches. Rejeitada porque agente trabalhando em qualquer branch ainda pode esquecer; melhor ensinar disciplina sempre, com `--no-verify` para WIP. Branch-aware é elegância sem ganho prático.
