
from datetime import datetime, date, time, timedelta

from . import filters
from ... import ast
from ... import values
from ..evaluator import Evaluator, handle


LITERALS = (str, float, int, bool, datetime, date, time, timedelta)


class SQLAlchemyFilterEvaluator(Evaluator):
    def __init__(self, field_mapping):
        self.field_mapping = field_mapping

    @handle(ast.Not)
    def not_(self, node, sub):
        return filters.negate(sub)

    @handle(ast.And, ast.Or)
    def combination(self, node, lhs, rhs):
        return filters.combine((lhs, rhs), node.op.value)

    @handle(ast.Comparison, subclasses=True)
    def comparison(self, node, lhs, rhs):
        return filters.runop(
            lhs,
            rhs,
            node.op.value,
        )

    @handle(ast.Between)
    def between(self, node, lhs, low, high):
        return filters.between(
            lhs,
            low,
            high,
            node.not_
        )

    @handle(ast.Like)
    def like(self, node, lhs):
        return filters.like(
            lhs,
            node.pattern,
            not node.nocase,
            node.not_,
        )

    @handle(ast.In)
    def in_(self, node, lhs, *options):
        return filters.runop(
            lhs,
            options,
            "in",
            node.not_,
        )

    @handle(ast.IsNull)
    def null(self, node, lhs):
        return filters.runop(
            lhs,
            None,
            "is_null",
            node.not_
        )

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
        return filters.spatial(
            lhs,
            rhs,
            'RELATE',
            pattern=node.pattern,
        )

    @handle(ast.SpatialDistancePredicate, subclasses=True)
    def spatial_distance(self, node, lhs, rhs):
        return filters.spatial(
            lhs,
            rhs,
            node.op.value,
            distance=node.distance,
            units=node.units,
        )

    @handle(ast.BBox)
    def bbox(self, node, lhs):
        return filters.bbox(
            lhs,
            node.minx,
            node.miny,
            node.maxx,
            node.maxy,
            node.crs
        )

    @handle(ast.Attribute)
    def attribute(self, node):
        return filters.attribute(
            node.name,
            self.field_mapping
        )

    @handle(ast.Arithmetic, subclasses=True)
    def arithmetic(self, node, lhs, rhs):
        return filters.runop(
            lhs,
            rhs,
            node.op.value
        )

    # TODO: map functions
    # @handle(ast.FunctionExpressionNode)
    # def function(self, node, *arguments):
    #     return self.function_map[node.name](*arguments)

    @handle(*values.LITERALS)
    def literal(self, node):
        return filters.literal(node)

    @handle(values.Geometry)
    def geometry(self, node):
        return filters.parse_geometry(node.__geo_interface__)

    @handle(values.Envelope)
    def envelope(self, node):
        return filters.parse_bbox([node.x1, node.y1, node.x2, node.y2])


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
    return SQLAlchemyFilterEvaluator(field_mapping).evaluate(ast)
