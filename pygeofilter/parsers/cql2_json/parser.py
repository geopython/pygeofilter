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

from ... import ast
from ... import values
from ... util import parse_datetime, parse_date, parse_duration

# https://github.com/opengeospatial/ogcapi-features/tree/master/cql2


COMPARISON_MAP = {
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

SPATIAL_PREDICATES_MAP = {
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


def walk_cql_json(node: dict) -> ast.Node:
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
        parsed = []
        for value in node['interval']:
            print(value)
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

    # decode all other nodes
    for name, value in node.items():
        if name in ('and', 'or'):
            sub_items = walk_cql_json(value)
            last = sub_items[0]
            for sub_item in sub_items[1:]:
                last = (ast.And if name == 'and' else ast.Or)(
                    last,
                    sub_item,
                )
            return last

        elif name == 'not':
            # allow both arrays and objects, the standard is ambigous in
            # that regard
            if isinstance(value, list):
                value = value[0]
            return ast.Not(walk_cql_json(value))

        elif name in COMPARISON_MAP:
            return COMPARISON_MAP[name](
                walk_cql_json(value[0]),
                walk_cql_json(value[1]),
            )

        elif name == 'between':
            return ast.Between(
                walk_cql_json(value['value']),
                walk_cql_json(value['lower']),
                walk_cql_json(value['upper']),
                not_=False,
            )

        elif name == 'like':
            return ast.Like(
                walk_cql_json(value[0]),
                value[1],
                nocase=False,
                wildcard='%',
                singlechar='.',
                escapechar='\\',
                not_=False,
            )

        elif name == 'in':
            return ast.In(
                walk_cql_json(value['value']),
                walk_cql_json(value['list']),
                not_=False,
            )

        elif name == 'isNull':
            return ast.IsNull(
                walk_cql_json(value),
                not_=False,
            )

        elif name in SPATIAL_PREDICATES_MAP:
            return SPATIAL_PREDICATES_MAP[name](
                walk_cql_json(value[0]),
                walk_cql_json(value[1]),
            )

        elif name in TEMPORAL_PREDICATES_MAP:
            return TEMPORAL_PREDICATES_MAP[name](
                walk_cql_json(value[0]),
                walk_cql_json(value[1]),
            )

        elif name in ARRAY_PREDICATES_MAP:
            return ARRAY_PREDICATES_MAP[name](
                walk_cql_json(value[0]),
                walk_cql_json(value[1]),
            )

        elif name in ARITHMETIC_MAP:
            return ARITHMETIC_MAP[name](
                walk_cql_json(value[0]),
                walk_cql_json(value[1]),
            )

        elif name == 'property':
            return ast.Attribute(value)

        elif name == 'function':
            return ast.Function(
                value['name'],
                walk_cql_json(value['arguments']),
            )


def parse(cql: Union[str, dict]) -> ast.Node:
    if isinstance(cql, str):
        cql = json.loads(cql)

    return walk_cql_json(cql)
