from abc import ABC, abstractmethod

from ..ast import Node


class Frontend(ABC):

    @abstractmethod
    def parse(self, raw: str) -> Node:
        ...

    @abstractmethod
    def encode(self, root: Node) -> str:
        ...
