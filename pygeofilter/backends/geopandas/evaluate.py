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

from datetime import date, datetime, time, timedelta

from shapely import geometry

from ... import ast, values
from ..evaluator import Evaluator, handle
from . import filters

LITERALS = (str, float, int, bool, datetime, date, time, timedelta)


class GeoPandasEvaluator(Evaluator):
    def __init__(self, df, field_mapping=None, function_map=None):
        self.df = df
        self.field_mapping = field_mapping
        self.function_map = function_map

    @handle(ast.Not)
    def not_(self, node, sub):
        return filters.negate(sub)

    @handle(ast.And, ast.Or)
    def combination(self, node, lhs, rhs):
        return filters.combine((lhs, rhs), node.op.value)

    @handle(ast.Comparison, subclasses=True)
    def comparison(self, node, lhs, rhs):
        return filters.compare(
            lhs,
            rhs,
            node.op.value,
        )

    @handle(ast.Between)
    def between(self, node, lhs, low, high):
        return filters.between(lhs, low, high, node.not_)

    @handle(ast.Like)
    def like(self, node, lhs):
        return filters.like(
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
        return filters.contains(
            lhs,
            options,
            node.not_,
        )

    @handle(ast.IsNull)
    def null(self, node, lhs):
        return filters.null(
            lhs,
            node.not_,
        )

    @handle(ast.TemporalPredicate, subclasses=True)
    def temporal(self, node, lhs, rhs):
        return filters.temporal(
            node.lhs,
            node.rhs,
            node.op.value,
        )

    @handle(ast.SpatialComparisonPredicate, subclasses=True)
    def spatial_operation(self, node, lhs, rhs):
        return filters.spatial(
            lhs,
            rhs,
            node.op.name,
        )

    @handle(ast.BBox)
    def bbox(self, node, lhs):
        return filters.bbox(lhs, node.minx, node.miny, node.maxx, node.maxy, node.crs)

    @handle(ast.Attribute)
    def attribute(self, node):
        return filters.attribute(self.df, node.name, self.field_mapping)

    @handle(ast.Arithmetic, subclasses=True)
    def arithmetic(self, node, lhs, rhs):
        return filters.arithmetic(lhs, rhs, node.op.value)

    @handle(ast.Function)
    def function(self, node, *arguments):
        return self.function_map[node.name](*arguments)

    @handle(*values.LITERALS)
    def literal(self, node):
        return node

    @handle(values.Interval)
    def interval(self, node, start, end):
        return (start, end)

    @handle(values.Geometry)
    def geometry(self, node):
        return geometry.shape(node)

    @handle(values.Envelope)
    def envelope(self, node):
        return geometry.Polygon.from_bounds(node.x1, node.y1, node.x2, node.y2)


def to_filter(df, root, field_mapping=None, function_map=None):
    """ """
    return GeoPandasEvaluator(df, field_mapping, function_map).evaluate(root)
