"""indexing.py — Geração dos arquivos INDEX.md a partir do manifest e decisions.

Três índices: manifest principal (features ativas), manifest archive
(features arquivadas, F-0012), decisions. Mesmo formato de tabela
markdown, regenerado a cada `agent-memory audit` ou após `archive --apply`.

Parte de `memory/`. Importa apenas de stdlib. Usado por
`governance.audit` (no fim do `run_audit`) e por `memory.archive`
(no fim do `archive --apply`) — esta segunda é o motivo de viver
em memory: archive não pode importar governance.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


def _gerado_em() -> str:
    return (
        f"_Gerado por `agent-memory audit` em "
        f"{datetime.now(timezone.utc).isoformat(timespec='seconds')}. "
        f"Não edite manualmente._"
    )


def gen_manifest_index(features: list[dict]) -> str:
    rows = [
        "# Índice de features", "",
        "| ID | Nome | Status | Versão | ADRs | Depende |",
        "|---|---|---|---|---|---|",
    ]
    for f in sorted(features, key=lambda x: str(x.get("id", ""))):
        rows.append(
            f"| {f.get('id', '?')} "
            f"| {f.get('name', '?')} "
            f"| {f.get('status', '?')} "
            f"| {f.get('version', '—')} "
            f"| {','.join(f.get('decisions') or []) or '—'} "
            f"| {','.join(f.get('depends_on') or []) or '—'} |"
        )
    rows += ["", _gerado_em()]
    return "\n".join(rows) + "\n"


def gen_archive_index(features: list[dict]) -> str:
    """Mesma estrutura de gen_manifest_index, mas para features arquivadas.

    Existência separada (em manifest/archive/INDEX.md) reduz o tamanho
    do INDEX principal carregado por `memory-bootstrap`. F-0012, ADR-0015.
    """
    rows = [
        "# Índice de features arquivadas", "",
        "Features `shipped` e fora de `STATE.md::active_features` movidas",
        "por `agent-memory archive --apply`. IDs continuam resolvíveis pelo",
        "cross-check; mantenha aqui o registro histórico, sem onerar o INDEX",
        "principal.", "",
        "| ID | Nome | Status | Versão | ADRs | Depende |",
        "|---|---|---|---|---|---|",
    ]
    for f in sorted(features, key=lambda x: str(x.get("id", ""))):
        rows.append(
            f"| {f.get('id', '?')} "
            f"| {f.get('name', '?')} "
            f"| {f.get('status', '?')} "
            f"| {f.get('version', '—')} "
            f"| {','.join(f.get('decisions') or []) or '—'} "
            f"| {','.join(f.get('depends_on') or []) or '—'} |"
        )
    rows += ["", _gerado_em()]
    return "\n".join(rows) + "\n"


def gen_decisions_index(decisions: list[dict]) -> str:
    rows = [
        "# Índice de decisões", "",
        "| ID | Data | Status | Tags | Afeta |",
        "|---|---|---|---|---|",
    ]
    for d in sorted(decisions, key=lambda x: str(x.get("id", ""))):
        rows.append(
            f"| {d.get('id', '?')} "
            f"| {d.get('date', '?')} "
            f"| {d.get('status', '?')} "
            f"| {','.join(d.get('tags') or []) or '—'} "
            f"| {','.join(d.get('affects_features') or []) or '—'} |"
        )
    rows += ["", _gerado_em()]
    return "\n".join(rows) + "\n"


def regenerate_all_indexes(manifest_dir: Path,
                           archive_dir: Path,
                           decisions_dir: Path,
                           features: list[dict],
                           archived_features: list[dict],
                           decisions: list[dict]) -> None:
    """Escreve os três INDEX.md no filesystem.

    Memory.archive chama esta função após mover arquivos sem precisar
    invocar governance.audit.run_audit (quebra a dependência reversa
    descrita em ADR-0021).
    """
    if manifest_dir.exists():
        (manifest_dir / "INDEX.md").write_text(
            gen_manifest_index(features), encoding="utf-8"
        )
        if archived_features:
            archive_dir.mkdir(parents=True, exist_ok=True)
            (archive_dir / "INDEX.md").write_text(
                gen_archive_index(archived_features), encoding="utf-8"
            )
    if decisions_dir.exists():
        (decisions_dir / "INDEX.md").write_text(
            gen_decisions_index(decisions), encoding="utf-8"
        )
