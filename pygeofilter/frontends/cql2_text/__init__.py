from ...ast import Node
from ..abc import Frontend
from .parser import parse


__all__ = ["parse"]


class CQL2TextFrontend(Frontend):
    def parse(self, raw: str) -> Node:
        return super().parse(raw)