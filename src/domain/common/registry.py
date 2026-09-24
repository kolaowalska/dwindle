from __future__ import annotations

from typing import Callable, Dict, Generic, Iterable, List, Tuple, Type, TypeVar

from src.domain.common.plugin_discovery import discover_modules

T = TypeVar("T")


class Registry(Generic[T]):
    """
    [REGISTRY] maps a string key to a plugin class, populated by decorators
    at import time and backed by package scanning.
    """

    def __init__(self, kind: str, package: str):
        self.kind = kind
        self.package = package
        self._items: Dict[str, Type[T]] = {}
        self._discovered = False

    def register(self, name: str) -> Callable[[Type[T]], Type[T]]:
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"{self.kind} name must be a non-empty string!!")

        key = name.strip()

        def _decorator(cls: Type[T]) -> Type[T]:
            if key in self._items and self._items[key] is not cls:
                raise ValueError(f"{self.kind} '{key}' already registered by {self._items[key].__name__}")
            self._items[key] = cls
            return cls

        return _decorator

    def discover(self) -> None:
        if self._discovered:
            return
        discover_modules(self.package)
        self._discovered = True

    def ensure_discovered(self) -> None:
        if not self._discovered:
            self.discover()

    def get(self, name: str) -> T:
        self.ensure_discovered()
        key = name.strip()
        try:
            cls = self._items[key]
        except KeyError as e:
            available = ", ".join(sorted(self._items))
            raise KeyError(f"unknown {self.kind} '{key}'. available: [{available}]") from e
        return cls()

    def list(self) -> List[str]:
        self.ensure_discovered()
        return sorted(self._items)

    def items(self) -> Iterable[Tuple[str, Type[T]]]:
        self.ensure_discovered()
        return self._items.items()
