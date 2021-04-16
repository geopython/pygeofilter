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

from typing import Union
import json

import pygeoif
from dateparser import parse as parse_datetime

from ...util import parse_duration
from ...values import Envelope
from ... import ast

# https://portal.ogc.org/files/96288


COMPARISON_OP_MAP = {
    'eq': ast.ComparisonOp.EQ,
    'lt': ast.ComparisonOp.LT,
    'gt': ast.ComparisonOp.GT,
    'lte': ast.ComparisonOp.LE,
    'gte': ast.ComparisonOp.GE,
}

SPATIAL_PREDICATES = {
    'intersects', 'equals', 'disjoint', 'touches', 'within', 'overlaps',
    'crosses', 'contains'
}

TEMPORAL_PREDICATES = {
    'before', 'after', 'meets', 'metby', 'toverlaps', 'overlappedby',
    'begins', 'begunby', 'during', 'tcontains', 'ends', 'endedby',
    'tequals', 'anyinteract'
}


def walk_cql_json(node: dict, is_temporal: bool = False) -> ast.Node:
    if is_temporal and isinstance(node, str):
        # Open interval
        if node == '..':
            return None

        try:
            return parse_duration(node)
        except ValueError:
            value = parse_datetime(node)

        if value is None:
            raise ValueError(f'Failed to parse temporal value from {node}')

        return value

    if isinstance(node, (str, float, int, bool)):
        return node

    if isinstance(node, list):
        return [
            walk_cql_json(sub_node, is_temporal)
            for sub_node in node
        ]

    assert isinstance(node, dict)

    # check if we are dealing with a geometry
    if 'type' in node and 'coordinates' in node:
        # TODO: test if node is actually valid
        return node

    elif 'bbox' in node:
        return Envelope(*node['bbox'])

    # decode all other nodes
    for name, value in node.items():
        if name in ('and', 'or'):
            op = ast.CombinationOp(name.upper())
            sub_items = walk_cql_json(value)
            last = sub_items[0]
            for sub_item in sub_items[1:]:
                last = ast.CombinationConditionNode(
                    last,
                    sub_item,
                    op=op
                )
            return last

        elif name == 'not':
            # allow both arrays and objects, the standard is ambigous in
            # that regard
            if isinstance(value, list):
                value = value[0]
            return ast.NotConditionNode(walk_cql_json(value))

        elif name in ('eq', 'lt', 'gt', 'lte', 'gte'):
            op = COMPARISON_OP_MAP[name]
            return ast.ComparisonPredicateNode(
                walk_cql_json(value[0]),
                walk_cql_json(value[1]),
                op,
            )

        elif name == 'between':
            return ast.BetweenPredicateNode(
                walk_cql_json(value['value']),
                walk_cql_json(value['lower']),
                walk_cql_json(value['upper']),
                not_=False,
            )

        elif name == 'like':
            return ast.LikePredicateNode(
                walk_cql_json(value['like'][0]),
                value['like'][1],
                nocase=value.get('nocase', True),
                wildcard=value.get('wildcard', '%'),
                singlechar=value.get('singleChar', '.'),
                escapechar=value.get('escapeChar', '\\'),
                not_=False,
            )

        elif name == 'in':
            return ast.InPredicateNode(
                walk_cql_json(value['value']),
                walk_cql_json(value['list']),
                not_=False,
                # TODO nocase
            )

        elif name == 'isNull':
            return ast.NullPredicateNode(
                walk_cql_json(value),
                not_=False,
            )

        elif name in SPATIAL_PREDICATES:
            return ast.SpatialOperationPredicateNode(
                walk_cql_json(value[0]),
                walk_cql_json(value[1]),
                op=ast.SpatialComparisonOp(name.upper()),
            )

        elif name in TEMPORAL_PREDICATES:
            return ast.TemporalPredicateNode(
                walk_cql_json(value[0], is_temporal=True),
                walk_cql_json(value[1], is_temporal=True),
                op=ast.TemporalComparisonOp(name.upper()),
            )

        # TODO: array predicates

        elif name in ('+', '-', '*', '/'):
            return ast.ArithmeticExpressionNode(
                walk_cql_json(value[0]),
                walk_cql_json(value[1]),
                op=ast.ArithmeticOp(name),
            )

        elif name == 'property':
            return ast.AttributeExpression(value)

        elif name == 'function':
            return ast.FunctionExpressionNode(
                value['name'],
                walk_cql_json(value['arguments']),
            )


def parse(cql: Union[str, dict]) -> ast.Node:
    if isinstance(cql, str):
        cql = json.loads(cql)

    return walk_cql_json(cql)
