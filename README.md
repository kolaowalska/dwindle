# dwindle
> an evolving research environment for the systematic study of graph reduction methods.

## overview & purpose
this project is a panoramic, research-oriented pipeline for evaluating graph reduction algorithms. it's designed to support thesis-level experimentation by allowing the user to compare different algorithms that reduce graph complexity and the ways they influence graph properties in large-scale networks. 

the core goal of this framework is to become a tool for the systematic study of reduction techniques and potentially evolve into a research environment as an automated laboratory for graph theory.

*__note__: the project is an unfolding consequence of my bachelor's `thesis.pdf`. it is still very much a work in progress (hence the demo) but is constantly evolving to hopefully become part of my postgraduate research at jagiellonian university.*

### general functionalities

* __multi-source graph ingestion__: loading graphs from various formats (edgelists, memory objects) via a unified gateway. additionally, the framework uses lazy loading to boost performance while handling large datasets
* __polymorphic transformations__: support for different types of graph reduction
  - __sparsification__ - selection of the most significant nodes/edges and discarding others
  - __coarsening__ - aggregation of similar nodes/edges to construct a smaller graph
  - __condensation (work in progress)__ - learning a synthetic graph from scratch
* __automated metric registry__: calculating structural properties in the original and modified graph on the fly 
* __experiment management__: orchestrating full experiments from start to finish, where a graph is imported, transformed, analyzed, and the results are persisted as an audit trail
* __efficiency benchmarking__: automatic tracking of wall-clock time for both transformation and metric phases to evaluate theoretical vs. empirical complexity
* __visualization__: basic metric value plots and graph figures

### structure tour d'horizon
the framework is built using domain-driven design principles and organized into distinct layers to ensure that experimental logic remains decoupled from infrastructure concerns. the plugin-forward architecture is highly adaptable and makes the program open for future extension.

- `src/domain/` layer contains the core truth of the system, such as the `Graph` model, `Metric` definitions, and the abstract `GraphTransform` logic; it is purely focused on graph theory and the mathematics behind the graph algorithms
- `src/application/` layer orchestrates the workflow via the `ExperimentService`, handling the "business logic" of running a research job without needing to know how graphs are stored and where they come from
- `src/infrastructure/` layer takes care of details like reading graphs (`GraphGateway`), persisting results (`Repository`), and managing database transactions (`UnitOfWork`)
- `src/interfaces/` layer provides entry points for the user including a CLI for automated batches and an API for potential integration with web dashboards

### the pipeline
the program follows a defined lifecycle for every experiment.
1. __import__: the `GraphGateway` reads raw data and creates a lazy object
2. __orchestration__: the `ExperimentService` receives a command via a CLI/API and fetches the original graph from the `Repository`
3. __transformation__: the system looks up the requested algorithm in a `Registry` and executes it, producing a new `Graph` object while keeping the original graph intact
4. __analysis__: a series of `Metrics` is run against the graph and return detailed dictionaries of values and metadata from the calculation
5. __commitment__: the `UnitOfWork` ensures that both the new graph and the experiment results are saved to storage simultaneously, preventing dirty data resulting from errors

## quick start
### installation
1. clone or download the repository to your local machine
2. open the terminal and navigate to the project's root directory
3. run the following command:
~~~shell
pip install -e .
~~~
this makes the `dwindle` command available system-wide. a virtual environment is recommended.

### discovering what's available
before running an experiment, list the algorithms and metrics the framework is aware of:
~~~shell
dwindle list-algorithms
dwindle list-metrics
~~~

### using the cli
to perform an experiment, run the following command:
~~~shell
dwindle run --graph <path> --algorithm <name> [options]
~~~

**required:**
  - `--graph` — path to your graph file; the format is inferred from the file extension
  - `--algorithm` — name of the reduction algorithm to apply (from `list-algorithms`)
  
**optional:**
  - `--metrics` — comma-separated list of metrics to compute, e.g. `diameter, clustering, community_preservation`
  - `--params` — algorithm parameters, either as space-separated `key=value` pairs or a single json object
  - `--output` — write results to a file instead of printing; supports `.json` and `.csv`
  - `--directed` — treat the graph as directed (default: undirected)
  - `--weighted` — treat the third column in the edgelist as edge weights (default: unweighted)
  - `--plugin` — path to a python file to import before registry discovery; can be repeated to load multiple plugins (see [extending via plugins](#extending-via-plugins))

### examples

run random sparsification and print results to the terminal:
~~~shell
dwindle run --graph my_graph.edgelist --algorithm random --weighted --params p=0.4 seed=420 --metrics diameter,clustering
~~~

pass parameters as a json object and save results to a flat csv for further analysis:
~~~shell
dwindle run --graph my_graph.edgelist --algorithm k_neighbor --weighted --params '{"rho": 0.5}' --metrics edge_density,spectral_similarity --output results.csv
~~~

load a custom algorithm from outside the project before running:
~~~shell
dwindle --plugin ~/research/my_sparsifier.py run --graph my_graph.edgelist --algorithm my-algo --metrics clustering
~~~

--- 
/*TODO*/

### batch benchmarking
to run one algorithm across an entire directory of graphs and collect results into a single csv:
~~~shell
dwindle batch --dir <directory> --algorithm <name> [options]
~~~

**required:**
  - `--dir` — directory containing graph files; any file with a recognised extension (`.edgelist`, `.graphml`, `.gexf`, `.gml`, `.adjlist`, `.edges`, `.txt`) is picked up automatically
  - `--algorithm` — algorithm to apply to every graph in the directory

**optional:**
  - `--metrics` — comma-separated metrics to compute for each graph
  - `--params` — algorithm parameters, same syntax as `run`
  - `--output` — path for the combined csv output (default: `batch_results.csv`)
  - `--pattern` — glob to narrow which files are processed, e.g. `*.edgelist`
  - `--recursive` — descend into subdirectories
  - `--directed` / `--weighted` — applied uniformly to all graphs in the batch

the output csv uses a long format with columns: `graph`, `algorithm`, `nodes_before`, `edges_before`, `nodes_after`, `edges_after`, `metric`, `key`, `value`. each metric key-value pair is its own row, so the file is straightforward to filter and pivot in pandas or a spreadsheet.

if a graph fails to load or the algorithm errors, that file is skipped with a warning and the rest of the batch continues. the exit code is `2` if any graphs were skipped (useful for scripting).

**example** — benchmark local degree sparsification across a d
~~~shell
dwindle batch --dir datasets/snap/ --algorithm local_degree --_density,clustering,diameter --outputresults/snap_benchmark.csv
~~~
~~~shell
# combine with a plugin for a custom algorithm
dwindle --plugin ~/research/my_algo.py batch --dir datasets/ --algorithm my-algo --metrics spectral_similarity --output my_benchmark.csv
~~~

note: the --plugin flag goes before batch (same as with run), since it's a global flag on the top-level parser.

---

## extensibility
### extending via plugins
the `--plugin` flag lets you load any `.py` file before the internal registries are populated, so you can add algorithms, metrics, or transforms without touching the project source.

a plugin file is a plain python module that uses the same registration decorators as the built-in implementations:

~~~python
# ~/research/my_sparsifier.py
import networkx as nx
from src.domain.sparsifiers.registry import register_sparsifier
from src.domain.sparsifiers.base import Sparsifier

@register_sparsifier("my-algo")
class MySparsifier(Sparsifier):
    def reduce(self, g: nx.Graph, **params) -> nx.Graph:
        ...
~~~

pass the file as a global flag (before the subcommand) so it applies to every command, including `list-algorithms` and `list-metrics`:
~~~shell
# use the algorithm immediately
dwindle --plugin ~/research/my_sparsifier.py run --graph g.edgelist --algorithm my-algo

# confirm it's visible in the registry
dwindle --plugin ~/research/my_sparsifier.py list-algorithms

# load several plugins at once
dwindle --plugin ~/algo.py --plugin ~/metric.py run --graph g.edgelist --algorithm my-algo --metrics my-metric
~~~
the plugin's parent directory is automatically added to `sys.path`, so any local imports inside the plugin resolve relative to its own location regardless of where `graph-reduce` is invoked from.

### algorithm agnosticism
it makes no difference whether the operation is removing edges, merging nodes, or reweighting the entire graph; as long as the algorithm follows the `GraphTransform` interface, it can be plugged into the pipeline without changing a single line of core code.

### dynamic metric discovery 
adding a new metric requires only creating a single new file, and the system automatically discovers new metrics at runtime using a scanning decorator. this makes it trivial to add new evaluation criteria with progressing research needs.

### interchangeable storage
the current system uses an in-memory storage for speed and demo purposes, but the architecture is decoupled such that swapping to a SQL database or a specialized graph database (like Neo4j) requires only changing the `Repository` implementation, while the rest of the logic remains untouched.

### future directions
this project is designed to eventually support adapting reduction strategies in dynamic graphs and automating the selection of reduction techniques based on graph topology for machine learning integration. 
