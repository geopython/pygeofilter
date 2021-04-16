
from datetime import datetime, date, time, timedelta

from . import filters
from ... import ast
from ...values import Envelope


LITERALS = (str, float, int, bool, datetime, date, time, timedelta)


def is_geometry(node):
    return (
        isinstance(node, dict) and 'type' in node and 'coordinates' in node
    )


class FilterEvaluator:
    def __init__(self, field_mapping=None):
        self.field_mapping = field_mapping

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
            return filters.runop(
                to_filter(node.lhs),
                to_filter(node.rhs),
                node.op.value,
            )

        elif isinstance(node, ast.BetweenPredicateNode):
            return filters.between(
                to_filter(node.lhs),
                to_filter(node.low),
                to_filter(node.high),
                node.not_,
            )

        elif isinstance(node, ast.LikePredicateNode):
            return filters.like(
                to_filter(node.lhs),
                node.pattern,
                not node.nocase,
                node.not_,
            )

        elif isinstance(node, ast.InPredicateNode):
            return filters.runop(
                to_filter(node.lhs),
                [to_filter(sub_node) for sub_node in node.sub_nodes],
                "in",
                node.not_,
            )

        elif isinstance(node, ast.NullPredicateNode):
            return filters.runop(
                to_filter(node.lhs),
                None,
                "is_null",
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
                node.op.value,
            )

        elif isinstance(node, ast.SpatialPatternPredicateNode):
            return filters.spatial(
                to_filter(node.lhs),
                to_filter(node.rhs),
                node.op.value,
                pattern=node.pattern,
            )

        elif isinstance(node, ast.SpatialDistancePredicateNode):
            return filters.spatial(
                to_filter(node.lhs),
                to_filter(node.rhs),
                node.op.value,
                distance=node.distance,
                units=node.units,
            )

        elif isinstance(node, ast.BBoxPredicateNode):
            return filters.bbox(
                to_filter(node.lhs),
                to_filter(node.minx),
                to_filter(node.miny),
                to_filter(node.maxx),
                to_filter(node.maxy),
                node.crs,
            )
        elif isinstance(node, ast.AttributeExpression):
            return filters.attribute(
                node.name,
                self.field_mapping
            )

        elif isinstance(node, ast.ArithmeticExpressionNode):
            return filters.runop(
                to_filter(node.lhs),
                to_filter(node.rhs),
                node.op.value,
            )

        elif isinstance(node, Envelope):
            return filters.parse_bbox([node.x1, node.y1, node.x2, node.y2])

        elif is_geometry(node):
            return filters.parse_geometry(node)

        elif isinstance(node, LITERALS):
            return filters.literal(node)

        else:
            raise Exception(f'Unsupported AST node type {type(node)}')

        return node


def to_filter(ast, field_mapping=None):
    """ Helper function to translate ECQL AST to Django Query expressions.

        :param ast: the abstract syntax tree
        :param field_mapping: a dict mapping from the filter name to the Django
                              field lookup.
        :param mapping_choices: a dict mapping field lookups to choices.
        :type ast: :class:`Node`
        :returns: a Django query object
        :rtype: :class:`django.db.models.Q`
    """
    return FilterEvaluator(field_mapping).to_filter(ast)
