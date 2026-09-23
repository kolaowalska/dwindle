from __future__ import annotations

import sys

import pytest

from src.domain.common.plugin_discovery import discover_modules, load_plugin_file


@pytest.fixture
def drop_plugin_modules():
    before = set(sys.modules)
    yield
    for name in set(sys.modules) - before:
        if name.startswith("dwindle_plugin_"):
            sys.modules.pop(name, None)


def test_unimportable_module_does_not_stop_discovery(tmp_path, monkeypatch):
    pkg = tmp_path / "fakepkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "good.py").write_text("VALUE = 1\n")
    (pkg / "broken.py").write_text("raise RuntimeError('unimportable')\n")
    monkeypatch.syspath_prepend(str(tmp_path))

    names = [m.__name__ for m in discover_modules("fakepkg")]
    assert "fakepkg.good" in names
    assert "fakepkg.broken" not in names

def test_plugin_directory_is_appended_not_prepended(tmp_path, drop_plugin_modules):
    import random as stdlib_random

    plugin = tmp_path / "random.py"
    plugin.write_text("MARKER = 'from plugin'\n")

    module = load_plugin_file(plugin)
    assert module.MARKER == "from plugin"
    assert sys.path[0] != str(tmp_path)
    assert str(tmp_path) in sys.path
    assert sys.modules["random"] is stdlib_random

def test_plugin_is_registered_under_a_namespaced_name(tmp_path, drop_plugin_modules):
    plugin = tmp_path / "myalgo.py"
    plugin.write_text("MARKER = 1\n")
    load_plugin_file(plugin)
    assert "dwindle_plugin_myalgo" in sys.modules

def test_failed_plugin_leaves_no_partial_module(tmp_path, drop_plugin_modules):
    plugin = tmp_path / "boom.py"
    plugin.write_text("raise RuntimeError('bad plugin')\n")
    with pytest.raises(RuntimeError):
        load_plugin_file(plugin)
    assert "boom" not in sys.modules
    assert "dwindle_plugin_boom" not in sys.modules

def test_missing_plugin_raises_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_plugin_file(tmp_path / "nope.py")
