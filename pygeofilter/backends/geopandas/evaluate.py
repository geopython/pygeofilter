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

from datetime import date, time, datetime, timedelta

from shapely import geometry

from . import filters
from ... import ast
from ...values import Envelope


LITERALS = (str, float, int, bool, datetime, date, time, timedelta)


def is_geometry(node):
    return (
        isinstance(node, dict) and 'type' in node and 'coordinates' in node
    )


class FilterEvaluator:
    def __init__(self, df, field_mapping=None, function_map=None):
        self.df = df
        self.field_mapping = field_mapping
        self.function_map = function_map

    def to_filter(self, node):
        to_filter = self.to_filter
        if isinstance(node, ast.NotConditionNode):
            return filters.negate(to_filter(node.sub_node))
        elif isinstance(node, ast.CombinationConditionNode):
            return filters.combine(
                (to_filter(node.lhs), to_filter(node.rhs)),
                node.op.value,
            )
        elif isinstance(node, ast.ComparisonPredicateNode):
            return filters.compare(
                to_filter(node.lhs),
                to_filter(node.rhs),
                node.op.value,
            )
        elif isinstance(node, ast.BetweenPredicateNode):
            return filters.between(
                to_filter(node.lhs),
                to_filter(node.low),
                to_filter(node.high),
                node.not_
            )
        elif isinstance(node, ast.LikePredicateNode):
            return filters.like(
                to_filter(node.lhs),
                node.pattern,
                node.nocase,
                node.wildcard,
                node.singlechar,
                node.escapechar,
                node.not_,
            )
        elif isinstance(node, ast.InPredicateNode):
            return filters.contains(
                to_filter(node.lhs), [
                    to_filter(sub_node) for sub_node in node.sub_nodes
                ], node.not_,
            )
        elif isinstance(node, ast.NullPredicateNode):
            return filters.null(
                to_filter(node.lhs),
                node.not_
            )
        elif isinstance(node, ast.TemporalPredicateNode):
            return filters.temporal(
                to_filter(node.lhs),
                node.rhs,
                node.op.value,
            )
        elif isinstance(node, ast.SpatialOperationPredicateNode):
            return filters.spatial(
                to_filter(node.lhs),
                to_filter(node.rhs),
                node.op.name,
            )
        # TODO: not possible with geopandas out of the box?
        # elif isinstance(node, ast.SpatialPatternPredicateNode):
        #     return filters.spatial(
        #         to_filter(node.lhs),
        #         to_filter(node.rhs),
        #         'RELATE',
        #         pattern=node.pattern,
        #     )
        # TODO: not possible with geopandas out of the box?
        # elif isinstance(node, ast.SpatialDistancePredicateNode):
        #     return filters.spatial(
        #         to_filter(node.lhs),
        #         to_filter(node.rhs),
        #         node.op.value,
        #         distance=node.distance,
        #         units=node.units,
        #     )
        elif isinstance(node, ast.BBoxPredicateNode):
            return filters.bbox(
                to_filter(node.lhs),
                node.minx,
                node.miny,
                node.maxx,
                node.maxy,
                node.crs
            )
        elif isinstance(node, ast.AttributeExpression):
            return filters.attribute(self.df, node.name, self.field_mapping)

        elif isinstance(node, ast.ArithmeticExpressionNode):
            return filters.arithmetic(
                to_filter(node.lhs),
                to_filter(node.rhs),
                node.op.value
            )

        elif isinstance(node, ast.FunctionExpressionNode):
            return self.function_map[node.name](*[
                to_filter(sub_node)
                for sub_node in node.arguments
            ])

        elif isinstance(node, Envelope):
            return geometry.Polygon.from_bounds(
                node.x1, node.y1, node.x2, node.y2
            )

        elif is_geometry(node):
            return geometry.shape(node)

        elif isinstance(node, LITERALS):
            # return filters.literal(node)
            return node

        else:
            raise Exception(f'Unsupported AST node type {type(node)}')


def to_filter(df, root, field_mapping=None, function_map=None):
    """
    """
    return FilterEvaluator(df, field_mapping, function_map).to_filter(root)
