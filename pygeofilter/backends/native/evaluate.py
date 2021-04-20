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

# import shapely

from ... import ast
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
    def __init__(self, obj, use_getattr=True):
        self.obj = obj
        self.use_getattr = use_getattr

    @handle(ast.NotConditionNode)
    def not_(self, node, sub):
        return operator.not_(sub)

    @handle(ast.CombinationConditionNode)
    def combination(self, node, lhs, rhs):
        op = operator.and_ if node.op.value == 'AND' else operator.or_
        return op(lhs, rhs)

    @handle(ast.ComparisonPredicateNode)
    def comparison(self, node, lhs, rhs):
        op = COMPARISON_MAP[node.op.value]
        print(op, lhs, rhs, op(lhs, rhs))
        return op(lhs, rhs)

    @handle(ast.BetweenPredicateNode)
    def between(self, node, lhs, low, high):
        return low <= lhs <= high

    @handle(ast.LikePredicateNode)
    def like(self, node, lhs):
        regex = like_pattern_to_re(
            node.pattern,
            node.nocase,
            node.wildcard,
            node.single_char,
            node.escape_char
        )
        return regex.match(node) is not None

    @handle(ast.InPredicateNode)
    def in_(self, node, lhs, options):
        return lhs in options

    @handle(ast.NullPredicateNode)
    def null(self, node, lhs):
        return lhs is None

    @handle(ast.TemporalPredicateNode)
    def temporal(self, node, lhs, rhs):
        raise NotImplementedError

    # @handle(ast.SpatialOperationPredicateNode)
    # def handle_spatial_operation(self, node, lhs, rhs):
    #     op = operator.and_ if node.op == 'AND' else operator.or_
    #     return op(lhs, rhs)

    # @handle(ast.SpatialPatternPredicateNode)
    # def handle_spatial_pattern(self, node, lhs, rhs):
    #     pass

    # @handle(ast.SpatialDistancePredicateNode)
    # def handle__(self, node, lhs, rhs):
    #     pass

    # @handle(ast.BBoxPredicateNode)
    # def handle__(self, node, lhs, rhs):
    #     pass

    @handle(ast.AttributeExpression)
    def attribute(self, node):
        if self.use_getattr:
            return getattr(self.obj, node.name)
        else:
            return self.obj[node.name]

    @handle(ast.ArithmeticExpressionNode)
    def arithmetic(self, node, lhs, rhs):
        op = ARITHMETIC_MAP[node.op.value]
        return op(lhs, rhs)

    @handle(str, float, int, bool, datetime, date, time, timedelta)
    def literal(self, node):
        return node

    # @handle(ast.Envelope)
    # def handle__(self, node, lhs, rhs):
    #     pass






# class FilterEvaluator:
#     def __init__(self, functions=None):
#         self.functions = functions or {}

#     def to_filter(self, node):
#         to_filter = self.to_filter
#         if isinstance(node, ast.NotConditionNode):
#             return operator.not_(to_filter(node.sub_node))
#         elif isinstance(node, ast.CombinationConditionNode):
#             op = operator.and_ if node.op == 'AND' else operator.or_
#             return op(to_filter(node.lhs), to_filter(node.rhs))
#         elif isinstance(node, ast.ComparisonPredicateNode):
#             op = COMPARISON_MAP[node.op]
#             return op(to_filter(node.lhs), to_filter(node.rhs))
#         elif isinstance(node, ast.BetweenPredicateNode):
#             value = (
#                 to_filter(node.low) <= to_filter(node.lhs) <= to_filter(node.high)
#             )
#             return not value if node.not_ else value
#         elif isinstance(node, ast.LikePredicateNode):
#             escape_char = r'\%' if sys.version_info < (3, 7) else '%'
#             pattern = f"^{re.escape(node.pattern).replace(escape_char, '.*')}$"
#             flags = 0
#             if not node.case:
#                 flags = re.I
#             return re.match(pattern, to_filter(node.rhs), flags=flags) is not None
#         elif isinstance(node, ast.InPredicateNode):
#             value = to_filter(node.lhs) in [
#                 to_filter(sub_node)
#                 for sub_node in node.sub_nodes
#             ]
#             return not value if node.not_ else value
#         elif isinstance(node, ast.NullPredicateNode):
#             if node.not_:
#                 return to_filter(node.lhs) is not None
#             return to_filter(node.lhs) is None
#         elif isinstance(node, ast.TemporalPredicateNode):
#             # TODO: implement
#             pass
#         elif isinstance(node, ast.SpatialPredicateNode):
#             return filters.spatial(
#                 to_filter(node.lhs), to_filter(node.rhs), node.op,
#                 to_filter(node.pattern),
#                 to_filter(node.distance),
#                 to_filter(node.units)
#             )
#         elif isinstance(node, ast.BBoxPredicateNode):
#             return filters.bbox(
#                 to_filter(node.lhs),
#                 to_filter(node.minx),
#                 to_filter(node.miny),
#                 to_filter(node.maxx),
#                 to_filter(node.maxy),
#                 to_filter(node.crs)
#             )
#         elif isinstance(node, ast.AttributeExpression):
#             return filters.attribute(node.name, self.field_mapping)

#         elif isinstance(node, (str, float, int, datetime, date, time, timedelta)):
#             return node.value

#         elif isinstance(node, ast.ArithmeticExpressionNode):
#             op = ARITHMETIC_MAP[node.op]
#             return op(to_filter(node.lhs), to_filter(node.rhs))

#         elif isinstance(node, ast.FunctionExpressionNode):
#             function = self.functions[node.name]
#             return function(*[
#                 to_filter(sub_node)
#                 for sub_node in node.get_sub_nodes()
#             ])

#         return node


# def to_filter(ast, field_mapping=None, mapping_choices=None):
#     """ Helper function to translate ECQL AST to Django Query expressions.

#         :param ast: the abstract syntax tree
#         :param field_mapping: a dict mapping from the filter name to the Django
#                               field lookup.
#         :param mapping_choices: a dict mapping field lookups to choices.
#         :type ast: :class:`Node`
#         :returns: a Django query object
#         :rtype: :class:`django.db.models.Q`
#     """
#     return FilterEvaluator(field_mapping, mapping_choices).to_filter(ast)
