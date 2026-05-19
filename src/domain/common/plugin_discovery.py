from __future__ import annotations

import importlib
import importlib.util
import pkgutil
import sys
from pathlib import Path
from types import ModuleType


def load_plugin_file(path: str | Path) -> ModuleType:
    resolved = Path(path).resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"plugin not found: {resolved}")

    parent = str(resolved.parent)
    if parent not in sys.path:
        sys.path.insert(0, parent)

    module_name = resolved.stem
    spec = importlib.util.spec_from_file_location(module_name, resolved)
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(module_name, module)
    spec.loader.exec_module(module)
    return module


def discover_modules(package_name: str) -> list[ModuleType]:
    pkg = importlib.import_module(package_name)

    if not hasattr(pkg, "__path__"):
        return [pkg]

    imported: list[ModuleType] = []
    for m in pkgutil.iter_modules(pkg.__path__, pkg.__name__ + "."):
        imported.append(importlib.import_module(m.name))
    return imported
