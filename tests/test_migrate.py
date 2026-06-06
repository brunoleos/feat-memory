"""Testes da detecção de entrypoints do `feat-memory migrate` (ADR-0030).

Foco: a varredura é agnóstica de linguagem. O `detect_entry_points` antigo só
olhava `*.py`, então retornava vazio em projetos JS/TS/Go e o agente perdia o
sinal de por onde começar a leitura code-first.
"""

from __future__ import annotations

from pathlib import Path

from feat_memory.memory import migrate


def _touch(root: Path, rel: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("// source\n", encoding="utf-8")


def test_detect_entry_points_is_language_agnostic(tmp_path):
    """Projeto JS com src/routes/ e src/cli/ é detectado (não só Python)."""
    _touch(tmp_path, "src/routes/home.js")
    _touch(tmp_path, "src/routes/about.ts")
    _touch(tmp_path, "src/cli/main.mjs")
    _touch(tmp_path, "src/util/helpers.js")  # não é entrypoint dir

    out = migrate.detect_entry_points(tmp_path)
    joined = "\n".join(out)

    assert "routes/" in joined
    assert "cli/" in joined
    # 2 arquivos de fonte em routes/
    assert any("routes/: 2" in line for line in out)


def test_detect_entry_points_prunes_vendored_dirs(tmp_path):
    """node_modules e afins não inflam a contagem."""
    _touch(tmp_path, "node_modules/pkg/routes/x.js")
    _touch(tmp_path, "dist/api/bundle.js")
    _touch(tmp_path, "src/api/real.js")

    out = migrate.detect_entry_points(tmp_path)

    assert any("api/: 1" in line for line in out), out
    assert not any("routes/" in line for line in out)


def test_detect_entry_points_empty_when_no_convention(tmp_path):
    """Sem diretórios de convenção, retorna lista vazia (sem ruído)."""
    _touch(tmp_path, "src/lib/core.js")
    assert migrate.detect_entry_points(tmp_path) == []


def test_detect_test_signals_by_dir_and_by_name(tmp_path):
    """Testes são detectados por diretório de convenção e por padrão de nome."""
    _touch(tmp_path, "tests/test_login.py")
    _touch(tmp_path, "e2e/checkout.spec.ts")
    _touch(tmp_path, "src/auth.test.js")  # fora de dir de teste, por nome
    _touch(tmp_path, "src/auth.js")        # não é teste

    out = migrate.detect_test_signals(tmp_path)
    joined = "\n".join(out)

    assert any("tests:" in line for line in out)
    assert any("e2e:" in line for line in out)
    assert "test_*/*.spec" in joined  # auth.test.js casado por nome


def test_detect_test_signals_prunes_vendored(tmp_path):
    """Testes dentro de node_modules não contam."""
    _touch(tmp_path, "node_modules/lib/test_x.py")
    _touch(tmp_path, "tests/test_real.py")

    out = migrate.detect_test_signals(tmp_path)
    assert any("tests: 1" in line for line in out), out


def test_detect_ui_signals_dirs_and_extensions(tmp_path):
    """UI detectada por diretório de view e por extensão de arquivo de tela."""
    _touch(tmp_path, "src/pages/Home.jsx")
    _touch(tmp_path, "src/views/Login.vue")
    _touch(tmp_path, "public/index.html")

    out = migrate.detect_ui_signals(tmp_path)
    joined = "\n".join(out)

    assert "pages/" in joined
    assert "views/" in joined
    assert "arquivos de view:" in joined  # .vue/.jsx/.html somados


def test_detect_ui_signals_empty_for_backend_only(tmp_path):
    """Projeto sem camada de UI não gera sinal de tela."""
    _touch(tmp_path, "src/api/users.py")
    assert migrate.detect_ui_signals(tmp_path) == []
