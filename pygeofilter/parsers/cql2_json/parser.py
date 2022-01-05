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

from datetime import date, datetime, timedelta
from typing import Dict, List, Type, Union, cast
import json

from ... import ast
from ... import values
from ... util import parse_datetime, parse_date, parse_duration

# https://github.com/opengeospatial/ogcapi-features/tree/master/cql2


COMPARISON_MAP: Dict[str, Type[ast.Comparison]] = {
    'eq': ast.Equal,
    '=': ast.Equal,
    'ne': ast.NotEqual,
    '!=': ast.NotEqual,
    'lt': ast.LessThan,
    '<': ast.LessThan,
    'lte': ast.LessEqual,
    '<=': ast.LessEqual,
    'gt': ast.GreaterThan,
    '>': ast.GreaterThan,
    'gte': ast.GreaterEqual,
    '>=': ast.GreaterEqual,
}

SPATIAL_PREDICATES_MAP: Dict[str, Type[ast.SpatialComparisonPredicate]] = {
    's_intersects': ast.GeometryIntersects,
    's_equals': ast.GeometryEquals,
    's_disjoint': ast.GeometryDisjoint,
    's_touches': ast.GeometryTouches,
    's_within': ast.GeometryWithin,
    's_overlaps': ast.GeometryOverlaps,
    's_crosses': ast.GeometryCrosses,
    's_contains': ast.GeometryContains,
}

TEMPORAL_PREDICATES_MAP = {
    't_before': ast.TimeBefore,
    't_after': ast.TimeAfter,
    't_meets': ast.TimeMeets,
    't_metby': ast.TimeMetBy,
    't_overlaps': ast.TimeOverlaps,
    't_overlappedby': ast.TimeOverlappedBy,
    't_begins': ast.TimeBegins,
    't_begunby': ast.TimeBegunBy,
    't_during': ast.TimeDuring,
    't_contains': ast.TimeContains,
    't_ends': ast.TimeEnds,
    't_endedby': ast.TimeEndedBy,
    't_equals': ast.TimeEquals,
}


ARRAY_PREDICATES_MAP = {
    'a_equals': ast.ArrayEquals,
    'a_contains': ast.ArrayContains,
    'a_containedBy': ast.ArrayContainedBy,
    'a_overlaps': ast.ArrayOverlaps,
}

ARITHMETIC_MAP = {
    '+': ast.Add,
    '-': ast.Sub,
    '*': ast.Mul,
    '/': ast.Div,
}


JsonType = Union[dict, list, str, float, int, bool, None]


def walk_cql_json(node: JsonType) -> ast.AstType:
    print(f"NODE: {node} {type(node)}")
    if isinstance(node, (str, float, int, bool)):
        return node

    if isinstance(node, list):
        return [
            walk_cql_json(sub_node)
            for sub_node in node
        ]

    if not isinstance(node, dict):
        raise ValueError(f'Invalid type {type(node)}')

    # check if we are dealing with a geometry
    if 'type' in node and 'coordinates' in node:
        # TODO: test if node is actually valid
        return values.Geometry(node)

    elif 'bbox' in node:
        return values.Envelope(*node['bbox'])

    elif 'date' in node:
        return parse_date(node['date'])

    elif 'timestamp' in node:
        return parse_datetime(node['timestamp'])

    elif 'interval' in node:
        parsed: List[Union[date, datetime, timedelta, None]] = []
        for value in node['interval']:
            if value == '..':
                parsed.append(None)
                continue
            try:
                parsed.append(
                    parse_date(value)
                )
            except ValueError:
                try:
                    parsed.append(parse_duration(value))
                except ValueError:
                    parsed.append(parse_datetime(value))

        return values.Interval(*parsed)
    elif 'op' in node:
        op = node['op']
        args = walk_cql_json(node['args'])

        if op in ('and', 'or'):
            return (ast.And if op == 'and' else ast.Or).from_items(args)

        elif op in COMPARISON_MAP:
            return COMPARISON_MAP[op](
                cast(ast.ScalarAstType, walk_cql_json(args[0])),
                cast(ast.ScalarAstType, walk_cql_json(args[1])),
            )

        elif op == 'not':
            # allow both arrays and objects, the standard is ambigous in
            # that regard
            if isinstance(args, list):
                args = args[0]
            return ast.Not(cast(ast.Node, walk_cql_json(args)))

        elif op in COMPARISON_MAP:
            return COMPARISON_MAP[op](
                cast(ast.ScalarAstType, walk_cql_json(args[0])),
                cast(ast.ScalarAstType, walk_cql_json(args[1])),
            )

        elif op == 'between':
            return ast.Between(
                cast(ast.Node, walk_cql_json(args['args'])),
                cast(ast.ScalarAstType, walk_cql_json(args['lower'])),
                cast(ast.ScalarAstType, walk_cql_json(args['upper'])),
                not_=False,
            )

        elif op == 'like':
            return ast.Like(
                cast(ast.Node, walk_cql_json(args[0])),
                cast(str, args[1]),
                nocase=False,
                wildcard='%',
                singlechar='.',
                escapechar='\\',
                not_=False,
            )

        elif op == 'in':
            return ast.In(
                cast(ast.AstType, walk_cql_json(args['args'])),
                cast(List[ast.AstType], walk_cql_json(args['list'])),
                not_=False,
            )

        elif op == 'isNull':
            return ast.IsNull(
                walk_cql_json(args),
                not_=False,
            )

        elif op in SPATIAL_PREDICATES_MAP:
            return SPATIAL_PREDICATES_MAP[op](
                cast(ast.SpatialAstType, walk_cql_json(args[0])),
                cast(ast.SpatialAstType, walk_cql_json(args[1])),
            )

        elif op in TEMPORAL_PREDICATES_MAP:
            return TEMPORAL_PREDICATES_MAP[op](
                cast(
                    ast.TemporalAstType,
                    walk_cql_json(args[0])
                ),
                cast(
                    ast.TemporalAstType,
                    walk_cql_json(args[1])
                ),
            )

        elif op in ARRAY_PREDICATES_MAP:
            return ARRAY_PREDICATES_MAP[op](
                cast(ast.ArrayAstType, walk_cql_json(args[0])),
                cast(ast.ArrayAstType, walk_cql_json(args[1])),
            )

        elif op in ARITHMETIC_MAP:
            return ARITHMETIC_MAP[op](
                cast(ast.ScalarAstType, walk_cql_json(args[0])),
                cast(ast.ScalarAstType, walk_cql_json(args[1])),
            )

    elif 'property' in node:
        # return ast.Attribute(node['property'])
        return node['property']

    elif 'function' in node:
        return ast.Function(
            node['function']['name'],
            cast(List[ast.AstType], walk_cql_json(node['function']['arguments'])),
        )

    raise ValueError(f'Unable to parse expression node {node!r}')


def parse(cql: Union[str, dict]) -> ast.AstType:
    if isinstance(cql, str):
        root = json.loads(cql)
    else:
        root = cql

    return walk_cql_json(root)
