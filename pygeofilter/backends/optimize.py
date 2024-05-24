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

import operator
from datetime import date, datetime, time, timedelta
from typing import Callable, Dict, Optional

import shapely

from .. import ast, values
from ..util import like_pattern_to_re
from .evaluator import Evaluator, handle

COMPARISON_MAP = {
    "=": operator.eq,
    "<>": operator.ne,
    "<": operator.lt,
    "<=": operator.le,
    ">": operator.gt,
    ">=": operator.ge,
}

ARITHMETIC_MAP = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
}


def is_literal(value):
    return isinstance(value, values.LITERALS)


TEMPORAL_LITERALS = (date, datetime, time, timedelta, values.Interval)


def is_temporal_literal(value):
    return isinstance(value, TEMPORAL_LITERALS)


GEOMETRY_LITERALS = (values.Geometry, values.Envelope)


def is_geometry_literal(value):
    return isinstance(value, GEOMETRY_LITERALS)


def is_any_literal(value):
    return is_literal(value) or is_temporal_literal(value) or is_geometry_literal(value)


def to_geometry(value):
    if isinstance(value, values.Geometry):
        return shapely.geometry.shape(value)
    elif isinstance(value, values.Envelope):
        return shapely.geometry.Polygon.from_bounds(
            value.x1, value.y1, value.x2, value.y2
        )
    raise ValueError(str(type(value)))


class OptimizeEvaluator(Evaluator):
    def __init__(self, function_map: Dict[str, Callable]):
        self.function_map = function_map

    @handle(ast.Not)
    def not_(self, node, sub):
        if isinstance(sub, bool):
            return operator.not_(sub)
        else:
            return ast.Not(sub)

    @handle(ast.And, ast.Or)
    def combination(self, node, lhs, rhs):
        if isinstance(lhs, bool) and isinstance(rhs, bool):
            op = operator.and_ if node.op.value == "AND" else operator.or_
            return op(lhs, rhs)

        elif isinstance(lhs, bool) or isinstance(rhs, bool):
            if isinstance(lhs, bool):
                certain, uncertain = lhs, rhs
            else:
                certain, uncertain = rhs, lhs

            # for OR nodes, when we have one true branch, the other
            # can be dropped. Otherwise we can shorthand to the
            # uncertain branch
            if node.op.value == "OR":
                if certain:
                    return True
                else:
                    return uncertain
            # for AND nodes, we can drop the node if the certain one is
            # false. Otherwise we can shorthand to the other
            elif node.op.value == "AND":
                if certain:
                    return uncertain
                else:
                    return False
            # we can eliminate the whole node and its sub-nodes, as it
            # will always evaluate to false
            return False

        else:
            return (ast.And if node.op.value == "AND" else ast.Or)(lhs, rhs)

    @handle(ast.Comparison, subclasses=True)
    def comparison(self, node, lhs, rhs):
        if is_literal(lhs) and is_literal(rhs):
            op = COMPARISON_MAP[node.op.value]
            return op(lhs, rhs)
        else:
            return type(node)(lhs, rhs)

    @handle(ast.Between)
    def between(self, node, lhs, low, high):
        if is_literal(lhs) and is_literal(low) and is_literal(high):
            result = low <= lhs <= high
            if node.not_:
                result = not result
            return result
        else:
            return ast.Between(lhs, low, high, node.not_)

    @handle(ast.Like)
    def like(self, node, lhs):
        if is_literal(lhs):
            regex = like_pattern_to_re(
                node.pattern,
                node.nocase,
                node.wildcard,
                node.singlechar,
                node.escapechar,
            )
            result = regex.match(lhs) is not None
            if node.not_:
                result = not result
            return result
        else:
            return ast.Like(
                lhs,
                node.pattern,
                node.nocase,
                node.wildcard,
                node.singlechar,
                node.escapechar,
                node.not_,
            )

    @handle(ast.In)
    def in_(self, node, lhs, *options):
        if is_literal(lhs) and all(is_literal(o) for o in options):
            result = lhs in options
            if node.not_:
                result = not result
            return result
        else:
            return ast.In(lhs, list(options), node.not_)

    @handle(ast.IsNull)
    def null(self, node, lhs):
        return ast.IsNull(lhs, node.not_)

    @handle(ast.Exists)
    def exists(self, node, lhs):
        return ast.Exists(lhs, node.not_)

    @handle(ast.TemporalPredicate, subclasses=True)
    def temporal(self, node, lhs, rhs):
        if is_temporal_literal(lhs) and is_temporal_literal(rhs):
            lhs = to_interval(lhs)
            rhs = to_interval(rhs)

            return node.op.value == relate_intervals(lhs, rhs)
        else:
            return type(node)(lhs, rhs)

    @handle(ast.ArrayPredicate, subclasses=True)
    def array(self, node, lhs, rhs):
        if isinstance(lhs, list) and isinstance(rhs, list):
            left = set(lhs)
            right = set(rhs)

            if node.op == ast.ArrayComparisonOp.AEQUALS:
                return left == right
            elif node.op == ast.ArrayComparisonOp.ACONTAINS:
                return left >= right
            elif node.op == ast.ArrayComparisonOp.ACONTAINEDBY:
                return left <= right
            elif node.op == ast.ArrayComparisonOp.AOVERLAPS:
                return bool(left & right)
        else:
            return type(node)(lhs, rhs)

    @handle(ast.SpatialComparisonPredicate, subclasses=True)
    def spatial_operation(self, node, lhs, rhs):
        if is_geometry_literal(lhs) and is_geometry_literal(rhs):
            lhs = to_geometry(lhs)
            rhs = to_geometry(rhs)
            op = getattr(lhs, node.op.value.lower())
            return op(rhs)
        else:
            return type(node)(lhs, rhs)

    @handle(ast.Relate)
    def spatial_pattern(self, node, lhs, rhs):
        if is_geometry_literal(lhs) and isinstance(rhs, str):
            lhs = to_geometry(lhs)
            return lhs.relate_pattern(rhs, node.pattern)
        else:
            return ast.Relate(lhs, rhs, node.pattern)

    @handle(ast.SpatialDistancePredicate)
    def distance(self, node, lhs, rhs):
        # TODO: can this be reduced?
        return type(node)(lhs, rhs, node.distance, node.units)

    @handle(ast.BBox)
    def bbox(self, node, lhs):
        if is_geometry_literal(lhs):
            lhs = to_geometry(lhs)
            return lhs.intersects(
                shapely.geometry.Polygon.from_bounds(
                    node.minx, node.miny, node.maxx, node.maxy
                )
            )
        else:
            return ast.BBox(lhs, node.minx, node.miny, node.maxx, node.maxy)

    @handle(ast.Attribute)
    def attribute(self, node):
        return node

    @handle(ast.Arithmetic, subclasses=True)
    def arithmetic(self, node, lhs, rhs):
        if is_literal(lhs) and is_literal(rhs):
            op = ARITHMETIC_MAP[node.op.value]
            return op(lhs, rhs)
        else:
            return type(node)(lhs, rhs)

    @handle(ast.Function)
    def function(self, node, *arguments):
        func = self.function_map.get(node.name)
        if func and all(is_any_literal(a) for a in arguments):
            return func(*arguments)
        else:
            return ast.Function(node.name, list(arguments))

    # just pass through these nodes
    @handle(ast.Attribute, values.Geometry, values.Envelope, *values.LITERALS)
    def literal(self, node):
        return node


def to_interval(value):
    # TODO:
    zulu = None
    if isinstance(value, values.Interval):
        low = value.start
        high = value.end
        if isinstance(low, date):
            low = datetime.combine(low, time.min, zulu)
        if isinstance(high, date):
            high = datetime.combine(high, time.max, zulu)

        if isinstance(low, timedelta):
            low = high - timedelta
        elif isinstance(high, timedelta):
            high = low + timedelta

        return (low, high)

    elif isinstance(value, date):
        return (
            datetime.combine(value, time.min, zulu),
            datetime.combine(value, time.max, zulu),
        )

    elif isinstance(value, datetime):
        return (value, value)

    raise ValueError(f"Invalid type {type(value)}")


def relate_intervals(lhs, rhs):  # noqa: C901
    ll, lh = lhs
    rl, rh = rhs
    if lh < rl:
        return "BEFORE"
    elif ll > rh:
        return "AFTER"
    elif lh == rl:
        return "MEETS"
    elif ll == rh:
        return "METBY"
    elif ll < rl and rl < lh < rh:
        return "TOVERLAPS"
    elif rl < ll < rh and lh > rh:
        return "OVERLAPPEDBY"
    elif ll == rl and lh < rh:
        return "BEGINS"
    elif ll == rl and lh > rh:
        return "BEGUNBY"
    elif ll > rl and lh < rh:
        return "DURING"
    elif ll < rl and lh > rh:
        return "TCONTAINS"
    elif ll > rl and lh == rh:
        return "TENDS"
    elif ll < rl and lh == rh:
        return "ENDEDBY"
    elif ll == rl and lh == rh:
        return "TEQUALS"

    raise ValueError(f"Error relating intervals [{ll}, {lh}] and ({rl}, {rh})")


def optimize(
    root: ast.Node, function_map: Optional[Dict[str, Callable]] = None
) -> ast.Node:
    result = OptimizeEvaluator(function_map or {}).evaluate(root)
    if isinstance(result, bool):
        result = ast.Include(not result)

    return result
