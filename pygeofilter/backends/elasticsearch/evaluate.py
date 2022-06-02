# ------------------------------------------------------------------------------
#
# Project: pygeofilter <https://github.com/geopython/pygeofilter>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
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

from typing import Dict, Optional, cast

import shapely.geometry
from elasticsearch_dsl import Q
from elasticsearch_dsl.query import Query

from ..evaluator import Evaluator, handle
from ... import ast
from ... import values
from .util import like_to_wildcard


COMPARISON_OP_MAP = {
    ast.ComparisonOp.LT: 'lt',
    ast.ComparisonOp.LE: 'lte',
    ast.ComparisonOp.GT: 'gt',
    ast.ComparisonOp.GE: 'gte',
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
    ast.SpatialComparisonOp.EQUALS: 'ST_Equals',
}


class ElasticSearchDSLEvaluator(Evaluator):
    def __init__(self, attribute_map: Optional[Dict[str, str]] = None):
        self.attribute_map = attribute_map

    @handle(ast.Not)
    def not_(self, node, sub):
        return ~sub

    @handle(ast.And)
    def and_(self, node, lhs, rhs):
        return lhs & rhs

    @handle(ast.Or)
    def or_(self, node, lhs, rhs):
        return lhs | rhs

    @handle(ast.Equal, ast.NotEqual)
    def equality(self, node, lhs, rhs):
        q = Q("match", **{lhs: rhs})
        if node.op == ast.ComparisonOp.NE:
            q = ~q
        return q

    @handle(ast.LessThan, ast.LessEqual, ast.GreaterThan, ast.GreaterEqual)
    def comparison(self, node, lhs, rhs):
        return Q("range", **{lhs: {COMPARISON_OP_MAP[node.op]: rhs}})

    @handle(ast.Between)
    def between(self, node, lhs, low, high):
        return Q("range", **{lhs: {"gte": low, "lte": high}})

    @handle(ast.Like)
    def like(self, node: ast.Like, lhs):
        pattern = like_to_wildcard(node.pattern, node.wildcard, node.singlechar, node.escapechar)

        # TODO: does not seem to work
        return Q("wildcard", **{
            lhs: {
                "value": pattern,
                "case_insensitive": node.nocase
            }
        })

    # @handle(ast.In)
    # def in_(self, node, lhs, *options):
    #     return f"{lhs} {'NOT ' if node.not_ else ''}IN ({', '.join(options)})"

    @handle(ast.IsNull)
    def null(self, node: ast.IsNull, lhs):
        q = cast(Query, Q("exists", field=lhs))
        if not node.not_:
            q = ~q
        return q

    # @handle(ast.TemporalPredicate, subclasses=True)
    # def temporal(self, node, lhs, rhs):
    #     pass

    @handle(
        ast.GeometryIntersects,
        ast.GeometryDisjoint,
        ast.GeometryContains,
        ast.GeometryContains,
        subclasses=True,
    )
    def spatial_comparison(self, node: ast.SpatialComparisonPredicate, lhs, rhs):
        return Q(
            "geo_shape",
            **{
            lhs: {
                    "shape": rhs,
                    "relation": node.op.value.lower(),
            },
            }
        )

    # @handle(ast.BBox)
    # def bbox(self, node, lhs):
    #     func = SPATIAL_COMPARISON_OP_MAP[ast.SpatialComparisonOp.INTERSECTS]
    #     # TODO: create BBox geometry
    #     rhs = ""
    #     return f"{func}({lhs},{rhs})"

    @handle(ast.Attribute)
    def attribute(self, node: ast.Attribute):
        if self.attribute_map is not None:
            return self.attribute_map[node.name]
        return node.name

    # @handle(ast.Arithmetic, subclasses=True)
    # def arithmetic(self, node: ast.Arithmetic, lhs, rhs):
    #     op = ARITHMETIC_OP_MAP[node.op]
    #     return f"({lhs} {op} {rhs})"

    # @handle(ast.Function)
    # def function(self, node, *arguments):
    #     func = self.function_map[node.name]
    #     return f"{func}({','.join(arguments)})"

    @handle(*values.LITERALS)
    def literal(self, node):
        return node

    @handle(values.Geometry)
    def geometry(self, node: values.Geometry):
        return node.geometry

    @handle(values.Envelope)
    def envelope(self, node: values.Envelope):
        return {
            "type": "envelope",
            "coordinates": [
                [
                    min(node.x1, node.x2),
                    max(node.y1, node.y2),
                ],
                [
                    max(node.x1, node.x2),
                    min(node.y1, node.y2),
                ],
            ],
        }

# def to_sql_where(root: ast.Node, field_mapping: Dict[str, str],
#                  function_map: Optional[Dict[str, str]] = None) -> str:
#     return SQLEvaluator(field_mapping, function_map or {}).evaluate(root)


def to_filter(root, attribute_map: Optional[Dict[str, str]] = None):
    return ElasticSearchDSLEvaluator(attribute_map).evaluate(root)
