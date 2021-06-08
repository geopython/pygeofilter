# ------------------------------------------------------------------------------
#
# Project: pygeofilter <https://github.com/geopython/pygeofilter>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2019 EOX IT Services GmbH
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
from datetime import date, time, datetime, timedelta

import shapely

from ... import ast
from ... import values
from ...util import like_pattern_to_re

from ..evaluator import Evaluator, handle


COMPARISON_MAP = {
    '=': operator.eq,
    '<>': operator.ne,
    '<': operator.lt,
    '<=': operator.le,
    '>': operator.gt,
    '>=': operator.ge,
}

ARITHMETIC_MAP = {
    '+': operator.add,
    '-': operator.sub,
    '*': operator.mul,
    '/': operator.truediv,
}


class NativeEvaluator(Evaluator):
    def __init__(self, obj, function_map=None, use_getattr=True):
        self.obj = obj
        self.function_map = function_map if function_map is not None else {}
        self.use_getattr = use_getattr

    @handle(ast.Not)
    def not_(self, node, sub):
        return operator.not_(sub)

    @handle(ast.And, ast.Or)
    def combination(self, node, lhs, rhs):
        op = operator.and_ if node.op.value == 'AND' else operator.or_
        return op(lhs, rhs)

    @handle(ast.Comparison, subclasses=True)
    def comparison(self, node, lhs, rhs):
        op = COMPARISON_MAP[node.op.value]
        print(op, lhs, rhs, op(lhs, rhs))
        return op(lhs, rhs)

    @handle(ast.Between)
    def between(self, node, lhs, low, high):
        result = low <= lhs <= high
        if node.not_:
            result = not result
        return result

    @handle(ast.Like)
    def like(self, node, lhs):
        regex = like_pattern_to_re(
            node.pattern,
            node.nocase,
            node.wildcard,
            node.singlechar,
            node.escapechar
        )
        result = regex.match(lhs) is not None
        if node.not_:
            result = not result
        return result

    @handle(ast.In)
    def in_(self, node, lhs, *options):
        result = lhs in options
        if node.not_:
            result = not result
        return result

    @handle(ast.IsNull)
    def null(self, node, lhs):
        result = lhs is None
        if node.not_:
            result = not result
        return result

    @handle(ast.Exists)
    def exists(self, node, lhs):
        if self.use_getattr:
            result = hasattr(self.obj, node.lhs.name)
        else:
            result = lhs in self.obj

        if node.not_:
            result = not result
        return result

    @handle(ast.TemporalPredicate, subclasses=True)
    def temporal(self, node, lhs, rhs):
        lhs = to_interval(lhs)
        rhs = to_interval(rhs)

        return node.op.value == relate_intervals(lhs, rhs)

    @handle(ast.ArrayPredicate, subclasses=True)
    def array(self, node, lhs, rhs):
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

    @handle(ast.SpatialComparisonPredicate, subclasses=True)
    def spatial_operation(self, node, lhs, rhs):
        op = getattr(lhs, node.op.value.lower())
        return op(rhs)

    @handle(ast.Relate)
    def spatial_pattern(self, node, lhs, rhs):
        return lhs.relate_pattern(rhs, node.pattern)

    # @handle(ast.SpatialDistancePredicateNode)
    # def handle__(self, node, lhs, rhs):
    #     pass

    @handle(ast.BBox)
    def bbox(self, node, lhs):
        return lhs.intersects(
            shapely.geometry.Polygon.from_bounds(
                node.minx, node.miny, node.maxx, node.maxy
            )
        )

    @handle(ast.Attribute)
    def attribute(self, node):
        if self.use_getattr:
            return getattr(self.obj, node.name, None)
        else:
            return self.obj.get(node.name)

    @handle(ast.Arithmetic, subclasses=True)
    def arithmetic(self, node, lhs, rhs):
        op = ARITHMETIC_MAP[node.op.value]
        return op(lhs, rhs)

    @handle(ast.Function)
    def function(self, node, *arguments):
        return self.function_map[node.name](*arguments)

    @handle(*values.LITERALS)
    def literal(self, node):
        return node

    @handle(values.Geometry)
    def geometry(self, node):
        return shapely.geometry.shape(node)

    @handle(values.Envelope)
    def envelope(self, node):
        return shapely.geometry.Polygon.from_bounds(
            node.x1, node.y1, node.x2, node.y2
        )


def to_interval(value):
    # TODO:
    zulu = None
    if isinstance(value, (list, tuple)):
        low, high = value
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

    raise ValueError(f'Invalid type {type(value)}')


def relate_intervals(lhs, rhs):
    ll, lh = lhs
    rl, rh = rhs
    if lh < rl:
        return 'BEFORE'
    elif ll > rh:
        return 'AFTER'
    elif lh == rl:
        return 'MEETS'
    elif ll == rh:
        return 'METBY'
    elif ll < rl and rl < lh < rh:
        return 'TOVERLAPS'
    elif rl < ll < rh and lh > rh:
        return 'OVERLAPPEDBY'
    elif ll == rl and lh < rh:
        return 'BEGINS'
    elif ll == rl and lh > rh:
        return 'BEGUNBY'
    elif ll > rl and lh < rh:
        return 'DURING'
    elif ll < rl and lh > rh:
        return 'TCONTAINS'
    elif ll > rl and lh == rh:
        return 'TENDS'
    elif ll < rl and lh == rh:
        return 'ENDEDBY'
    elif ll == rl and lh == rh:
        return 'TEQUALS'

    raise ValueError(
        f'Error relating intervals [{ll}, {lh}] and ({rl}, {rh})'
    )
