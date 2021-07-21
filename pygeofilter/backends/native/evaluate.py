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


from datetime import date, time, datetime, timedelta

import shapely

from ... import ast
from ... import values
from ...util import like_pattern_to_re

from ..evaluator import Evaluator, handle


COMPARISON_MAP = {
    ast.ComparisonOp.EQ: '==',
    ast.ComparisonOp.NE: '!=',
    ast.ComparisonOp.LT: '<',
    ast.ComparisonOp.LE: '<=',
    ast.ComparisonOp.GT: '>',
    ast.ComparisonOp.GE: '>=',
}

ARITHMETIC_MAP = {
    ast.ArithmeticOp.ADD: '+',
    ast.ArithmeticOp.SUB: '-',
    ast.ArithmeticOp.MUL: '*',
    ast.ArithmeticOp.DIV: '/',
}


class NativeEvaluator(Evaluator):
    def __init__(self, function_map=None, use_getattr=True):
        self.function_map = function_map if function_map is not None else {}
        self.use_getattr = use_getattr
        self.locals = {}
        self.local_count = 0

    def _add_local(self, value) -> str:
        self.local_count += 1
        key = f'local_{self.local_count}'
        self.locals[key] = value
        return key

    @handle(ast.Not)
    def not_(self, node, sub):
        return f'not ({sub})'

    @handle(ast.And)
    def and_(self, node, lhs, rhs):
        return f'({lhs}) and ({rhs})'

    @handle(ast.Or)
    def or_(self, node, lhs, rhs):
        return f'({lhs}) or ({rhs})'

    @handle(ast.Comparison, subclasses=True)
    def comparison(self, node, lhs, rhs):
        op = COMPARISON_MAP[node.op]
        return f'({lhs}) {op} ({rhs})'

    @handle(ast.Between)
    def between(self, node, lhs, low, high):
        maybe_not = "not " if node.not_ else ""
        return f'{maybe_not}({low}) <= ({lhs}) <= ({high})'

    @handle(ast.Like)
    def like(self, node, lhs):
        maybe_not_inv = "" if node.not_ else "not "
        regex = like_pattern_to_re(
            node.pattern,
            node.nocase,
            node.wildcard,
            node.singlechar,
            node.escapechar
        )
        key = self._add_local(regex)
        return f'{key}.match({lhs}) is {maybe_not_inv} None'

    @handle(ast.In)
    def in_(self, node, lhs, *options):
        maybe_not = 'not' if node.not_ else ''
        opts = ', '.join([
            f'({opt})' for opt in options
        ])
        return f'({lhs}) {maybe_not} in ({opts})'

    @handle(ast.IsNull)
    def null(self, node, lhs):
        maybe_not = 'not ' if node.not_ else ''
        return f'({lhs}) is {maybe_not}None'

    @handle(ast.Exists)
    def exists(self, node, lhs):
        maybe_not = 'not ' if node.not_ else ''
        if self.use_getattr:
            return f'{maybe_not}hasattr(item, "{node.lhs.name}")'
        else:
            return f'"{node.lhs.name}" {maybe_not}in item'

    @handle(ast.TemporalPredicate, subclasses=True)
    def temporal(self, node, lhs, rhs):
        return (
            f'relate_intervals(to_interval({lhs}),'
            f'to_interval({rhs})) == "{node.op.value}"'
        )

    @handle(ast.ArrayPredicate, subclasses=True)
    def array(self, node, lhs, rhs):
        if node.op == ast.ArrayComparisonOp.AEQUALS:
            op = '=='
        elif node.op == ast.ArrayComparisonOp.ACONTAINS:
            op = '>='
        elif node.op == ast.ArrayComparisonOp.ACONTAINEDBY:
            op = '<='
        elif node.op == ast.ArrayComparisonOp.AOVERLAPS:
            op = '&'
        return f'bool(set({lhs}) {op} set({rhs}))'

    @handle(ast.SpatialComparisonPredicate, subclasses=True)
    def spatial_operation(self, node, lhs, rhs):
        return f'getattr({lhs}, "{node.op.value.lower()}")({rhs})'

    @handle(ast.Relate)
    def spatial_pattern(self, node, lhs, rhs):
        return f'({lhs}).relate_pattern(({rhs}), {node.pattern})'

    @handle(ast.BBox)
    def bbox(self, node, lhs):
        return (
            f'({lhs}).intersects(shapely.geometry.Polygon.from_bounds('
            f'{node.minx}, {node.miny}, {node.maxx}, {node.maxy}))'
        )

    @handle(ast.Attribute)
    def attribute(self, node):
        # TODO: nested lookup here?
        if self.use_getattr:
            return f'getattr(item, "{node.name}", None)'
        else:
            return f'item.get("{node.name}")'

    @handle(ast.Arithmetic, subclasses=True)
    def arithmetic(self, node, lhs, rhs):
        op = ARITHMETIC_MAP[node.op]
        return f'({lhs}) {op} ({rhs})'

    @handle(ast.Function)
    def function(self, node, *arguments):
        args = ', '.join([
            f'({arg})' for arg in arguments
        ])
        return f'{node.name}({args})'

    @handle(*values.LITERALS)
    def literal(self, node):
        key = self._add_local(node)
        return key

    @handle(values.Interval)
    def interval(self, node):
        key = self._add_local(node)
        return key

    @handle(values.Geometry)
    def geometry(self, node):
        key = self._add_local(shapely.geometry.shape(node))
        return key

    @handle(values.Envelope)
    def envelope(self, node):
        key = self._add_local(
            shapely.geometry.Polygon.from_bounds(
                node.x1, node.y1, node.x2, node.y2
            )
        )
        return key

    def adopt_result(self, result):
        expression = f'lambda item: {result}'
        print(expression, self.locals)
        globals_ = {
            "relate_intervals": relate_intervals,
            "to_interval": to_interval,
        }
        assert set(globals_).isdisjoint(set(self.function_map))

        globals_.update(self.function_map)
        globals_.update(self.locals)

        return eval(expression, globals_)


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
