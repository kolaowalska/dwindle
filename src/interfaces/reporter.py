from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# ── formatting constants ──────────────────────────────────────────────────────

COL_WIDTH = 20
ROW_LABEL_WIDTH = 32

_METRIC_ABBREV = {
    "diameter":                 "diameter",
    "average path length":      "avg-path",
    "degree distribution":      "deg-dist",
    "connectivity":             "connect",
    "global efficiency":        "glob-eff",
    "clustering":               "cluster",
    "community preservation":   "community",
    "effective resistance":     "eff-res",
    "degree assortativity":     "assort",
    "spectral similarity":      "spectral",
    "diameter delta":               "diameter",
    "average path length delta":    "avg-path",
    "degree distribution delta":    "deg-dist",
    "connectivity delta":           "connect",
    "global efficiency delta":      "glob-eff",
    "clustering delta":             "cluster",
    "community preservation delta": "community",
    "effective resistance delta":   "eff-res",
    "degree assortativity delta":   "assort",
}

_KEY_ABBREV = {
    "diameter":                     "diam",
    "component_nodes":              "cc-n",
    "total_nodes":                  "tot-n",
    "avg":                          "avg",
    "weighted":                     "wtd",
    "max_degree":                   "max-deg",
    "min_degree":                   "min-deg",
    "unique_degrees":               "uniq-deg",
    "n_components":                 "n-comp",
    "largest_component_ratio":      "lcc-ratio",
    "fiedler":                      "fiedler",
    "avg_clustering":               "avg-clust",
    "transitivity":                 "transit",
    "modularity":                   "modular",
    "n_communities":                "n-comm",
    "kirchhoff_index":              "kirchhoff",
    "density":                      "density",
    "assortativity":                "assort",
    "relative_l2_error":            "l2-err",
    "fiedler_G":                    "fiedler-G",
    "fiedler_H":                    "fiedler-H",
    "fiedler_ratio":                "fiedl-ratio",
    "k":                            "k",
    "diameter_delta":               "diam Δ",
    "diameter_original":            "diam orig",
    "diameter_reduced":             "diam redu",
    "fiedler_delta":                "fiedler Δ",
    "fiedler_original":             "fiedler orig",
    "fiedler_reduced":              "fiedler redu",
    "avg_delta":                    "avg Δ",
    "avg_original":                 "avg orig",
    "avg_reduced":                  "avg redu",
    "modularity_delta":             "modul Δ",
    "modularity_original":          "modul orig",
    "modularity_reduced":           "modul redu",
    "n_communities_delta":          "n-comm Δ",
    "n_communities_original":       "n-comm orig",
    "n_communities_reduced":        "n-comm redu",
    "n_components_delta":           "n-comp Δ",
    "n_components_original":        "n-comp orig",
    "n_components_reduced":         "n-comp redu",
    "largest_component_ratio_delta":    "lcc-ratio Δ",
    "largest_component_ratio_original": "lcc-ratio orig",
    "largest_component_ratio_reduced":  "lcc-ratio redu",
    "avg_clustering_delta":         "avg-clust Δ",
    "avg_clustering_original":      "avg-clust orig",
    "avg_clustering_reduced":       "avg-clust redu",
    "transitivity_delta":           "transit Δ",
    "transitivity_original":        "transit orig",
    "transitivity_reduced":         "transit redu",
    "max_degree_delta":             "max-deg Δ",
    "max_degree_original":          "max-deg orig",
    "max_degree_reduced":           "max-deg redu",
    "min_degree_delta":             "min-deg Δ",
    "min_degree_original":          "min-deg orig",
    "min_degree_reduced":           "min-deg redu",
    "unique_degrees_delta":         "uniq-deg Δ",
    "unique_degrees_original":      "uniq-deg orig",
    "unique_degrees_reduced":       "uniq-deg redu",
}


def _abbrev_algo(label: str, algorithm: str, registry_get) -> str:
    """
    Try to get the abbrev from the sparsifier's INFO.
    Falls back to the label string if the registry call fails.
    """
    try:
        transform = registry_get(algorithm)
        abbrev = transform.INFO.abbrev
        # import re
        # match = re.search(r"\((.*?)\)", label)
        # hint = match.group(1).replace("rho=", "ρ=") if match else ""
        # return f"{abbrev} {hint}".strip()
        return f"{abbrev}".strip()
    except Exception:
        return label[:COL_WIDTH - 1]


def _abbrev_row(metric_name: str, key: str) -> str:
    m = _METRIC_ABBREV.get(metric_name, metric_name[:10])
    k = _KEY_ABBREV.get(key, key[:10])
    return f"{m} / {k}"

_RESET  = "\033[0m"
_BOLD   = "\033[1m"
_DIM    = "\033[2m"
_RED    = "\033[91m"
_GREEN  = "\033[92m"
_YELLOW = "\033[93m"
_CYAN   = "\033[96m"
_WHITE  = "\033[97m"


def _c(text: str, *codes: str) -> str:
    return "".join(codes) + str(text) + _RESET

# ── data model ────────────────────────────────────────────────────────────────

@dataclass
class ScenarioRecord:
    """all results for one sparsifier run, collected during demo execution"""
    label: str
    algorithm: str
    nodes_before: int
    edges_before: int
    nodes_after: int
    edges_after: int
    metrics: dict[str, dict[str, Any]]
    deltas: dict[str, dict[str, Any]]
    error: str | None = None


@dataclass
class Reporter:
    records: list[ScenarioRecord] = field(default_factory=list)

    def add(self, record: ScenarioRecord) -> None:
        self.records.append(record)

    def print_report(self) -> None:
        from src.domain.sparsifiers.registry import SparsifierRegistry
        from src.domain.transforms.registry import TransformRegistry

        def resolve(label: str, algo: str) -> str:
            for registry in (SparsifierRegistry, TransformRegistry):
                try:
                    transform = registry.get(algo)
                    abbrev = transform.INFO.abbrev
                    # import re
                    # match = re.search(r"\((.*?)\)", label)
                    # hint = match.group(1).replace("rho=", "ρ=") if match else ""
                    # return f"{abbrev} {hint}".strip()
                    return f"{abbrev}".strip()
                except Exception:
                    continue
            return label[:COL_WIDTH - 1]

        columns = [(r.label, r.algorithm) for r in self.records]
        _print_header("EXPERIMENT REPORT")
        _print_topology_table(self.records, columns, resolve)
        _print_metrics_table(self.records, columns, resolve)
        _print_deltas_table(self.records, columns, resolve)


# ── table helpers ─────────────────────────────────────────────────────────────

def _print_header(title: str) -> None:
    width = 135
    print()
    print(_c("═" * width, _CYAN))
    print(_c(f"  {title}", _BOLD, _CYAN))
    print(_c("═" * width, _CYAN))


def _print_section(title: str) -> None:
    print()
    print(_c(f"  {title}", _BOLD, _WHITE))
    print(_c("  " + "─" * 132, _DIM))


def _fmt(v: Any, is_delta: bool = False) -> str:
    """format a single cell value, colouring deltas red/green"""
    if isinstance(v, float):
        s = f"{v:+.4f}" if is_delta else f"{v:.4f}"
    elif isinstance(v, int):
        s = f"{v:+d}" if is_delta else str(v)
    elif isinstance(v, bool):
        s = str(v)
    else:
        s = str(v)

    if is_delta:
        if isinstance(v, (int, float)):
            if v > 0:
                return _c(s, _GREEN)
            elif v < 0:
                return _c(s, _RED)
    return s


def _print_table(
    rows: list[str],
    columns: list[str],
    cells: list[list[str]],
) -> None:
    col_w = COL_WIDTH
    row_w = ROW_LABEL_WIDTH

    header = _c(f"  {'metric':<{row_w}}", _DIM)
    for col in columns:
        label = col[:col_w - 1]
        header += _c(f"{label:>{col_w}}", _BOLD)
    print(header)
    print(_c("  " + "─" * (row_w + col_w * len(columns)), _DIM))

    for row_label, row_cells in zip(rows, cells):
        line = _c(f"  {row_label:<{row_w}}", _DIM)
        for cell in row_cells:
            visible = len(_strip_ansi(cell))
            line += " " * max(col_w - visible, 1) + cell
        print(line)


def _strip_ansi(s: str) -> str:
    import re
    return re.sub(r"\033\[[0-9;]*m", "", s)


# ── topology table ────────────────────────────────────────────────────────────

def _print_topology_table(
    records: list[ScenarioRecord],
    columns: list[tuple[str, str]],
    resolve: callable,
) -> None:
    _print_section("TOPOLOGY")
    col_headers = [resolve(label, algo) for label, algo in columns]
    rows = ["nodes before", "nodes after", "Δ nodes",
            "edges before", "edges after", "Δ edges", "edge retention"]
    cells = []
    for row in rows:
        row_cells = []
        for r in records:
            if row == "nodes before": row_cells.append(_fmt(r.nodes_before))
            elif row == "nodes after": row_cells.append(_fmt(r.nodes_after))
            elif row == "Δ nodes": row_cells.append(_fmt(r.nodes_after - r.nodes_before, is_delta=True))
            elif row == "edges before": row_cells.append(_fmt(r.edges_before))
            elif row == "edges after": row_cells.append(_fmt(r.edges_after))
            elif row == "Δ edges": row_cells.append(_fmt(r.edges_after - r.edges_before, is_delta=True))
            elif row == "edge retention":
                ratio = r.edges_after / r.edges_before if r.edges_before > 0 else 0.0
                row_cells.append(_fmt(ratio))
        cells.append(row_cells)
    _print_table(rows, col_headers, cells)


# ── absolute metrics table ────────────────────────────────────────────────────

def _print_metrics_table(
    records: list[ScenarioRecord],
    columns: list[tuple[str, str]],
    resolve: callable,
) -> None:
    _print_section("METRICS ON SPARSIFIED GRAPH (H)")
    col_headers = [resolve(label, algo) for label, algo in columns]
    metric_keys: list[tuple[str, str]] = []
    seen: set = set()
    for r in records:
        for metric_name, summary in r.metrics.items():
            if metric_name in ("spectral_similarity", "spectral similarity"):
                continue
            for key in summary:
                if key == "execution_time":
                    continue
                pair = (metric_name, key)
                if pair not in seen:
                    metric_keys.append(pair)
                    seen.add(pair)
    rows = [_abbrev_row(m, k) for m, k in metric_keys]
    cells = []
    for metric_name, key in metric_keys:
        row_cells = []
        for r in records:
            val = r.metrics.get(metric_name, {}).get(key, "—")
            row_cells.append(_fmt(val))
        cells.append(row_cells)
    _print_table(rows, col_headers, cells)


# ── deltas table ──────────────────────────────────────────────────────────────

def _print_deltas_table(
    records: list[ScenarioRecord],
    columns: list[tuple[str, str]],
    resolve: callable,
) -> None:
    _print_section(f"DELTAS (H vs G)  ·  {_c("green", _GREEN)} = increase  ·  {_c("red", _RED)} = decrease")
    col_headers = [resolve(label, algo) for label, algo in columns]
    delta_keys: list[tuple[str, str]] = []
    seen: set = set()
    for r in records:
        for metric_name, summary in r.deltas.items():
            for key in summary:
                pair = (metric_name, key)
                if pair not in seen:
                    delta_keys.append(pair)
                    seen.add(pair)
    rows = [_abbrev_row(m, k) for m, k in delta_keys]
    cells = []
    for metric_name, key in delta_keys:
        row_cells = []
        for r in records:
            val = r.deltas.get(metric_name, {}).get(key, "—")
            is_delta = key.endswith("_delta") or metric_name in (
                "spectral similarity", "spectral_similarity"
            )
            row_cells.append(_fmt(val, is_delta=is_delta))
        cells.append(row_cells)
    _print_table(rows, col_headers, cells)