---
id: F-0018
name: consumer-version-notice
status: in_progress
introduced: 2026-05-05
version: 0.7.0
user_value: >
  Notifica o consumidor (soft) quando a versão do CLI instalada via pipx
  difere da versão registrada em `.meta.yaml::version`. Fecha o loop de
  feedback que F-0010 (`.meta.yaml::version`) e F-0016 (VERSION-bump-on-code)
  abriram: agora "consumer está desatualizado" é um sinal observável,
  não algo que se descobre tarde quando uma skill faz algo inesperado.
  Time pequeno com vários agentes recebe a notificação coletivamente
  na próxima vez que cada um roda `agent-memory audit`.
contracts:
  api:
    - src/agent_memory/governance/version_check.py::consumer_version_notice
    - src/agent_memory/governance/version_check.py::run
    - src/agent_memory/governance/audit.py::run
  tests:
    - tests/test_version_check.py
acceptance:
  - id: A1
    pattern: state
    state: "`.meta.yaml::version` difere de `agent_memory.__version__`"
    response: >
      `consumer_version_notice(root)` retorna texto contendo ambas as
      versões e a sugestão de re-rodar `agent-memory deploy .`;
      `agent-memory audit` imprime esse texto na stderr após o relatório,
      sem alterar exit code
  - id: A2
    pattern: state
    state: "`.meta.yaml::version` é igual a `__version__`"
    response: >
      `consumer_version_notice(root)` retorna `None`; audit não emite
      nenhuma linha extra
  - id: A3
    pattern: unwanted
    trigger: "`.agent-memory/.meta.yaml` não existe (consumidor pré-v0.6)"
    response: >
      `consumer_version_notice(root)` retorna `None`; sem dados, não há
      como avaliar diff — fail-soft
  - id: A4
    pattern: state
    state: "`.meta.yaml::version_check_enabled: false`"
    response: >
      `consumer_version_notice(root)` retorna `None`; usuário desabilitou
      explicitamente o sinal (coerente com `telemetry_enabled` de F-0014)
  - id: A5
    pattern: event
    trigger: "`agent-memory version-check` é invocado"
    response: >
      imprime o notice (ou "atualizado: vX.Y.Z") na stderr/stdout,
      sai com 0; subcomando standalone para CI/scripts que querem
      o sinal sem rodar audit completo
  - id: A6
    pattern: ubiquitous
    requirement: >
      o exit code de `agent-memory audit` NUNCA é alterado por esta
      feature — soft sempre, ADR-0008 fail-open preservado para
      o sinal de notificação
depends_on: [F-0010, F-0017]
decisions: [ADR-0022]
---

# F-0018 · consumer-version-notice

## Comportamento

Notifica o consumidor quando a versão do CLI instalada via pipx difere da versão registrada em `.agent-memory/.meta.yaml::version`. **Soft sempre** — não bloqueia, não muda exit code; apenas informa.

**Função core.** `consumer_version_notice(root: Path) -> str | None` em [src/agent_memory/governance/version_check.py](src/agent_memory/governance/version_check.py):

- Lê `.meta.yaml` via `shared.parsing.read_meta()`.
- Compara `meta.get("version")` com `agent_memory.__version__`.
- Retorna texto do notice se diferentes; `None` em qualquer outro caso (iguais, .meta ausente, version_check_enabled=false).

**Integração no audit.** [governance.audit::run()](src/agent_memory/governance/audit.py) chama `consumer_version_notice` após `print_report()`. Se houver notice, imprime na stderr (cor amarela com `isatty`, plain em CI). Exit code do audit NÃO é afetado — soft, ADR-0008.

**Subcomando standalone.** `agent-memory version-check` invoca `consumer_version_notice` direto. Útil em CI ou scripts que querem só esse sinal. Sai com 0 sempre.

**Disable.** `.agent-memory/.meta.yaml::version_check_enabled: false` desliga o notice. Default `true`. Schema do `.meta.yaml` ganha campo opcional, retro-compatível (leitores antigos ignoram).

ADR-0022 explica a política: notice em qualquer diff (sem distinção semver na primeira versão), soft sempre (atualizar não é obrigatório), integrado em audit (lugar natural — usuário já está olhando o estado), subcomando dedicado para CI.
