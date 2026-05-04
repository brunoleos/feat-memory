---
id: ADR-0015
date: 2026-05-04
status: accepted
supersedes: null
superseded_by: null
affects_features: [F-0012]
related: [ADR-0002, ADR-0014]
tags: [manifest, archive, retention, retomada, dogfooding]
---

# ADR-0015 · Arquivamento explícito de features shipped via `agent-memory archive`

## Contexto

`gen_manifest_index()` em [audit.py:386](src/agent_memory/audit.py#L386) varre `.agent-memory/manifest/features/F-*.md` e regenera o `INDEX.md` a cada audit. Nada move features para fora do diretório quando elas viram `shipped` — o índice cresce monotonicamente. O efeito direto é no orçamento de retomada: a skill `memory-bootstrap` lê o INDEX inteiro, e cada linha de feature antiga toma espaço sem dar contexto à sessão atual.

ADR-0014 deu a F-0011 (cross-check) o reconhecimento de `manifest/archive/` como segundo diretório válido de features — a infraestrutura já está pronta para que features arquivadas continuem resolvíveis a partir de `STATE.md::active_features`. Falta o mecanismo de movimentação e a regeneração de INDEX consciente da divisão.

A pergunta de design não é "arquivar?", é "automaticamente ou explícito?". Automaticamente significaria: o `audit` move features `shipped` no INDEX cycle. Conveniente, mas tem dois problemas: (1) o audit deixa de ser puramente leitor (hoje só escreve INDEX, não move arquivos), e (2) o `git mv` no meio do audit fica difícil de raciocinar quando algo dá errado num CI. Explícito (subcomando dedicado `agent-memory archive`) preserva separação de responsabilidades e dá ao mantenedor controle direto — exatamente quando ele quer arquivar.

ADRs nunca são arquivados. Eles são registro histórico imutável por design — o `superseded_by` já dá a semântica de "não use mais isto sem custar uma movimentação de arquivo". Mover ADRs quebraria links em features e em outros ADRs.

## Decisão

Novo subcomando `agent-memory archive` em [src/agent_memory/cli.py](src/agent_memory/cli.py), implementado em novo módulo `src/agent_memory/archive.py`. Comportamento:

- **Default é dry-run.** `agent-memory archive` lista o que seria arquivado e sai com 0. Para mover de fato, exige `--apply`. Segurança contra dedo-no-gatilho. Inverte a convenção habitual (default = ação) deliberadamente — o custo de "esqueci o flag" é zero, o custo de "movi sem querer" é commit indesejado.
- **Critério de elegibilidade.** Uma feature `F-NNNN-*.md` em `manifest/features/` é elegível ⟺ `status == "shipped"` E `F-NNNN` não aparece em `STATE.md::active_features`. As duas condições devem se manter; basta uma falhar para a feature permanecer em `features/`.
- **Movimento preserva histórico Git.** Quando o repositório é Git, usa `git mv`. Fallback para `shutil.move` em projetos sem Git ou quando `git mv` falha (ex: arquivo não tracked).
- **Regenera ambos os INDEXes.** Após mover, chama `audit.gen_manifest_index(active_features)` para `manifest/INDEX.md` e nova `gen_archive_index(archived_features)` para `manifest/archive/INDEX.md`. Ambos com mesmo formato (mesmas colunas).
- **ADRs nunca movem.** O subcomando não tem opção para arquivar ADRs. Histórico de decisão tem semântica diferente (immutável, citável, encadeável via `superseded_by`).

`audit.run_audit` ganha capacidade de varrer features em `archive/` para fins de validação de schema e detecção de drift de contracts — features arquivadas ainda devem manter seus contratos coerentes (se o caminho citado em `contracts.api` desaparece, é drift mesmo arquivada). O cross-check de F-0011 já busca em ambos. A geração de INDEX permanece separada: `manifest/INDEX.md` lista só ativas, `manifest/archive/INDEX.md` lista só arquivadas.

## Consequências

**Positivas**:

- Orçamento de retomada cai linearmente com adoção: cada feature shipped saída de `features/` reduz o tamanho do INDEX que `memory-bootstrap` materializa. Em projetos com 30+ features, isso é diferença material.
- Discoverability preservada: `manifest/archive/INDEX.md` é um arquivo legível como qualquer outro. Quem quer ver "o que esse projeto fez no passado" sabe onde olhar. Cross-check resolve referências de IDs antigos sem custo.
- Subcomando dedicado é auditável: cada arquivamento é uma invocação CLI, gera diff Git claro, fácil de reverter. Audit continua só lendo, nada escapa do princípio "ferramenta de leitura não muta arquivos".
- Compatível com F-0011: o cross-check já procura em ambos os diretórios, então mover não quebra `STATE.md::active_features` (improvável que aponte para shipped, mas possível em transições).
- Compatível com Git: `git mv` mantém o histórico de blame e o ADR de revisão futura ainda achará origem da decisão.

**Negativas**:

- Mais um subcomando para o usuário aprender. Mitigação: não é necessário para uso básico — só rende valor depois que o projeto acumula features. Documentação no `agent-memory archive --help` e menção em `memory-debrief` (skill pode sugerir quando vê uma feature recém-marcada `shipped`).
- O default dry-run pode confundir quem espera "ação por padrão". Aceito porque o custo do erro inverso (movimento indesejado) é maior. A mensagem de saída é clara: "[dry-run] N features seriam arquivadas. Use --apply para confirmar."
- Cresce o número de diretórios versionados. `manifest/archive/` é mais um lugar pra olhar. Aceito como custo do valor — alternativa (deletar features shipped) seria perda de história.
- Drift checks rodam mais devagar em projetos grandes (varrer dois diretórios em vez de um). Custo desprezível para a escala típica (dezenas a centenas de features).

## Alternativas rejeitadas

**Arquivamento automático no `audit`**. Move features `shipped` durante o cycle de regeneração de INDEX. Reduz fricção, mas viola separação de responsabilidades e cria comportamento mágico difícil de raciocinar quando dá errado. Rejeitada por mismatch entre uma operação informativa (audit) e uma destrutiva (mv).

**Arquivar via flag em `agent-memory audit --archive`**. Acopla auditoria a movimentação. Mesma crítica acima, com penalidade adicional: o pre-commit hook que invoca audit começaria a mover arquivos durante commits, surpresa horrível. Rejeitada.

**Não ter arquivo separado, usar campo `archived: true` no frontmatter**. Mais simples, evita movimentação. Mas não atinge o objetivo: a feature continuaria em `features/`, o INDEX continuaria gigante, retomada continuaria pagando o custo. Rejeitada por não resolver o problema.

**Default = `--apply` (mover por padrão), `--dry-run` opt-in**. Convencional para CLIs. Rejeitada porque movimentação acidental gera commit não-trivial pra reverter (precisa achar arquivos um a um). Default seguro vence default convencional aqui.

**Arquivar ADRs também (status `superseded`)**. Tentador para reduzir ainda mais o INDEX de decisões. Rejeitada porque ADRs `superseded` ainda são citados (`superseded_by` aponta pra eles, e ADRs novos referenciam pra explicar a evolução). Mover quebraria links sem ganho — e ADRs já são pequenos no INDEX (uma linha cada).

**Deletar features shipped em vez de arquivar**. Resolve INDEX e drift de contracts, mas joga fora história. Antagonista direto ao princípio C3 / ADR-0009 (memória persistente). Rejeitada por vandalismo.
