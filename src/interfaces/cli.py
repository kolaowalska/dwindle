from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from pathlib import Path
from typing import Optional

from src.interfaces.api import ExperimentFacade
from src.infrastructure.persistence.stubs import InMemoryExperimentRepository
from src.infrastructure.persistence.json_store import JsonExperimentRepository, resolve_store
from src.domain.sparsifiers.registry import SparsifierRegistry
from src.domain.transforms.registry import TransformRegistry
from src.domain.metrics.registry import MetricRegistry
from src.domain.common.plugin_discovery import load_plugin_file

_GRAPH_EXTENSIONS = {".graphml", ".gexf", ".gml", ".adjlist", ".edgelist", ".txt", ".edges", ".csv"}
_CSV_FIELDNAMES = ["run_id", "graph", "algorithm", "nodes_before", "edges_before", "nodes_after",
                   "edges_after", "transform_seconds", "metric", "key", "value"]


def _parse_params(raw: list[str] | None) -> dict:
    if not raw:
        return {}
    if len(raw) == 1 and raw[0].strip().startswith("{"):
        return json.loads(raw[0])
    result: dict = {}
    for item in raw:
        if "=" not in item:
            raise ValueError(f"invalid param '{item}': expected KEY=VALUE format")
        k, _, v = item.partition("=")
        try:
            result[k] = int(v)
        except ValueError:
            try:
                result[k] = float(v)
            except ValueError:
                result[k] = v
    return result


def _fmt(v) -> str:
    if isinstance(v, float):
        return f"{v:.4g}"
    return str(v)


def _fmt_signed(v) -> str:
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, float):
        return f"{v:+.4g}"
    if isinstance(v, int):
        return f"{v:+d}"
    return str(v)


def _delta_rows(summary: dict) -> list[tuple[str, str]]:
    rows = []
    paired = set()

    for key in summary:
        if not key.endswith("_original"):
            continue
        base = key[: -len("_original")]
        reduced, delta = f"{base}_reduced", f"{base}_delta"
        if reduced in summary and delta in summary:
            rows.append((base, f"{_fmt(summary[key])} → {_fmt(summary[reduced])} ({_fmt_signed(summary[delta])})"))
            paired.update({key, reduced, delta})

    for key, value in summary.items():
        if key not in paired and key != "execution_time":
            rows.append((key, _fmt(value)))

    return rows


def _configure_logging(verbosity: int) -> None:
    level = {0: logging.WARNING, 1: logging.INFO}.get(verbosity, logging.DEBUG)
    logging.basicConfig(level=level, format="%(levelname)s  %(name)s: %(message)s")
    logging.getLogger().setLevel(level)


def _experiment_repo(args):
    if getattr(args, "no_store", False):
        return InMemoryExperimentRepository()
    return JsonExperimentRepository(resolve_store(getattr(args, "store", None)))


def _experiment_to_data(experiment) -> dict:
    """shape a stored Experiment like a run response so it shares the csv schema"""
    return {
        "run_id": str(experiment.run_id),
        "graph_name": experiment.graph_name or "",
        "algorithm_name": experiment.algorithm or "",
        "nodes_before": experiment.nodes_before,
        "edges_before": experiment.edges_before,
        "nodes_after": experiment.nodes_after,
        "edges_after": experiment.edges_after,
        "transform_seconds": experiment.transform_seconds,
        "metric_results": [
            {"metric": name, "summary": dict(result.summary)}
            for name, result in experiment.results.items()
        ],
    }


def _result_rows(data: dict) -> list[dict]:
    base = {
        "run_id": data.get("run_id", ""),
        "graph": data["graph_name"],
        "algorithm": data["algorithm_name"],
        "nodes_before": data["nodes_before"],
        "edges_before": data["edges_before"],
        "nodes_after": data["nodes_after"],
        "edges_after": data["edges_after"],
        "transform_seconds": data.get("transform_seconds", ""),
    }
    if not data["metric_results"]:
        return [{**base, "metric": "", "key": "", "value": ""}]
    return [
        {**base, "metric": m["metric"], "key": k, "value": v}
        for m in data["metric_results"]
        for k, v in m["summary"].items()
    ]


def _print_result(data: dict, output: Optional[str]) -> None:
    if output is None:
        print(f"\n{data['graph_name']}  →  {data['algorithm_name']}")
        print(f"  nodes : {data['nodes_before']} → {data['nodes_after']}")
        print(f"  edges : {data['edges_before']} → {data['edges_after']}")
        if data["metric_results"]:
            print("  metrics:")
            for m in data["metric_results"]:
                rows = _delta_rows(m["summary"])
                if not rows:
                    continue
                width = max(len(label) for label, _ in rows)
                head = f"{m['metric']}: "
                for i, (label, rendered) in enumerate(rows):
                    prefix = head if i == 0 else " " * len(head)
                    print(f"    {prefix}{label:<{width}}  {rendered}")
        return

    if output.endswith(".csv"):
        with open(output, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=_CSV_FIELDNAMES)
            writer.writeheader()
            writer.writerows(_result_rows(data))
    else:
        with open(output, "w") as f:
            json.dump(data, f, indent=2, default=str)

    print(f"results written to {output}")


def cmd_run(args) -> int:
    facade = ExperimentFacade(experiment_repo=_experiment_repo(args))

    graph_name = Path(args.graph).stem
    try:
        upload_resp = facade.upload_graph({
            "path": args.graph,
            "name": graph_name,
            "kind": "file",
            "directed": args.directed,
            "weighted": args.weighted,
        })
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    metrics = [m.strip() for m in args.metrics.split(",")] if args.metrics else []
    try:
        params = _parse_params(args.params)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    try:
        run_resp = facade.run_job({
            "graph_key": upload_resp["graph_key"],
            "algorithm": args.algorithm,
            "metrics": metrics,
            "params": params,
        })
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    _print_result(run_resp["data"], args.output)
    return 0


def cmd_history(args) -> int:
    runs = _experiment_repo(args).list_all()

    if not runs:
        print("no runs recorded yet")
        return 0

    if args.output:
        rows = [r for e in runs for r in _result_rows(_experiment_to_data(e))]
        with open(args.output, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=_CSV_FIELDNAMES)
            writer.writeheader()
            writer.writerows(rows)
        print(f"{len(runs)} run(s) written to {args.output}")
        return 0

    print(f"{'RUN':<10}{'GRAPH':<18}{'ALGORITHM':<18}{'EDGES':<16}{'TIME':>9}")
    for e in runs:
        edges = f"{e.edges_before} → {e.edges_after}" if e.edges_before is not None else "—"
        secs = f"{e.transform_seconds:.4f}s" if e.transform_seconds is not None else "—"
        print(f"{str(e.run_id)[:8]:<10}{(e.graph_name or '—')[:17]:<18}"
              f"{(e.algorithm or '—')[:17]:<18}{edges:<16}{secs:>9}")
    print(f"\n{len(runs)} run(s)")
    return 0


def cmd_list_algorithms(args) -> int:
    SparsifierRegistry.discover()
    TransformRegistry.discover()
    print("sparsifiers:  " + "  ".join(SparsifierRegistry.list()))
    print("transforms:   " + "  ".join(TransformRegistry.list()))
    return 0


def cmd_list_metrics(args) -> int:
    MetricRegistry.discover()
    print("metrics:  " + "  ".join(MetricRegistry.list()))
    return 0


def cmd_batch(args) -> int:
    graph_dir = Path(args.dir)
    if not graph_dir.is_dir():
        print(f"error: '{args.dir}' is not a directory", file=sys.stderr)
        return 1

    pattern = args.pattern or "*"
    walker = graph_dir.rglob(pattern) if args.recursive else graph_dir.glob(pattern)
    files = sorted(
        p for p in walker
        if p.is_file() and p.suffix.lower() in _GRAPH_EXTENSIONS
    )

    if not files:
        print(f"error: no graph files found in '{args.dir}' (pattern: {pattern})", file=sys.stderr)
        return 1

    metrics = [m.strip() for m in args.metrics.split(",")] if args.metrics else []
    try:
        params = _parse_params(args.params)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    output_path = Path(args.output)
    experiment_repo = _experiment_repo(args)
    rows: list[dict] = []
    ok = 0
    failed = 0

    print(f"batch: {len(files)} graph(s)  algorithm={args.algorithm}  output={output_path}")

    for path in files:
        facade = ExperimentFacade(experiment_repo=experiment_repo)
        graph_name = path.stem

        try:
            upload_resp = facade.upload_graph({
                "path": str(path),
                "name": graph_name,
                "kind": "file",
                "directed": args.directed,
                "weighted": args.weighted,
            })
            run_resp = facade.run_job({
                "graph_key": upload_resp["graph_key"],
                "algorithm": args.algorithm,
                "metrics": metrics,
                "params": params,
            })
        except Exception as e:
            print(f"  SKIP  {path.name}: {e}", file=sys.stderr)
            failed += 1
            continue

        data = run_resp["data"]
        rows.extend(_result_rows(data))

        reduction = 100 * (1 - data["edges_after"] / data["edges_before"]) if data["edges_before"] else 0
        print(f"  OK    {path.name}  edges {data['edges_before']} → {data['edges_after']} ({reduction:.1f}% reduction)")
        ok += 1

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=_CSV_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\ndone: {ok} succeeded, {failed} failed  →  {output_path}")
    return 0 if failed == 0 else 2


def run_cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="dwindle",
        description="graph complexity reduction framework",
    )
    parser.add_argument(
        "--plugin", metavar="FILE", action="append", default=[],
        help="load a plugin module before registry discovery (repeatable)",
    )
    parser.add_argument(
        "-v", "--verbose", action="count", default=0,
        help="show log output (-v for info, -vv for debug)",
    )
    store_opts = argparse.ArgumentParser(add_help=False)
    store_opts.add_argument(
        "--store", metavar="DIR",
        help=f"directory holding the run store (default: $DWINDLE_STORE or ./{'.dwindle'})",
    )
    store_opts.add_argument(
        "--no-store", action="store_true", help="do not record this run to disk",
    )

    sub = parser.add_subparsers(dest="command")

    run_p = sub.add_parser("run", parents=[store_opts], help="run a reduction experiment on a graph file")
    run_p.add_argument("--graph", required=True, help="path to graph file (edgelist format)")
    run_p.add_argument("--algorithm", required=True, help="algorithm name  (see: list-algorithms)")
    run_p.add_argument("--metrics", help="comma-separated metric names  (see: list-metrics)")
    run_p.add_argument(
        "--params", nargs="*", metavar="KEY=VALUE",
        help="algorithm params as KEY=VALUE pairs or a single JSON object string",
    )
    run_p.add_argument("--output", metavar="FILE", help="write results to FILE (.json or .csv); default: stdout")
    run_p.add_argument("--directed", action="store_true", help="treat graph as directed")
    run_p.add_argument("--weighted", action="store_true", help="treat graph as weighted")

    batch_p = sub.add_parser(
        "batch", parents=[store_opts],
        help="run one algorithm across a directory of graphs and produce a combined CSV",
    )
    batch_p.add_argument("--dir", required=True, metavar="DIR", help="directory containing graph files")
    batch_p.add_argument("--algorithm", required=True, help="algorithm name  (see: list-algorithms)")
    batch_p.add_argument("--metrics", help="comma-separated metric names  (see: list-metrics)")
    batch_p.add_argument(
        "--params", nargs="*", metavar="KEY=VALUE",
        help="algorithm params as KEY=VALUE pairs or a single JSON object string",
    )
    batch_p.add_argument(
        "--output", default="batch_results.csv", metavar="FILE",
        help="output CSV path (default: batch_results.csv)",
    )
    batch_p.add_argument(
        "--pattern", metavar="GLOB",
        help="filename glob to filter graph files (default: all recognised extensions)",
    )
    batch_p.add_argument("--recursive", action="store_true", help="recurse into subdirectories")
    batch_p.add_argument("--directed", action="store_true", help="treat all graphs as directed")
    batch_p.add_argument("--weighted", action="store_true", help="treat all graphs as weighted")

    history_p = sub.add_parser("history", parents=[store_opts], help="list runs recorded in the store")
    history_p.add_argument("--output", metavar="FILE", help="export every recorded run to a combined CSV")

    sub.add_parser("list-algorithms", help="list available reduction algorithms")
    sub.add_parser("list-metrics", help="list available metrics")
    sub.add_parser("smoke", help="run a quick smoke test")

    args = parser.parse_args(argv)
    _configure_logging(args.verbose)

    for plugin_path in args.plugin:
        try:
            load_plugin_file(plugin_path)
        except FileNotFoundError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1

    if args.command == "run":
        return cmd_run(args)
    if args.command == "batch":
        return cmd_batch(args)
    if args.command == "history":
        return cmd_history(args)
    if args.command == "list-algorithms":
        return cmd_list_algorithms(args)
    if args.command == "list-metrics":
        return cmd_list_metrics(args)
    if args.command == "smoke":
        from src.interfaces.smoke import run_smoke
        run_smoke()
        return 0

    parser.print_help()
    return 0
