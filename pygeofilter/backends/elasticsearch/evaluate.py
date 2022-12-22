# ------------------------------------------------------------------------------
#
# Project: pygeofilter <https://github.com/geopython/pygeofilter>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2022 EOX IT Services GmbH
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

"""
Elasticsearch filter evaluator.

Uses elasticsearch-dsl package to create filter objects.
"""


# pylint: disable=E1130,C0103,W0223

from datetime import date, datetime
from typing import Dict, Optional, Union

from elasticsearch_dsl import Q
from packaging.version import Version

from ... import ast, values
from ..evaluator import Evaluator, handle
from .util import like_to_wildcard

VERSION_7_10_0 = Version("7.10.0")


COMPARISON_OP_MAP = {
    ast.ComparisonOp.LT: "lt",
    ast.ComparisonOp.LE: "lte",
    ast.ComparisonOp.GT: "gt",
    ast.ComparisonOp.GE: "gte",
}


ARITHMETIC_OP_MAP = {
    ast.ArithmeticOp.ADD: "+",
    ast.ArithmeticOp.SUB: "-",
    ast.ArithmeticOp.MUL: "*",
    ast.ArithmeticOp.DIV: "/",
}


class ElasticSearchDSLEvaluator(Evaluator):
    """A filter evaluator for Elasticsearch DSL."""

    def __init__(
        self,
        attribute_map: Optional[Dict[str, str]] = None,
        version: Optional[Version] = None,
    ):
        self.attribute_map = attribute_map
        self.version = version or Version("7.1.0")

    @handle(ast.Not)
    def not_(self, _, sub):
        """Inverts a filter object."""
        return ~sub

    @handle(ast.And)
    def and_(self, _, lhs, rhs):
        """Joins two filter objects with an `and` operator."""
        return lhs & rhs

    @handle(ast.Or)
    def or_(self, _, lhs, rhs):
        """Joins two filter objects with an `or` operator."""
        return lhs | rhs

    @handle(ast.Equal, ast.NotEqual)
    def equality(self, node, lhs, rhs):
        """Creates a match filter."""
        q = Q("match", **{lhs: rhs})
        if node.op == ast.ComparisonOp.NE:
            q = ~q
        return q

    @handle(ast.LessThan, ast.LessEqual, ast.GreaterThan, ast.GreaterEqual)
    def comparison(self, node, lhs, rhs):
        """Creates a `range` filter."""
        return Q("range", **{lhs: {COMPARISON_OP_MAP[node.op]: rhs}})

    @handle(ast.Between)
    def between(self, node: ast.Between, lhs, low, high):
        """Creates a `range` filter."""
        q = Q("range", **{lhs: {"gte": low, "lte": high}})
        if node.not_:
            q = ~q
        return q

    @handle(ast.Like)
    def like(self, node: ast.Like, lhs):
        """Transforms the provided LIKE pattern to an Elasticsearch wildcard
        pattern. Thus, this only works properly on "wildcard" fields.
        Ignores case-sensitivity when Elasticsearch version is below 7.10.0.
        """
        pattern = like_to_wildcard(
            node.pattern, node.wildcard, node.singlechar, node.escapechar
        )
        expr: Dict[str, Union[str, bool]] = {
            "value": pattern,
        }
        if self.version >= VERSION_7_10_0:
            expr["case_insensitive"] = node.nocase

        q = Q("wildcard", **{lhs: expr})
        if node.not_:
            q = ~q
        return q

    @handle(ast.In)
    def in_(self, node, lhs, *options):
        """Creates a `terms` filter."""
        q = Q("terms", **{lhs: options})
        if node.not_:
            q = ~q
        return q

    @handle(ast.IsNull)
    def null(self, node: ast.IsNull, lhs):
        """Performs a null check, by using the `exists` query on the given
        field.
        """
        q = Q("exists", field=lhs)
        if not node.not_:
            q = ~q
        return q

    @handle(ast.Exists)
    def exists(self, node: ast.Exists, lhs):
        """Performs an existense check, by using the `exists` query on the
        given field
        """
        q = Q("exists", field=lhs)
        if node.not_:
            q = ~q
        return q

    @handle(ast.TemporalPredicate, subclasses=True)
    def temporal(self, node: ast.TemporalPredicate, lhs, rhs):
        """Creates a filter to match the given temporal predicate"""
        op = node.op
        if isinstance(rhs, (date, datetime)):
            low = high = rhs
        else:
            low, high = rhs

        query = "range"
        not_ = False
        predicate: Dict[str, Union[date, datetime, str]]
        if op == ast.TemporalComparisonOp.DISJOINT:
            not_ = True
            predicate = {"gte": low, "lte": high}
        elif op == ast.TemporalComparisonOp.AFTER:
            predicate = {"gt": high}
        elif op == ast.TemporalComparisonOp.BEFORE:
            predicate = {"lt": low}
        elif (
            op == ast.TemporalComparisonOp.TOVERLAPS
            or op == ast.TemporalComparisonOp.OVERLAPPEDBY
        ):
            predicate = {"gte": low, "lte": high}
        elif op == ast.TemporalComparisonOp.BEGINS:
            query = "term"
            predicate = {"value": low}
        elif op == ast.TemporalComparisonOp.BEGUNBY:
            query = "term"
            predicate = {"value": high}
        elif op == ast.TemporalComparisonOp.DURING:
            predicate = {"gt": low, "lt": high, "relation": "WITHIN"}
        elif op == ast.TemporalComparisonOp.TCONTAINS:
            predicate = {"gt": low, "lt": high, "relation": "CONTAINS"}
        # elif op == ast.TemporalComparisonOp.ENDS:
        #     pass
        # elif op == ast.TemporalComparisonOp.ENDEDBY:
        #     pass
        # elif op == ast.TemporalComparisonOp.TEQUALS:
        #     pass
        # elif op == ast.TemporalComparisonOp.BEFORE_OR_DURING:
        #     pass
        # elif op == ast.TemporalComparisonOp.DURING_OR_AFTER:
        #     pass
        else:
            raise NotImplementedError(f"Unsupported temporal operator: {op}")

        q = Q(
            query,
            **{lhs: predicate},
        )
        if not_:
            q = ~q
        return q

    @handle(
        ast.GeometryIntersects,
        ast.GeometryDisjoint,
        ast.GeometryWithin,
        ast.GeometryContains,
    )
    def spatial_comparison(self, node: ast.SpatialComparisonPredicate, lhs: str, rhs):
        """Creates a geo_shape query for the give spatial comparison
        predicate.
        """
        return Q(
            "geo_shape",
            **{
                lhs: {
                    "shape": rhs,
                    "relation": node.op.value.lower(),
                },
            },
        )

    @handle(ast.BBox)
    def bbox(self, node: ast.BBox, lhs):
        """Performs a geo_shape query for the given bounding box.
        Ignores CRS parameter, as it is not supported by Elasticsearch.
        """
        return Q(
            "geo_shape",
            **{
                lhs: {
                    "shape": self.envelope(
                        values.Envelope(node.minx, node.maxx, node.miny, node.maxy)
                    ),
                    "relation": "intersects",
                },
            },
        )

    @handle(ast.Attribute)
    def attribute(self, node: ast.Attribute):
        """Attribute mapping from filter fields to elasticsearch fields.
        If an attribute mapping is provided, it is used to look up the
        field name from there.
        """
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
        """Literal values are directly passed to elasticsearch-dsl"""
        return node

    @handle(values.Geometry)
    def geometry(self, node: values.Geometry):
        """Geometry values are converted to a GeoJSON object"""
        return node.geometry

    @handle(values.Envelope)
    def envelope(self, node: values.Envelope):
        """Envelope values are converted to an GeoJSON Elasticsearch
        extension object."""
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


def to_filter(
    root,
    attribute_map: Optional[Dict[str, str]] = None,
    version: Optional[str] = None,
):
    """Shorthand function to convert a pygeofilter AST to an Elasticsearch
    filter structure.
    """
    return ElasticSearchDSLEvaluator(
        attribute_map, Version(version) if version else None
    ).evaluate(root)
