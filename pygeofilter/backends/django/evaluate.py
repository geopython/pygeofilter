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

import json

from django.contrib.gis.geos import GEOSGeometry, Polygon

from ... import ast, values
from ..evaluator import Evaluator, handle
from . import filters


class DjangoFilterEvaluator(Evaluator):
    def __init__(self, field_mapping, mapping_choices):
        self.field_mapping = field_mapping
        self.mapping_choices = mapping_choices

    @handle(ast.Not)
    def not_(self, node, sub):
        return filters.negate(sub)

    @handle(ast.And, ast.Or)
    def combination(self, node, lhs, rhs):
        return filters.combine((lhs, rhs), node.op.value)

    @handle(ast.Comparison, subclasses=True)
    def comparison(self, node, lhs, rhs):
        return filters.compare(lhs, rhs, node.op.value, self.mapping_choices)

    @handle(ast.Between)
    def between(self, node, lhs, low, high):
        return filters.between(lhs, low, high, node.not_)

    @handle(ast.Like)
    def like(self, node, lhs):
        return filters.like(
            lhs, node.pattern, node.nocase, node.not_, self.mapping_choices
        )

    @handle(ast.In)
    def in_(self, node, lhs, *options):
        return filters.contains(lhs, options, node.not_, self.mapping_choices)

    @handle(ast.IsNull)
    def null(self, node, lhs):
        return filters.null(lhs, node.not_)

    # @handle(ast.ExistsPredicateNode)
    # def exists(self, node, lhs):
    #     if self.use_getattr:
    #         result = hasattr(self.obj, node.lhs.name)
    #     else:
    #         result = lhs in self.obj

    #     if node.not_:
    #         result = not result
    #     return result

    @handle(ast.TemporalPredicate, subclasses=True)
    def temporal(self, node, lhs, rhs):
        return filters.temporal(
            lhs,
            rhs,
            node.op.value,
        )

    @handle(ast.SpatialComparisonPredicate, subclasses=True)
    def spatial_operation(self, node, lhs, rhs):
        return filters.spatial(
            lhs,
            rhs,
            node.op.name,
        )

    @handle(ast.Relate)
    def spatial_pattern(self, node, lhs, rhs):
        return filters.spatial_relate(
            lhs,
            rhs,
            pattern=node.pattern,
        )

    @handle(ast.SpatialDistancePredicate, subclasses=True)
    def spatial_distance(self, node, lhs, rhs):
        return filters.spatial_distance(
            lhs,
            rhs,
            node.op.value,
            distance=node.distance,
            units=node.units,
        )

    @handle(ast.BBox)
    def bbox(self, node, lhs):
        return filters.bbox(lhs, node.minx, node.miny, node.maxx, node.maxy, node.crs)

    @handle(ast.Attribute)
    def attribute(self, node):
        return filters.attribute(node.name, self.field_mapping)

    @handle(ast.Arithmetic, subclasses=True)
    def arithmetic(self, node, lhs, rhs):
        return filters.arithmetic(lhs, rhs, node.op.value)

    # TODO: map functions
    # @handle(ast.FunctionExpressionNode)
    # def function(self, node, *arguments):
    #     return self.function_map[node.name](*arguments)

    @handle(*values.LITERALS)
    def literal(self, node):
        return filters.literal(node)

    @handle(values.Interval)
    def interval(self, node, start, end):
        return filters.literal((start, end))

    @handle(values.Geometry)
    def geometry(self, node):
        return GEOSGeometry(json.dumps(node.__geo_interface__))

    @handle(values.Envelope)
    def envelope(self, node):
        return Polygon.from_bbox((node.x1, node.y1, node.x2, node.y2))


def to_filter(root, field_mapping=None, mapping_choices=None):
    """Helper function to translate ECQL AST to Django Query expressions.

    :param ast: the abstract syntax tree
    :param field_mapping: a dict mapping from the filter name to the Django
                          field lookup.
    :param mapping_choices: a dict mapping field lookups to choices.
    :type ast: :class:`Node`
    :returns: a Django query object
    :rtype: :class:`django.db.models.Q`
    """
    return DjangoFilterEvaluator(field_mapping, mapping_choices).evaluate(root)
