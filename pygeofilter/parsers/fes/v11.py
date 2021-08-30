from ... import ast
from .base import FESBaseParser
from .util import handle, ParseInput


class FES11Parser(FESBaseParser):
    namespace = 'http://www.opengis.net/ogc'

    @handle('Add')
    def add(self, node, lhs, rhs):
        return ast.Add(lhs, rhs)

    @handle('Sub')
    def sub(self, node, lhs, rhs):
        return ast.Sub(lhs, rhs)

    @handle('Mul')
    def mul(self, node, lhs, rhs):
        return ast.Mul(lhs, rhs)

    @handle('Div')
    def div(self, node, lhs, rhs):
        return ast.Div(lhs, rhs)


def parse(input_: ParseInput) -> ast.Node:
    return FES11Parser().parse(input_)
