from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.graph_model import Graph
from src.domain.experiment import Experiment, RunID



class GraphRepository(ABC):
    """
    interface for storing and retrieving Graph domain objects
    """
    @abstractmethod
    def save(self, graph: Graph) -> None:
        pass

    @abstractmethod
    def get(self, name: str) -> Optional[Graph]:
        pass

    @abstractmethod
    def list_names(self) -> List[str]:
        pass

    @abstractmethod
    def delete(self, name: str) -> None:
        pass


class ExperimentRepository(ABC):
    """
    interface for storing and retrieving Experiment entities
    """
    @abstractmethod
    def save(self, experiment: Experiment):
        pass

    @abstractmethod
    def get(self, run_id: RunID) -> Optional[Experiment]:
        pass

    @abstractmethod
    def delete(self, run_id: RunID) -> None:
        pass

    @abstractmethod
    def list_all(self) -> List[Experiment]:
        pass
