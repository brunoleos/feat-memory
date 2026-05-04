# Melhorias futuras

Este documento cataloga extensões viáveis para a metodologia, organizadas por horizonte de implementação. Cada item descreve o problema que resolve, a forma proposta e os trade-offs envolvidos. A lista não é uma promessa de roadmap; é um inventário de ideias que a operação real do sistema vai eventualmente justificar ou descartar.

## Implementadas

Esta seção registra o que já saiu do plano e está disponível na metodologia. Os itens permanecem documentados para que a história de evolução da metodologia fique explícita, em vez de ser silenciosa.

### Notação EARS completa

Os critérios de aceitação no Manifest agora seguem os cinco padrões canônicos da Easy Approach to Requirements Syntax: ubiquitous, event, state, optional, unwanted, com um sexto padrão complex como escape para combinações. O `agent-memory audit` valida que cada critério declara `pattern` e contém os campos obrigatórios para aquele padrão. Critérios mal-formados são erro de schema e bloqueiam o build.

### Pre-commit hook

O hook em `src/agent_memory/data/hooks/pre-commit` é instalado pelo `agent-memory deploy` e roda `agent-memory audit --strict` antes de cada commit. A flag `--strict` promove warnings (drift) a errors. O hook respeita `--no-verify` como válvula de escape para casos excepcionais. A combinação recomendada continua sendo hook local mais checagem em CI.

### Geração automática de propostas de ADR

A ferramenta `agent-memory propose-adr` examina o diff atual e detecta sinais de mudança arquitetural não-trivial: volume, dependências alteradas, mudanças em múltiplos diretórios, padrões linguísticos em mensagens de commit. Quando detecta sinais, gera um draft em `.agent-memory/decisions/proposals/`, subpasta que o `agent-memory audit` ignora explicitamente para preservar a invariante de imutabilidade dos ADRs reais. O modo `--prompt` emite um prompt estruturado para um agente LLM em vez do template direto, separando detecção determinística de redação que exige julgamento.

### Portabilidade total via Python

Todas as ferramentas e scripts do pacote estão escritos em Python 3.10 ou superior, sem dependência de shell scripts. O pre-commit hook é Python executável. A única dependência externa é PyYAML, declarada em `pyproject.toml` e instalada automaticamente pelo pipx. O pacote roda em Linux, macOS e Windows nativamente.

### Versionamento semântico e changelog

O pacote tem versionamento semântico em arquivo `VERSION` na raiz (lido dinamicamente pelo `pyproject.toml`) e histórico em `CHANGELOG.md` seguindo o formato Keep a Changelog. Cada release publicada no GitHub corresponde a uma tag `vX.Y.Z` e a uma seção do `CHANGELOG.md`.

### Distribuição como CLI Python (v0.3.0)

O agent-memory é distribuído como pacote Python com entry point `agent-memory = agent_memory.cli:main` definido em `pyproject.toml`. O usuário clona o repositório uma vez na máquina e instala em modo editable com `pipx install -e <clone>`; o binário `agent-memory` no PATH lê código direto do clone, então `git pull` no clone atualiza a CLI imediatamente em todos os projetos consumidores. Templates, skills e o pre-commit hook ficam em `src/agent_memory/data/` e são acessados via `importlib.resources` (funciona em editable e wheel install). Esta arquitetura substitui o modelo v0.2.0 ("clonar para `.agent-memory/` dentro do projeto") e elimina a duplicação de scripts em cada projeto consumidor.

### Robustez de tratamento de erros

O `agent-memory propose-adr` ganhou validação prévia de base ref, com mensagens de erro acionáveis quando o repositório tem poucos commits para `HEAD~1` funcionar. O `agent-memory audit` ganhou mensagem acionável quando PyYAML está ausente, incluindo opções de instalação para diferentes ambientes (pip, pip3, virtualenv, --break-system-packages). Estas mudanças tornam o feedback de erro útil em vez de obscuro.

## Curto prazo

### Publicação na PyPI

Quando a CLI estabilizar (interface congelada por algumas releases sem mudança breaking), publicar o pacote na PyPI permitirá que usuários finais instalem com `pipx install agent-memory` em vez do clone-and-install editable atual. O caminho técnico é simples: `python -m build` para gerar wheel + sdist, `twine upload` para publicar; o trabalho real é (a) reservar o nome `agent-memory` na PyPI antes de qualquer concorrência, (b) decidir cadência de releases, e (c) configurar GitHub Actions para publicar automaticamente em cada tag `vX.Y.Z`.

### Integração com CI

Rodar `agent-memory audit --json --strict` em cada pull request, parsear o JSON e postar comentário no PR listando issues encontrados. Bloquear merge quando `violations_count > 0` ou `manifest_drift` não-vazio. A integração com GitHub Actions ou GitLab CI cabe em poucas linhas de YAML; o trabalho real é decidir os limiares de bloqueio. Com o pre-commit hook já implementado, a CI atua como segunda linha de defesa para casos onde o hook foi pulado ou não estava instalado.

### Comando de busca no Manifest

Um subcomando `agent-memory query` que responde perguntas comuns sem o agente precisar carregar arquivos. Exemplos: `agent-memory query depends-on F-0007` lista features que dependem de `F-0007`, `agent-memory query affected-by ADR-0002` lista features afetadas por uma decisão, `agent-memory query stale --days 90` lista features sem update há mais de noventa dias. Reduz o custo de retomada para perguntas frequentes.

### Linting de constraints hard

Hoje as restrições `severity: hard` em `AGENT.md` são apenas declarativas. A extensão é executar linters específicos para cada constraint registrada e reportar violações reais no código. Por exemplo, uma constraint "Pydantic obrigatório para schemas de borda" pode ser checada por um plugin de AST. Aumenta significativamente o valor das constraints, mas cada nova regra exige código de validação.

### Formalizar campo `version` em ADRs no schema da metodologia

A METHODOLOGY descreve `version` (semver da release que tocou) apenas para features no Manifest. Durante a gênese retroativa do próprio agent-memory (v0.3.0), introduzimos o mesmo campo no frontmatter dos ADRs para registrar em qual versão do projeto cada decisão foi aceita — útil para tabelas de overview e para correlacionar mudanças arquiteturais com releases. A extensão é propagar isso formalmente: documentar o campo na seção "Decisions" da METHODOLOGY, atualizar o schema validado pelo `agent-memory audit` para reconhecer (mas não exigir) o campo, e atualizar o template de ADR gerado pelo `agent-memory propose-adr`. Trabalho pequeno, mas precisa de coordenação entre doc, audit e propose-adr para evitar drift.

## Médio prazo

### Coordenação multi-agente

A versão atual assume sessão única em série. Quando duas sessões de Claude Code rodam em paralelo no mesmo repositório, há risco de conflito no `.agent-memory/STATE.md` e de duplicação de IDs em features novas. A proposta é um protocolo simples de lock: o agente cria um arquivo `.state.lock` com sua identidade ao iniciar uma sessão; outros agentes detectam o lock e operam em modo read-only no Manifest até o lock ser liberado. Para IDs novos, uma reserva atômica via Git push força resolução de conflito explícita.

### Coverage real ligado a pytest-cov

O campo `manifest_coverage` hoje mede apenas presença de arquivos de teste, não cobertura real de execução. A extensão é cruzar com a saída de `pytest --cov` (ou equivalente) e reportar cobertura real por feature. Uma feature pode ter arquivo de teste linkado mas com cobertura efetiva de quinze por cento, e o sistema atual não detecta isso. O trabalho é em parsear o relatório de coverage e mapear de volta para feature IDs via convenção de nomes ou marcadores no teste.

### Geração de OpenAPI a partir do Manifest

Para features de API, o campo `contracts.api` aponta para a função handler e `contracts.schemas` aponta para os schemas Pydantic. Com essa informação, é possível gerar a especificação OpenAPI automaticamente, garantindo que a documentação externa fique sempre alinhada com o Manifest interno. Útil principalmente em sistemas com SDK de cliente gerado a partir de OpenAPI, onde drift entre spec e implementação tem impacto direto em consumidores.

### Snapshot histórico do State

O `.agent-memory/STATE.md` é reescrito a cada sessão e a história fica no Git. Para análises retrospectivas — "qual era o foco do time em janeiro?", "quanto tempo passamos em F-0007?" — fazer `git log .agent-memory/STATE.md` é viável mas inconveniente. A proposta é um script que extrai snapshots semanais do `.agent-memory/STATE.md` e produz uma timeline navegável. Nada que não dê para fazer ad-hoc, mas a presença da ferramenta induz a hábito.

## Longo prazo

### Busca semântica sobre o Manifest

Em projetos com mais de cinquenta features, encontrar a feature relevante por nome ou tags vira difícil. Indexar os campos `name`, `user_value` e o corpo das features em embeddings permite busca por similaridade: "qual feature trata de autenticação?" retorna as três mais relevantes mesmo que nenhuma tenha "autenticação" no nome. O custo é manter o índice atualizado; em projetos pequenos não vale, em projetos grandes economiza muito tempo.

### Federação entre projetos

Em monorepos ou em organizações com múltiplos projetos relacionados, faz sentido linkar Manifests. Uma feature em `projeto-a` pode declarar `depends_on_external: projeto-b/F-0042`, e o `agent-memory audit` consulta o Manifest do projeto vizinho via Git submodule ou registry. Habilita raciocínio cross-cutting sobre dependências sem precisar duplicar informação.

### Versionamento de schema

A versão atual usa `schema_version: 2` em todos os artefatos. Quando o schema mudar (campos novos, formatos diferentes), precisamos de migration scripts que atualizem artefatos antigos preservando informação. A proposta é um diretório `src/agent_memory/migrations/` com scripts numerados, um para cada incremento de schema, expostos como `agent-memory migrate-schema --to N` (dry-run por padrão).

### Integração com feature flags

Quando `status: shipped` em produção é mediado por feature flags (LaunchDarkly, Unleash, Flagsmith), seria útil que o Manifest refletisse o estado real de exposição. Uma feature pode estar marcada como shipped mas com flag desligada para 95% dos usuários, e essa nuance importa para decisões operacionais. A integração é via adapter por provedor, lendo o estado da flag e anexando ao registro da feature.

### Análise de drift histórico

Manter `manifest_drift` é uma série temporal valiosa: pode-se medir quanto drift acumulou entre releases, quais features são mais propensas a drift, e correlacionar com regressões. A proposta é um job de CI que registra a métrica diariamente em uma tabela ou arquivo append-only, e um dashboard mínimo (HTML estático gerado por script) para visualização. Útil principalmente em times grandes onde refactors frequentes desafiam a manutenção do Manifest.

## Ideias avaliadas e rejeitadas

Algumas extensões parecem atraentes mas não passam o teste de custo-benefício, e vale documentar a rejeição para evitar reabrir a discussão.

A geração automática completa de ADRs a partir de diffs foi rejeitada porque ADRs são exatamente o tipo de conteúdo onde julgamento humano é insubstituível. A versão implementada de `agent-memory propose-adr` é deliberadamente parcial: ela detecta sinais e gera template, mas exige preenchimento humano (ou assistido por LLM em modo `--prompt`) para se tornar ADR de fato. Geração end-to-end totalmente automática produziria ADRs vazios e poluiria a memória arquitetural.

Migração automática silenciosa do Manifest a partir do código foi rejeitada pelo mesmo motivo da migração de ADRs: cristaliza interpretações erradas como verdades. O agente pode propor, o humano decide.

Webhooks que disparam em cada commit do State foram rejeitados por baixo retorno: a frequência seria alta, o sinal seria ruidoso, e o problema que resolveriam (notificar pessoas sobre mudanças) é melhor resolvido por hábito de leitura semanal do `git log .agent-memory/STATE.md` ou pelo dashboard de drift histórico.

Substituir os arquivos markdown por banco de dados foi avaliado e rejeitado. A simplicidade de markdown mais Git é o que torna a metodologia portável e auditável; mover para um banco perde a propriedade de "tudo está no repositório, versionado, sem dependência externa". Para projetos onde isso muda — federação entre dezenas de equipes, por exemplo — o item de federação acima é o caminho preferível, não substituição completa.
