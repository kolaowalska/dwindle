from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Optional

from src.interfaces.api import ExperimentFacade
from src.domain.sparsifiers.registry import SparsifierRegistry
from src.domain.transforms.registry import TransformRegistry
from src.domain.metrics.registry import MetricRegistry
from src.domain.common.plugin_discovery import load_plugin_file


def _parse_params(raw: list[str] | None) -> dict:
    if not raw:
        return {}
    if len(raw) == 1 and raw[0].strip().startswith("{"):
        return json.loads(raw[0])
    result = {}
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


def _print_result(data: dict, output: Optional[str]) -> None:
    if output is None:
        print(f"\n{data['graph_name']}  →  {data['algorithm_name']}")
        print(f"  nodes : {data['nodes_before']} → {data['nodes_after']}")
        print(f"  edges : {data['edges_before']} → {data['edges_after']}")
        if data["metric_results"]:
            print("  metrics:")
            for m in data["metric_results"]:
                vals = "  ".join(f"{k}={_fmt(v)}" for k, v in m["summary"].items())
                print(f"    {m['metric']}: {vals}")
        return

    if output.endswith(".csv"):
        rows = [
            {
                "graph": data["graph_name"],
                "algorithm": data["algorithm_name"],
                "metric": m["metric"],
                "key": k,
                "value": v,
            }
            for m in data["metric_results"]
            for k, v in m["summary"].items()
        ]
        with open(output, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["graph", "algorithm", "metric", "key", "value"])
            writer.writeheader()
            writer.writerows(rows)
    else:
        with open(output, "w") as f:
            json.dump(data, f, indent=2, default=str)

    print(f"results written to {output}")


def cmd_run(args) -> int:
    facade = ExperimentFacade()

    graph_name = Path(args.graph).stem
    upload_resp = facade.upload_graph({
        "path": args.graph,
        "name": graph_name,
        "kind": "file",
        "directed": args.directed,
        "weighted": args.weighted,
    })

    if upload_resp["status"] != "success":
        print(f"error: {upload_resp['message']}", file=sys.stderr)
        return 1

    metrics = [m.strip() for m in args.metrics.split(",")] if args.metrics else []
    try:
        params = _parse_params(args.params)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    run_resp = facade.run_job({
        "graph_key": upload_resp["graph_key"],
        "algorithm": args.algorithm,
        "metrics": metrics,
        "params": params,
    })

    if run_resp["status"] != "success":
        print(f"error: {run_resp['message']}", file=sys.stderr)
        return 1

    _print_result(run_resp["data"], args.output)
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


def run_cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="dwindle",
        description="graph complexity reduction framework",
    )
    parser.add_argument(
        "--plugin", metavar="FILE", action="append", default=[],
        help="load a plugin module before registry discovery (repeatable)",
    )
    sub = parser.add_subparsers(dest="command")

    run_p = sub.add_parser("run", help="run a reduction experiment on a graph file")
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

    sub.add_parser("list-algorithms", help="list available reduction algorithms")
    sub.add_parser("list-metrics", help="list available metrics")
    sub.add_parser("smoke", help="run a quick smoke test")

    args = parser.parse_args(argv)

    for plugin_path in args.plugin:
        try:
            load_plugin_file(plugin_path)
        except FileNotFoundError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1

    if args.command == "run":
        return cmd_run(args)
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
