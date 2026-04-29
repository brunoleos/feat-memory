# Melhorias futuras

Este documento cataloga extensões viáveis para a metodologia, organizadas por horizonte de implementação. Cada item descreve o problema que resolve, a forma proposta e os trade-offs envolvidos. A lista não é uma promessa de roadmap; é um inventário de ideias que a operação real do sistema vai eventualmente justificar ou descartar.

## Implementadas

Esta seção registra o que já saiu do plano e está disponível na metodologia. Os itens permanecem documentados para que a história de evolução da metodologia fique explícita, em vez de ser silenciosa.

### Notação EARS completa

Os critérios de aceitação no Manifest agora seguem os cinco padrões canônicos da Easy Approach to Requirements Syntax: ubiquitous, event, state, optional, unwanted, com um sexto padrão complex como escape para combinações. O `audit.py` valida que cada critério declara `pattern` e contém os campos obrigatórios para aquele padrão. Critérios mal-formados são erro de schema e bloqueiam o build.

### Pre-commit hook

O hook em `tools/hooks/pre-commit` é instalado por `tools/install-hooks.sh` e roda `audit.py --strict` antes de cada commit. A flag `--strict` foi adicionada ao `audit.py` para promover warnings (drift) a errors. O hook respeita `--no-verify` como válvula de escape para casos excepcionais. A combinação recomendada continua sendo hook local mais checagem em CI.

### Geração automática de propostas de ADR

A ferramenta `tools/propose-adr.py` examina o diff atual e detecta sinais de mudança arquitetural não-trivial: volume, dependências alteradas, mudanças em múltiplos diretórios, padrões linguísticos em mensagens de commit. Quando detecta sinais, gera um draft em `decisions/proposals/`, subpasta que o `audit.py` ignora explicitamente para preservar a invariante de imutabilidade dos ADRs reais. O modo `--prompt` emite um prompt estruturado para um agente LLM em vez do template direto, separando detecção determinística de redação que exige julgamento.

### Portabilidade total via Python

Todas as ferramentas e scripts do pacote estão escritos em Python 3.10 ou superior, sem dependência de shell scripts. O `deploy.py` substitui o antigo `deploy.sh`, o `install_hooks.py` substitui o `install-hooks.sh`, e o pre-commit hook foi reescrito como script Python executável. A única dependência externa é PyYAML, que o `audit.py` reporta com mensagem acionável quando ausente. O pacote roda em Linux, macOS e Windows nativamente.

### Versionamento semântico e changelog

O pacote tem versionamento semântico em arquivo `VERSION` na raiz e histórico em `CHANGELOG.md` seguindo o formato Keep a Changelog. O `deploy.py` registra a versão instalada em `.agent-memory/.installed-version` no momento da instalação, permitindo que cada projeto consumidor saiba qual versão está em uso. Esta peça habilita o sistema de updates documentado no item seguinte.

### Sistema de updates com upstream configurável

O `update.py` permite que projetos consumidores recebam atualizações da metodologia ao longo do tempo sem perder customizações locais. O upstream é configurado em `.agent-memory/.upstream` apontando para um repositório Git, uma referência específica desse repositório, ou um caminho local. O update baixa o conteúdo upstream, substitui o pacote preservando arquivos de configuração local, e re-roda o deploy com a lógica de merge para propagar mudanças aos artefatos do projeto sem perder customizações do `AGENT.md` ou do `CLAUDE.md`. Esta abordagem permite que o `agent-memory` seja desenvolvido como repositório upstream único e replicado em vários projetos consumidores via comando explícito.

### Robustez de tratamento de erros

O `propose-adr.py` ganhou validação prévia de base ref, com mensagens de erro acionáveis quando o repositório tem poucos commits para `HEAD~1` funcionar. O `audit.py` ganhou mensagem acionável quando PyYAML está ausente, incluindo opções de instalação para diferentes ambientes (pip, pip3, virtualenv, --break-system-packages). Estas mudanças tornam o feedback de erro útil em vez de obscuro.

## Curto prazo

### Integração com CI

Rodar `python tools/audit.py --json --strict` em cada pull request, parsear o JSON e postar comentário no PR listando issues encontrados. Bloquear merge quando `violations_count > 0` ou `manifest_drift` não-vazio. A integração com GitHub Actions ou GitLab CI cabe em poucas linhas de YAML; o trabalho real é decidir os limiares de bloqueio. Com o pre-commit hook já implementado, a CI atua como segunda linha de defesa para casos onde o hook foi pulado ou não estava instalado.

### Comando de busca no Manifest

Uma CLI auxiliar `tools/query.py` que responde perguntas comuns sem o agente precisar carregar arquivos. Exemplos: `query.py depends-on F-0007` lista features que dependem de `F-0007`, `query.py affected-by ADR-0002` lista features afetadas por uma decisão, `query.py stale --days 90` lista features sem update há mais de noventa dias. Reduz o custo de retomada para perguntas frequentes.

### Linting de constraints hard

Hoje as restrições `severity: hard` em `AGENT.md` são apenas declarativas. A extensão é executar linters específicos para cada constraint registrada e reportar violações reais no código. Por exemplo, uma constraint "Pydantic obrigatório para schemas de borda" pode ser checada por um plugin de AST. Aumenta significativamente o valor das constraints, mas cada nova regra exige código de validação.

## Médio prazo

### Coordenação multi-agente

A versão atual assume sessão única em série. Quando duas sessões de Claude Code rodam em paralelo no mesmo repositório, há risco de conflito no `STATE.md` e de duplicação de IDs em features novas. A proposta é um protocolo simples de lock: o agente cria um arquivo `.state.lock` com sua identidade ao iniciar uma sessão; outros agentes detectam o lock e operam em modo read-only no Manifest até o lock ser liberado. Para IDs novos, uma reserva atômica via Git push força resolução de conflito explícita.

### Coverage real ligado a pytest-cov

O campo `manifest_coverage` hoje mede apenas presença de arquivos de teste, não cobertura real de execução. A extensão é cruzar com a saída de `pytest --cov` (ou equivalente) e reportar cobertura real por feature. Uma feature pode ter arquivo de teste linkado mas com cobertura efetiva de quinze por cento, e o sistema atual não detecta isso. O trabalho é em parsear o relatório de coverage e mapear de volta para feature IDs via convenção de nomes ou marcadores no teste.

### Geração de OpenAPI a partir do Manifest

Para features de API, o campo `contracts.api` aponta para a função handler e `contracts.schemas` aponta para os schemas Pydantic. Com essa informação, é possível gerar a especificação OpenAPI automaticamente, garantindo que a documentação externa fique sempre alinhada com o Manifest interno. Útil principalmente em sistemas com SDK de cliente gerado a partir de OpenAPI, onde drift entre spec e implementação tem impacto direto em consumidores.

### Snapshot histórico do State

O `STATE.md` é reescrito a cada sessão e a história fica no Git. Para análises retrospectivas — "qual era o foco do time em janeiro?", "quanto tempo passamos em F-0007?" — fazer `git log STATE.md` é viável mas inconveniente. A proposta é um script que extrai snapshots semanais do `STATE.md` e produz uma timeline navegável. Nada que não dê para fazer ad-hoc, mas a presença da ferramenta induz a hábito.

## Longo prazo

### Busca semântica sobre o Manifest

Em projetos com mais de cinquenta features, encontrar a feature relevante por nome ou tags vira difícil. Indexar os campos `name`, `user_value` e o corpo das features em embeddings permite busca por similaridade: "qual feature trata de autenticação?" retorna as três mais relevantes mesmo que nenhuma tenha "autenticação" no nome. O custo é manter o índice atualizado; em projetos pequenos não vale, em projetos grandes economiza muito tempo.

### Federação entre projetos

Em monorepos ou em organizações com múltiplos projetos relacionados, faz sentido linkar Manifests. Uma feature em `projeto-a` pode declarar `depends_on_external: projeto-b/F-0042`, e o `audit.py` consulta o Manifest do projeto vizinho via Git submodule ou registry. Habilita raciocínio cross-cutting sobre dependências sem precisar duplicar informação.

### Versionamento de schema

A versão atual usa `schema_version: 2` em todos os artefatos. Quando o schema mudar (campos novos, formatos diferentes), precisamos de migration scripts que atualizem artefatos antigos preservando informação. A proposta é um diretório `tools/migrations/` com scripts numerados, um para cada incremento de schema, executáveis tanto em modo dry-run quanto aplicado.

### Integração com feature flags

Quando `status: shipped` em produção é mediado por feature flags (LaunchDarkly, Unleash, Flagsmith), seria útil que o Manifest refletisse o estado real de exposição. Uma feature pode estar marcada como shipped mas com flag desligada para 95% dos usuários, e essa nuance importa para decisões operacionais. A integração é via adapter por provedor, lendo o estado da flag e anexando ao registro da feature.

### Análise de drift histórico

Manter `manifest_drift` é uma série temporal valiosa: pode-se medir quanto drift acumulou entre releases, quais features são mais propensas a drift, e correlacionar com regressões. A proposta é um job de CI que registra a métrica diariamente em uma tabela ou arquivo append-only, e um dashboard mínimo (HTML estático gerado por script) para visualização. Útil principalmente em times grandes onde refactors frequentes desafiam a manutenção do Manifest.

## Ideias avaliadas e rejeitadas

Algumas extensões parecem atraentes mas não passam o teste de custo-benefício, e vale documentar a rejeição para evitar reabrir a discussão.

A geração automática completa de ADRs a partir de diffs foi rejeitada porque ADRs são exatamente o tipo de conteúdo onde julgamento humano é insubstituível. A versão implementada de `propose-adr.py` é deliberadamente parcial: ela detecta sinais e gera template, mas exige preenchimento humano (ou assistido por LLM em modo `--prompt`) para se tornar ADR de fato. Geração end-to-end totalmente automática produziria ADRs vazios e poluiria a memória arquitetural.

Migração automática silenciosa do Manifest a partir do código foi rejeitada pelo mesmo motivo da migração de ADRs: cristaliza interpretações erradas como verdades. O agente pode propor, o humano decide.

Webhooks que disparam em cada commit do State foram rejeitados por baixo retorno: a frequência seria alta, o sinal seria ruidoso, e o problema que resolveriam (notificar pessoas sobre mudanças) é melhor resolvido por hábito de leitura semanal do `git log STATE.md` ou pelo dashboard de drift histórico.

Substituir os arquivos markdown por banco de dados foi avaliado e rejeitado. A simplicidade de markdown mais Git é o que torna a metodologia portável e auditável; mover para um banco perde a propriedade de "tudo está no repositório, versionado, sem dependência externa". Para projetos onde isso muda — federação entre dezenas de equipes, por exemplo — o item de federação acima é o caminho preferível, não substituição completa.
