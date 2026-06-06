---
id: ADR-0031
date: 2026-06-03
status: accepted
version: 0.13.0
supersedes: null
superseded_by: null
affects_features: [F-0026]
related: [ADR-0030, ADR-0003, ADR-0004]
tags: [methodology, genesis, legacy, reverse-engineering, tests, ui, precision]
---

# ADR-0031 · gênese retroativa é engenharia reversa multi-fonte com triangulação

## Contexto

ADR-0030 inverteu a gênese para **code-first** (código primário, git secundário).
Mas "ler o código" é instrução insuficiente: código é a verdade do *comportamento*,
não da *intenção* — extrair propósito a partir dele exige inferência, e inferência
solta aluciná. A skill `memory-deploy` tratava o problema como binário (código vs
git) e ignorava as fontes que **descrevem intenção com mais precisão que o código
cru**:

- **Testes** — especialmente aceitação/E2E — são spec executável, mantida e
  verificada por asserção. Cada cenário ≈ uma feature; cada asserção ≈ um critério
  `acceptance` EARS. É a fonte mais precisa de comportamento *pretendido*, e não era
  citada na skill.
- **UI / telas** — em apps com frontend, o conjunto de telas/rotas/forms ≈ o
  conjunto de capacidades, e labels/i18n nomeiam as features na língua do usuário
  (matéria-prima direta de `user_value`). Também ignorada.
- **Documentação viva** (README/CHANGELOG/OpenAPI), **dependências** e **estrutura**
  completam o quadro — cada uma com confiabilidade diferente para inferir intenção.

Feedback do mantenedor: *"o código é a pura fonte da verdade, mas é código: precisa
de inferência para entender o propósito. Testes trazem muita informação sobre o uso;
as telas também dizem bastante."* O ponto: precisão vem de **triangular** fontes
heterogêneas, não de eleger uma só.

## Decisão

A gênese retroativa é um **protocolo de engenharia reversa multi-fonte** com objetivo
explícito de **alta precisão e baixa alucinação**. Refina ADR-0030 (não o substitui):
o code-first permanece, mas "código" se expande para um conjunto ordenado de fontes
com técnicas de leitura.

1. **Fontes de evidência, ranqueadas por precisão para inferir propósito**
   (na skill, Etapa 3):
   1. Testes (comportamento pretendido, executável)
   2. UI/telas (capacidades como o usuário as vê)
   3. Documentação viva (intenção declarada, pode estar stale)
   4. Entrypoints + código (verdade do comportamento; propósito por inferência)
   5. Dependências + estrutura (= decisões de arquitetura)
   6. Git (porquê/quando; secundário e variável)

2. **Técnicas de precisão**, codificadas na skill:
   - **Triangulação** — só cristalize o que ≥2 fontes independentes confirmam;
     fonte única é hipótese.
   - **Confiança em camadas** — separe *observado* (teste asserta / código faz) de
     *inferido* (palpite de intenção); só cristalize o observado.
   - **Top-down + bottom-up** — hipóteses das docs/telas/entrypoints, verificação
     pelos testes/código; divergência é sinal.
   - **Cobertura = mapa de importância**; **nomes são evidência, não prova**;
     **ausência é sinal**; **datar por múltiplos sinais** (blame, lockfile,
     CHANGELOG).

3. **`feat-memory migrate` passa a emitir os sinais de teste e UI**, agnóstico de
   linguagem: `detect_test_signals` (diretórios de convenção + padrão de nome
   `test_*`/`*_test`/`*.spec`) e `detect_ui_signals` (diretórios de view +
   extensões `.html/.vue/.svelte/.jsx/.tsx/.astro`). O output reordena para a ordem
   de precisão (testes → UI → entrypoints → git) e o JSON ganha `test_signals`/
   `ui_signals`. A ferramenta aponta as fontes certas; a leitura é do agente.

4. **`acceptance` deriva preferencialmente das asserções dos testes** (Fase 3.2), e o
   arquivo de teste entra em `contracts` como contrato executável da feature.

## Consequências

Positivas: a gênese fica drasticamente mais precisa onde há testes/UI (a maioria dos
projetos legacy maduros); `acceptance` EARS deixa de ser inferência solta e passa a
espelhar asserções reais; a triangulação e a marcação de confiança reduzem
cristalização de palpites; a doutrina fica explícita e ensinável em vez de "leia o
código e use bom senso".

Negativas: a Etapa 3 da skill ficou mais longa e densa (aceito — é instrução de alto
valor, lida sob demanda, não orçamento de retomada); as heurísticas de detecção de
teste/UI no `migrate` têm falsos-positivos/negativos (mitigado: são só pistas de
"onde olhar", e a skill manda triangular, não confiar na varredura).

## Alternativas rejeitadas

- **Manter "code-first" genérico (ADR-0030) sem detalhar fontes:** deixava o agente
  reinventar o método a cada gênese e ignorar testes/UI — exatamente o gap relatado.
- **Parser/AST para extrair capacidades automaticamente dos testes:** acoplado a
  framework de teste e linguagem (mesmo anti-padrão de ADR-0028/0030). A leitura
  conduzida pelo agente é agnóstica.
- **Expandir ADR-0030 em vez de criar ADR-0031:** ADR-0030 captura uma decisão
  distinta (a *inversão* de prioridade código↔git); o protocolo multi-fonte com
  triangulação é uma decisão separada que a refina. Mantê-las distintas preserva a
  rastreabilidade.
- **Tratar UI como entrypoint comum:** telas têm semântica própria (capacidade
  visível, nomeada em linguagem de usuário) que merece ser uma fonte de primeira
  classe, não diluída em "entrypoints".
