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
MongoDB filter evaluator.
"""


# pylint: disable=E1130,C0103,W0223

from dataclasses import dataclass
from functools import wraps
from typing import Dict, Optional

from pygeofilter.util import like_pattern_to_re_pattern

from ..evaluator import Evaluator, handle
from ... import ast
from ... import values


COMPARISON_OP_MAP = {
    ast.ComparisonOp.EQ: "$eq",
    ast.ComparisonOp.NE: "$ne",
    ast.ComparisonOp.LT: "$lt",
    ast.ComparisonOp.LE: "$lte",
    ast.ComparisonOp.GT: "$gt",
    ast.ComparisonOp.GE: "$gte",
}


SWAP_COMPARISON_OP_MAP = {
    ast.ComparisonOp.EQ: ast.Equal,
    ast.ComparisonOp.NE: ast.NotEqual,
    ast.ComparisonOp.LT: ast.GreaterThan,
    ast.ComparisonOp.GT: ast.LessThan,
    ast.ComparisonOp.LE: ast.GreaterEqual,
    ast.ComparisonOp.GE: ast.LessEqual,
}


SPATIAL_COMPARISON_OP_MAP = {
    ast.SpatialComparisonOp.INTERSECTS: "$geoIntersects",
    ast.SpatialComparisonOp.WITHIN: "$geoWithin",
}

SPATIAL_DISTANCE_OP_MAP = {
    ast.SpatialDistanceOp.DWITHIN: "$maxDistance",
    ast.SpatialDistanceOp.BEYOND: "$minDistance",
}

DISTANCE_UNITS_FACTORS = {
    "kilometers": 1000,
    "feet": 0.3048,
    "statute miles": 1609.34,
    "nautical miles": 1852,
    "meters": 1,
}


def to_meters(distance: float, units: str):
    """Returns common distance units to meters"""
    factor = DISTANCE_UNITS_FACTORS[units.lower()]
    return distance * factor


def swap_comparison(node: ast.Comparison, lhs, rhs):
    """Swaps comparison nodes"""
    return SWAP_COMPARISON_OP_MAP[node.op](node.rhs, node.lhs), rhs, lhs


def swap_spatial_comparison(node: ast.SpatialComparisonPredicate, lhs, rhs):
    """Swaps spatial comparison nodes"""
    if node.op == ast.SpatialComparisonOp.INTERSECTS:
        return ast.GeometryIntersects(node.rhs, node.lhs), rhs, lhs

    raise ValueError(f"Cannot swap spatial comparison predicate {node.op}")


def swap_distance_comparison(node: ast.SpatialDistancePredicate, lhs, rhs):
    """Swaps distance comparison nodes"""
    return type(node)(node.rhs, node.lhs, node.distance, node.units), rhs, lhs


def swap_array_comparison(node: ast.ArrayPredicate, lhs, rhs):
    """Swaps array comparison nodes"""
    if node.op == ast.ArrayComparisonOp.AEQUALS:
        return ast.ArrayEquals(node.rhs, node.lhs), rhs, lhs

    raise ValueError(f"Cannot swap array comparison predicate {node.op}")


@dataclass(slots=True)
class AttributeWrapper:
    "Wrapper for attribute access"
    name: str


def ensure_lhs_attribute(swapper=None):
    """Decorator to ensure that the left hand side is always an attribute.
    If a `swapper` is provided, it will swap `lhs` with `rhs`
    """

    def inner(handler):
        @wraps(handler)
        def wrapper(self, node, lhs, *args, **kwargs):
            print(handler, self, node, lhs)
            if isinstance(lhs, AttributeWrapper):
                return handler(self, node, lhs.name, *args, **kwargs)
            if swapper and isinstance(args[0], AttributeWrapper):
                node, lhs, rhs = swapper(node, lhs, args[0].name)
                return handler(self, node, lhs, rhs, *args[1:], **kwargs)
            raise Exception()

        return wrapper

    return inner


class MongoDBEvaluator(Evaluator):
    """A filter evaluator for Elasticsearch DSL."""

    def __init__(
        self,
        attribute_map: Optional[Dict[str, str]] = None,
    ):
        self.attribute_map = attribute_map

    @handle(ast.Not)
    def not_(self, _, sub):
        """Inverts a filter object."""
        return {"$not": sub}

    @handle(ast.And, ast.Or)
    def combination(self, node: ast.Combination, lhs, rhs):
        """Joins two filter objects with an `$and`/`$or` operator."""
        op = "$and" if node.op == ast.CombinationOp.AND else "$or"
        lhs_subs = lhs[op] if op in lhs else [lhs]
        rhs_subs = rhs[op] if op in rhs else [rhs]
        return {op: lhs_subs + rhs_subs}

    @handle(ast.Comparison, subclasses=True)
    @ensure_lhs_attribute(swap_comparison)
    def comparison(self, node: ast.Comparison, lhs, rhs):
        """Creates a comparison filter."""
        return {lhs: {COMPARISON_OP_MAP[node.op]: rhs}}

    @handle(ast.Between)
    @ensure_lhs_attribute()
    def between(self, node: ast.Between, lhs, low, high):
        """Creates an expression with `$lte`/`$gte` for the `between` node."""
        expr = {
            "$lte": high,
            "$gte": low,
        }
        if node.not_:
            expr = self.not_(None, expr)
        return {lhs: expr}

    @handle(ast.Like)
    @ensure_lhs_attribute()
    def like(self, node: ast.Like, lhs):
        """Creates a regex query for a given like filter"""
        re_pattern = like_pattern_to_re_pattern(
            node.pattern, node.wildcard, node.singlechar, node.escapechar
        )
        expr = {"$regex": re_pattern, "$options": "i" if node.nocase else ""}
        if node.not_:
            expr = self.not_(None, expr)
        return {lhs: expr}

    @handle(ast.In)
    @ensure_lhs_attribute()
    def in_(self, node: ast.In, lhs, *options):
        """Creates a `$in`/`$nin` query for the given `in` filter."""
        return {lhs: {"$nin" if node.not_ else "$in": list(options)}}

    @handle(ast.IsNull)
    @ensure_lhs_attribute()
    def null(self, node: ast.IsNull, lhs):
        """Performs a null check, by using the `$type` query on the given
        field.
        """
        expr = {"$type": "null"}
        if node.not_:
            expr = self.not_(None, expr)
        return {lhs: expr}

    @handle(ast.Exists)
    @ensure_lhs_attribute()
    def exists(self, node: ast.Exists, lhs):
        """Performs an existense check, by using the `$exists` query on the
        given field
        """
        return {lhs: {"$exists": not node.not_}}

    # @handle(ast.TemporalPredicate, subclasses=True)
    # def temporal(self, node: ast.TemporalPredicate, lhs, rhs):
    #     """Creates a filter to match the given temporal predicate"""
    #     op = node.op
    #     if isinstance(rhs, (date, datetime)):
    #         low = high = rhs
    #     else:
    #         low, high = rhs

    #     query = "range"
    #     not_ = False
    #     predicate: Dict[str, Union[date, datetime, str]]
    #     if op == ast.TemporalComparisonOp.DISJOINT:
    #         not_ = True
    #         predicate = {"gte": low, "lte": high}
    #     elif op == ast.TemporalComparisonOp.AFTER:
    #         predicate = {"gt": high}
    #     elif op == ast.TemporalComparisonOp.BEFORE:
    #         predicate = {"lt": low}
    #     elif (
    #         op == ast.TemporalComparisonOp.TOVERLAPS
    #         or op == ast.TemporalComparisonOp.OVERLAPPEDBY
    #     ):
    #         predicate = {"gte": low, "lte": high}
    #     elif op == ast.TemporalComparisonOp.BEGINS:
    #         query = "term"
    #         predicate = {"value": low}
    #     elif op == ast.TemporalComparisonOp.BEGUNBY:
    #         query = "term"
    #         predicate = {"value": high}
    #     elif op == ast.TemporalComparisonOp.DURING:
    #         predicate = {"gt": low, "lt": high, "relation": "WITHIN"}
    #     elif op == ast.TemporalComparisonOp.TCONTAINS:
    #         predicate = {"gt": low, "lt": high, "relation": "CONTAINS"}
    #     # elif op == ast.TemporalComparisonOp.ENDS:
    #     #     pass
    #     # elif op == ast.TemporalComparisonOp.ENDEDBY:
    #     #     pass
    #     # elif op == ast.TemporalComparisonOp.TEQUALS:
    #     #     pass
    #     # elif op == ast.TemporalComparisonOp.BEFORE_OR_DURING:
    #     #     pass
    #     # elif op == ast.TemporalComparisonOp.DURING_OR_AFTER:
    #     #     pass
    #     else:
    #         raise NotImplementedError(f"Unsupported temporal operator: {op}")

    #     q = Q(
    #         query,
    #         **{lhs: predicate},
    #     )
    #     if not_:
    #         q = ~q
    #     return q

    @handle(ast.GeometryIntersects, ast.GeometryWithin)
    @ensure_lhs_attribute(swap_spatial_comparison)
    def spatial_comparison(
        self, node: ast.SpatialComparisonPredicate, lhs: str, rhs
    ):
        """Creates a query for the give spatial comparison predicate."""
        return {lhs: {SPATIAL_COMPARISON_OP_MAP[node.op]: {"$geometry": rhs}}}

    @handle(ast.DistanceWithin, ast.DistanceBeyond)
    @ensure_lhs_attribute(swap_distance_comparison)
    def distance(self, node: ast.SpatialDistancePredicate, lhs, rhs):
        """Creates a `$near` query for the given spatial distance
        predicate.
        """
        distance = to_meters(node.distance, node.units)
        return {
            lhs: {
                "$near": {
                    "$geometry": rhs,
                    SPATIAL_DISTANCE_OP_MAP[node.op]: distance,
                }
            }
        }

    @handle(ast.BBox)
    @ensure_lhs_attribute()
    def bbox(self, node: ast.BBox, lhs):
        """Creates a `$geoIntersects` query with the given bbox as
        a `$box`. Ignores the `crs` parameter of the BBox.
        """
        return {
            lhs: {
                "$geoIntersects": {
                    "$geometry": self.envelope(
                        values.Envelope(
                            node.minx, node.maxx, node.miny, node.maxy
                        )
                    )
                }
            }
        }

    @handle(ast.ArrayEquals, ast.ArrayOverlaps, ast.ArrayContains)
    @ensure_lhs_attribute(swap_array_comparison)
    def array(self, node: ast.ArrayPredicate, lhs, rhs):
        """Creates the according query for the given array predicate."""
        if node.op == ast.ArrayComparisonOp.AEQUALS:
            return {lhs: {"$eq": rhs}}
        elif node.op == ast.ArrayComparisonOp.AOVERLAPS:
            return {lhs: {"$in": rhs}}
        elif node.op == ast.ArrayComparisonOp.ACONTAINS:
            return {lhs: {"$all": rhs}}

    @handle(ast.Attribute)
    def attribute(self, node: ast.Attribute):
        """Attribute mapping from filter fields to elasticsearch fields.
        If an attribute mapping is provided, it is used to look up the
        field name from there.
        """
        if self.attribute_map is not None:
            return AttributeWrapper(self.attribute_map[node.name])
        return AttributeWrapper(node.name)

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
        """Literal values are directly passed through"""
        return node

    @handle(values.Geometry)
    def geometry(self, node: values.Geometry):
        """Geometry values are converted to a GeoJSON object"""
        return node.geometry

    @handle(values.Envelope)
    def envelope(self, node: values.Envelope):
        """Envelope values are converted to a $box object."""
        return {
            "type": "Polygon",
            "coordinates": [
                [
                    [node.x1, node.y1],
                    [node.x1, node.y2],
                    [node.x2, node.y2],
                    [node.x2, node.y1],
                    [node.x1, node.y1],
                ]
            ],
        }


def to_filter(root, attribute_map: Optional[Dict[str, str]] = None):
    """Shorthand function to convert a pygeofilter AST to a MongoDB
    filter structure.
    """
    return MongoDBEvaluator(attribute_map).evaluate(root)
