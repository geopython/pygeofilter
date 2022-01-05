# ------------------------------------------------------------------------------
#
# Project: pygeofilter <https://github.com/geopython/pygeofilter>
# Authors: Fabian Schindler <fabian.schindler@eox.at>, David Bitner <bitner@dbspatial.com>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2021 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# ------------------------------------------------------------------------------

from typing import Dict

import shapely.geometry

from ..evaluator import Evaluator, handle
from ... import ast
from ... import values


COMPARISON_OP_MAP = {
    ast.ComparisonOp.EQ: '=',
    ast.ComparisonOp.NE: '<>',
    ast.ComparisonOp.LT: '<',
    ast.ComparisonOp.LE: '<=',
    ast.ComparisonOp.GT: '>',
    ast.ComparisonOp.GE: '>=',
}


ARITHMETIC_OP_MAP = {
    ast.ArithmeticOp.ADD: '+',
    ast.ArithmeticOp.SUB: '-',
    ast.ArithmeticOp.MUL: '*',
    ast.ArithmeticOp.DIV: '/',
}

SPATIAL_COMPARISON_OP_MAP = {
    ast.SpatialComparisonOp.INTERSECTS: 'ST_Intersects',
    ast.SpatialComparisonOp.DISJOINT: 'ST_Disjoint',
    ast.SpatialComparisonOp.CONTAINS: 'ST_Contains',
    ast.SpatialComparisonOp.WITHIN: 'ST_Within',
    ast.SpatialComparisonOp.TOUCHES: 'ST_Touches',
    ast.SpatialComparisonOp.CROSSES: 'ST_Crosses',
    ast.SpatialComparisonOp.OVERLAPS: 'ST_Overlaps',
    ast.SpatialComparisonOp.EQUALS: 'equals',
}


class CQLEvaluator(Evaluator):
    def __init__(self, attribute_map: Dict[str, str], function_map: Dict[str, str]):
        self.attribute_map = attribute_map
        self.function_map = function_map

    @handle(ast.Not)
    def not_(self, node, sub):
        return {"not": [ sub ]}

    @handle(ast.And, ast.Or)
    def combination(self, node, lhs, rhs):
        return {node.op.value: [lhs, rhs]}

    @handle(ast.Comparison, subclasses=True)
    def comparison(self, node, lhs, rhs):
        return {COMPARISON_OP_MAP[node.op]: [lhs, rhs]}

    # @handle(ast.Between)
    # def between(self, node, lhs, low, high):
    #     return {"between": ["value": lhs, "lower": low, "upper": high]}
    #     return f"({lhs} {'NOT ' if node.not_ else ''}BETWEEN {low} AND {high})"

    @handle(ast.Like)
    def like(self, node, lhs):
        pattern = node.pattern
        if node.wildcard != '%':
            # TODO: not preceded by escapechar
            pattern = pattern.replace(node.wildcard, '%')
        if node.singlechar != '_':
            # TODO: not preceded by escapechar
            pattern = pattern.replace(node.singlechar, '_')

        # TODO: handle node.nocase
        return {"like": [lhs, pattern]}
        return f"{lhs} {'NOT ' if node.not_ else ''}LIKE '{pattern}' ESCAPE '{node.escapechar}'"

    @handle(ast.In)
    def in_(self, node, lhs, *options):
        return {"in": {"value": lhs, "list": options}}

    @handle(ast.IsNull)
    def null(self, node, lhs):
        return {"isNull": lhs}

    @handle(ast.TemporalPredicate, subclasses=True)
    def temporal(self, node, lhs, rhs):
        func = TEMPORAL_COMPARISON_OP_MAP[node.op]
        return {func: [lhs, rhs]}

    @handle(ast.SpatialComparisonPredicate, subclasses=True)
    def spatial_operation(self, node, lhs, rhs):
        func = SPATIAL_COMPARISON_OP_MAP[node.op]
        return {func: [lhs, rhs]}

    @handle(ast.BBox)
    def bbox(self, node, lhs):
        func = SPATIAL_COMPARISON_OP_MAP[ast.SpatialComparisonOp.INTERSECTS]
        # TODO: create BBox geometry
        return {func: [lhs, rhs]}

    @handle(ast.Attribute)
    def attribute(self, node: ast.Attribute):
        return {"property": node.name}

    @handle(ast.Arithmetic, subclasses=True)
    def arithmetic(self, node: ast.Arithmetic, lhs, rhs):
        op = ARITHMETIC_OP_MAP[node.op]
        return {op: [lhs, rhs]}


    @handle(*values.LITERALS)
    def literal(self, node):
        return node

    @handle(values.Geometry)
    def geometry(self, node: values.Geometry):
        wkb_hex = shapely.geometry.shape(node).wkb_hex
        return f"ST_GeomFromWKB(x'{wkb_hex}')"

    @handle(values.Envelope)
    def envelope(self, node: values.Envelope):
        wkb_hex = shapely.geometry.box(node.x1, node.y1, node.x2, node.y2).wkb_hex
        return f"ST_GeomFromWKB(x'{wkb_hex}')"


def to_cql(root: ast.Node, field_mapping: Dict[str, str]=None, function_map: Dict[str, str]=None) -> str:
    return CQLEvaluator(field_mapping, function_map).evaluate(root)
