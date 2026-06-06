---
id: ADR-0029
date: 2026-06-03
status: accepted
version: 0.13.0
supersedes: null
superseded_by: null
affects_features: [F-0025]
related: [ADR-0011, ADR-0002]
tags: [deploy, onboarding, legacy, constitution, schema]
---

# ADR-0029 · deploy injeta esqueleto de frontmatter em AGENTS.md legado sem frontmatter

## Contexto

No deploy greenfield (sem `AGENTS.md`), o template completo — **com** frontmatter
(`schema_version`, `project`, `constraints`, `references`, `budgets`) — é copiado
([deploy.py](../../src/feat_memory/deploy.py), branch "arquivo ausente"). No deploy
legacy (com `AGENTS.md` já existente), a única mudança que o deploy faz é
inserir/refrescar o bloco entre sentinelas markdown; o topo do arquivo **nunca é
tocado** (ADR-0011).

A consequência é uma assimetria que pune o usuário diligente. Um mantenedor que
escreveu uma constituição rica **em prosa** (identidade, gate de push, lições
operacionais) mas sem YAML frontmatter — caso real observado na adoção em
`tensegrams` — recebe, logo após o deploy:

```
Conformidade de schema:    0.00
[error] AGENTS.md: campo ausente: schema_version
[error] AGENTS.md: campo ausente: project
[error] AGENTS.md: campo ausente: constraints
[error] AGENTS.md: campo ausente: references
[error] AGENTS.md: campo ausente: budgets
```

E o "próximos passos" do deploy instrui *"Edite o frontmatter de AGENTS.md"* —
apontando para um frontmatter que **não existe**. O usuário tem que escrever o
YAML do zero, sem nenhum esqueleto no arquivo guiando a forma. O pior primeiro
contato possível para exatamente quem fez o trabalho direito.

A causa não é a doutrina "deploy nunca autora identidade" (ADR-0011), que é
correta. É o buraco entre *"não escrevo o conteúdo"* e *"não deixo nem a estrutura
vazia para preencher"*. O greenfield já entrega essa estrutura; o legacy não.

## Decisão

No caminho legacy (merge em arquivo existente), se a `AGENTS.md` **não tem
frontmatter** — detecção espelhando `shared.parsing.parse_frontmatter`: o arquivo
não começa com `---\n` — o deploy **prepende um esqueleto de frontmatter** antes de
refrescar o bloco com sentinelas. Implementado em `deploy._ensure_frontmatter`.

1. **Esqueleto distinto do template greenfield.** Um novo template
   `data/templates/AGENTS.frontmatter-skeleton.md`, **não** o frontmatter do
   template greenfield. O greenfield traz constraints de exemplo Python-específicas
   (`Pydantic obrigatório`, `Nenhuma PII em logs`) que, injetadas num projeto JS,
   seriam **conteúdo autorado errado** — pior que o vácuo. O esqueleto legacy traz:
   - `references` e `budgets` **preenchidos e corretos** — são mecânicos, idênticos
     em todo projeto; não há autoria de identidade neles.
   - `schema_version: 2` — fixo.
   - `project`, `stack`, `constraints` como **TODO/vazio** (`constraints: []`), com
     um comentário HTML explicando o que preencher e remontando à doutrina de que a
     prosa de identidade é autoria humana.

2. **É estrutura, não conteúdo.** Injetar a *forma* com placeholders explícitos é
   o mesmo que o greenfield já faz — não viola ADR-0011. A skill `memory-deploy`
   continua proibida de **preencher** os campos por conta própria; ela migra a
   prosa do mantenedor para o esqueleto com aprovação humana.

3. **Idempotente e não-destrutivo.** Só injeta quando não há frontmatter algum.
   Arquivo que já tem frontmatter (mesmo parcial) é deixado intacto — re-deploy não
   duplica. A prosa existente é preservada integralmente abaixo do bloco injetado.

4. **Companheiro de bugfix (mesma entrega, sem ADR próprio):** o template
   `STATE.md` tinha `updated_at: 2026-04-28` hardcoded, copiado verbatim, fazendo a
   auditoria pós-deploy reportar semanas de drift num arquivo recém-nascido. Passa a
   usar o token `{DEPLOY_DATE}`, substituído pelo instante UTC do deploy
   (`deploy._substitute_tokens`), e `updated_by: deploy`.

## Consequências

Positivas: a adoção legacy produz uma baseline que **passa** os checks de presença
de campo do `validate_agent` (que só checa presença, não valor), elevando a
conformidade de schema de 0.00 para limpo no primeiro audit; o "edite o frontmatter"
passa a apontar para um frontmatter real; greenfield e legacy ficam simétricos. O
falso-alarme de frescor do STATE some.

Negativas: `references`/`budgets` no esqueleto duplicam os valores do template
greenfield — duas fontes para um dado que muda raramente (mitigado por serem
mecânicos e por um comentário cruzado). Um `project: TODO-...` não-preenchido passa
o audit mas é claramente um placeholder — aceito, porque é melhor que erro e a skill
conduz o preenchimento.

## Alternativas rejeitadas

- **Reusar o frontmatter do template greenfield no legacy:** injetaria constraints
  de exemplo Python num projeto de outra stack — conteúdo autorado errado, que pode
  ser commitado e esquecido. Esqueleto neutro é mais honesto.
- **Frontmatter comentado (HTML) em vez de YAML real:** os campos não seriam
  parseados e o audit continuaria falhando com "campo ausente". Não resolve.
- **Deixar como está e só documentar no "próximos passos":** mantém o 0.00 e o
  ponteiro para um frontmatter inexistente — a fricção que esta ADR existe para
  remover.
- **A skill `memory-deploy` escrever o frontmatter inteiro com a identidade real:**
  violaria ADR-0011 (deploy/skill não autora identidade). A injeção entrega forma,
  não conteúdo; o preenchimento fica com o humano via skill.
