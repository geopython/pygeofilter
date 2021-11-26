from ... import ast
from .base import FESBaseParser
from .util import handle, ParseInput, Element


class FES11Parser(FESBaseParser):
    namespace = 'http://www.opengis.net/ogc'

    @handle('Add')
    def add(self, node: Element, lhs: ast.ScalarAstType,
            rhs: ast.ScalarAstType) -> ast.Node:
        return ast.Add(lhs, rhs)

    @handle('Sub')
    def sub(self, node: Element, lhs: ast.ScalarAstType,
            rhs: ast.ScalarAstType) -> ast.Node:
        return ast.Sub(lhs, rhs)

    @handle('Mul')
    def mul(self, node: Element, lhs: ast.ScalarAstType,
            rhs: ast.ScalarAstType) -> ast.Node:
        return ast.Mul(lhs, rhs)

    @handle('Div')
    def div(self, node: Element, lhs: ast.ScalarAstType,
            rhs: ast.ScalarAstType) -> ast.Node:
        return ast.Div(lhs, rhs)


def parse(input_: ParseInput) -> ast.Node:
    return FES11Parser().parse(input_)
