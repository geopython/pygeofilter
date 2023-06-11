from ..abc import Frontend
from ...ast import Node

from .parser import parse
from .encoder import encode


class ECQLFrontend(Frontend):
    def parse(self, raw: str) -> Node:
        return parse(raw)

    def encode(self, root: Node) -> str:
        return encode(root)
