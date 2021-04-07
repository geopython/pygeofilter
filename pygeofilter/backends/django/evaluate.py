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
# The above copyright notice and this permission notice shall be included in all
# copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# ------------------------------------------------------------------------------


from . import filters
from ...parser import parse
from ...ast import (
    NotConditionNode, CombinationConditionNode, ComparisonPredicateNode,
    BetweenPredicateNode, BetweenPredicateNode, LikePredicateNode,
    InPredicateNode, NullPredicateNode, TemporalPredicateNode,
    SpatialPredicateNode, BBoxPredicateNode, AttributeExpression,
    LiteralExpression, ArithmeticExpressionNode,
)


class FilterEvaluator:
    def __init__(self, field_mapping=None, mapping_choices=None):
        self.field_mapping = field_mapping
        self.mapping_choices = mapping_choices

    def to_filter(self, node):
        to_filter = self.to_filter
        if isinstance(node, NotConditionNode):
            return filters.negate(to_filter(node.sub_node))
        elif isinstance(node, CombinationConditionNode):
            return filters.combine(
                (to_filter(node.lhs), to_filter(node.rhs)), node.op
            )
        elif isinstance(node, ComparisonPredicateNode):
            return filters.compare(
                to_filter(node.lhs), to_filter(node.rhs), node.op,
                self.mapping_choices
            )
        elif isinstance(node, BetweenPredicateNode):
            return filters.between(
                to_filter(node.lhs), to_filter(node.low), to_filter(node.high),
                node.not_
            )
        elif isinstance(node, BetweenPredicateNode):
            return filters.between(
                to_filter(node.lhs), to_filter(node.low), to_filter(node.high),
                node.not_
            )
        elif isinstance(node, LikePredicateNode):
            return filters.like(
                to_filter(node.lhs), to_filter(node.rhs), node.case, node.not_,
                self.mapping_choices

            )
        elif isinstance(node, InPredicateNode):
            return filters.contains(
                to_filter(node.lhs), [
                    to_filter(sub_node) for sub_node in node.sub_nodes
                ], node.not_, self.mapping_choices
            )
        elif isinstance(node, NullPredicateNode):
            return filters.null(
                to_filter(node.lhs), node.not_
            )
        elif isinstance(node, TemporalPredicateNode):
            return filters.temporal(
                to_filter(node.lhs), node.rhs, node.op
            )
        elif isinstance(node, SpatialPredicateNode):
            return filters.spatial(
                to_filter(node.lhs), to_filter(node.rhs), node.op,
                to_filter(node.pattern),
                to_filter(node.distance),
                to_filter(node.units)
            )
        elif isinstance(node, BBoxPredicateNode):
            return filters.bbox(
                to_filter(node.lhs),
                to_filter(node.minx),
                to_filter(node.miny),
                to_filter(node.maxx),
                to_filter(node.maxy),
                to_filter(node.crs)
            )
        elif isinstance(node, AttributeExpression):
            return filters.attribute(node.name, self.field_mapping)

        elif isinstance(node, LiteralExpression):
            return node.value

        elif isinstance(node, ArithmeticExpressionNode):
            return filters.arithmetic(
                to_filter(node.lhs), to_filter(node.rhs), node.op
            )

        return node


def to_filter(ast, field_mapping=None, mapping_choices=None):
    """ Helper function to translate ECQL AST to Django Query expressions.

        :param ast: the abstract syntax tree
        :param field_mapping: a dict mapping from the filter name to the Django
                              field lookup.
        :param mapping_choices: a dict mapping field lookups to choices.
        :type ast: :class:`Node`
        :returns: a Django query object
        :rtype: :class:`django.db.models.Q`
    """
    return FilterEvaluator(field_mapping, mapping_choices).to_filter(ast)
