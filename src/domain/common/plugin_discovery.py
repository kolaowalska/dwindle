from __future__ import annotations

import importlib
import importlib.util
import logging
import pkgutil
import sys
from pathlib import Path
from types import ModuleType

log = logging.getLogger(__name__)

_PLUGIN_PREFIX = "dwindle_plugin_"


def load_plugin_file(path: str | Path) -> ModuleType:
    resolved = Path(path).resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"plugin not found: {resolved}")

    parent = str(resolved.parent)
    if parent not in sys.path:
        sys.path.append(parent)

    module_name = f"{_PLUGIN_PREFIX}{resolved.stem}"
    spec = importlib.util.spec_from_file_location(module_name, resolved)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load plugin: {resolved}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(module_name, None)
        raise

    return module


def discover_modules(package_name: str) -> list[ModuleType]:
    pkg = importlib.import_module(package_name)

    if not hasattr(pkg, "__path__"):
        return [pkg]

    imported: list[ModuleType] = []
    for m in pkgutil.iter_modules(pkg.__path__, pkg.__name__ + "."):
        try:
            imported.append(importlib.import_module(m.name))
        except Exception as e:
            log.warning(f"skipping '{m.name}': {type(e).__name__}: {e}")
    return imported
