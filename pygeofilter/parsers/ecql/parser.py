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

import logging
import os.path

from lark import Lark, logger, v_args

from ... import ast, values
from ..iso8601 import ISO8601Transformer
from ..wkt import WKTTransformer

logger.setLevel(logging.DEBUG)


SPATIAL_PREDICATES_MAP = {
    "INTERSECTS": ast.GeometryIntersects,
    "DISJOINT": ast.GeometryDisjoint,
    "CONTAINS": ast.GeometryContains,
    "WITHIN": ast.GeometryWithin,
    "TOUCHES": ast.GeometryTouches,
    "CROSSES": ast.GeometryCrosses,
    "OVERLAPS": ast.GeometryOverlaps,
    "EQUALS": ast.GeometryEquals,
}


@v_args(meta=False, inline=True)
class ECQLTransformer(WKTTransformer, ISO8601Transformer):
    def and_(self, lhs, rhs):
        return ast.And(lhs, rhs)

    def or_(self, lhs, rhs):
        return ast.Or(lhs, rhs)

    def not_(self, node):
        return ast.Not(node)

    def eq(self, lhs, rhs):
        return ast.Equal(lhs, rhs)

    def ne(self, lhs, rhs):
        return ast.NotEqual(lhs, rhs)

    def lt(self, lhs, rhs):
        return ast.LessThan(lhs, rhs)

    def lte(self, lhs, rhs):
        return ast.LessEqual(lhs, rhs)

    def gt(self, lhs, rhs):
        return ast.GreaterThan(lhs, rhs)

    def gte(self, lhs, rhs):
        return ast.GreaterEqual(lhs, rhs)

    def between(self, lhs, low, high):
        return ast.Between(lhs, low, high, False)

    def not_between(self, lhs, low, high):
        return ast.Between(lhs, low, high, True)

    def like(self, node, pattern):
        return ast.Like(node, pattern, False, "%", ".", "\\", False)

    def not_like(self, node, pattern):
        return ast.Like(node, pattern, False, "%", ".", "\\", True)

    def ilike(self, node, pattern):
        return ast.Like(node, pattern, True, "%", ".", "\\", False)

    def not_ilike(self, node, pattern):
        return ast.Like(node, pattern, True, "%", ".", "\\", True)

    def in_(self, node, *options):
        return ast.In(node, list(options), False)

    def not_in(self, node, *options):
        return ast.In(node, list(options), True)

    def null(self, node):
        return ast.IsNull(node, False)

    def not_null(self, node):
        return ast.IsNull(node, True)

    def exists(self, attribute):
        return ast.Exists(attribute, False)

    def does_not_exist(self, attribute):
        return ast.Exists(attribute, True)

    def include(self):
        return ast.Include(False)

    def exclude(self):
        return ast.Include(True)

    def before(self, node, dt):
        return ast.TimeBefore(node, dt)

    def before_or_during(self, node, period):
        return ast.TimeBeforeOrDuring(node, period)

    def during(self, node, period):
        return ast.TimeDuring(node, period)

    def during_or_after(self, node, period):
        return ast.TimeDuringOrAfter(node, period)

    def after(self, node, dt):
        return ast.TimeAfter(node, dt)

    def binary_spatial_predicate(self, op, lhs, rhs):
        return SPATIAL_PREDICATES_MAP[op](lhs, rhs)

    def relate_spatial_predicate(self, lhs, rhs, pattern):
        return ast.Relate(lhs, rhs, pattern)

    def distance_spatial_predicate(self, op, lhs, rhs, distance, units):
        cls = ast.DistanceWithin if op == "DWITHIN" else ast.DistanceBeyond
        return cls(lhs, rhs, distance, units)

    def distance_units(self, value):
        return value

    def bbox_spatial_predicate(self, lhs, minx, miny, maxx, maxy, crs=None):
        return ast.BBox(lhs, minx, miny, maxx, maxy, crs)

    def function(self, func_name, *expressions):
        return ast.Function(str(func_name), list(expressions))

    def add(self, lhs, rhs):
        return ast.Add(lhs, rhs)

    def sub(self, lhs, rhs):
        return ast.Sub(lhs, rhs)

    def mul(self, lhs, rhs):
        return ast.Mul(lhs, rhs)

    def div(self, lhs, rhs):
        return ast.Div(lhs, rhs)

    def neg(self, value):
        return -value

    def attribute(self, name):
        return ast.Attribute(str(name))

    def period(self, start, end):
        return values.Interval(start, end)

    def INT(self, value):
        return int(value)

    def FLOAT(self, value):
        return float(value)

    def BOOLEAN(self, value):
        return value.lower() == "true"

    def DOUBLE_QUOTED(self, token):
        return token[1:-1]

    def SINGLE_QUOTED(self, token):
        return token[1:-1]

    def geometry(self, value):
        return values.Geometry(value)

    def envelope(self, x1, x2, y1, y2):
        return values.Envelope(x1, x2, y1, y2)


parser = Lark.open(
    "grammar.lark",
    rel_to=__file__,
    parser="lalr",
    debug=True,
    maybe_placeholders=False,
    transformer=ECQLTransformer(),
    import_paths=[os.path.dirname(os.path.dirname(__file__))],
)


def parse(cql_text):
    return parser.parse(cql_text)
