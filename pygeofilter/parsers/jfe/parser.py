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

"""
Parser implementation for JFE. Spec here:
https://github.com/tschaub/ogcapi-features/tree/json-array-expression/extensions/cql/jfe
"""

from datetime import datetime
import json
from typing import Union

from dateparser import parse as parse_datetime

from ... import ast
from ... import values


COMPARISON_MAP = {
    '==': ast.Equal,
    '!=': ast.NotEqual,
    '<': ast.LessThan,
    '<=': ast.LessEqual,
    '>': ast.GreaterThan,
    '>=': ast.GreaterEqual,
}

SPATIAL_PREDICATES_MAP = {
    'intersects': ast.GeometryIntersects,
    'within': ast.GeometryWithin,
}

TEMPORAL_PREDICATES_MAP = {
    'before': ast.TimeBefore,
    'after': ast.TimeAfter,
    'during': ast.TimeDuring,
}

ARITHMETIC_MAP = {
    '+': ast.Add,
    '-': ast.Sub,
    '*': ast.Mul,
    '/': ast.Div,
}

FUNCTION_MAP = {
    '%': 'mod',
    '^': 'pow',
}


def _parse_node(node: Union[list, dict]) -> ast.Node:
    if isinstance(node, (str, float, int)):
        return node
    elif isinstance(node, dict):
        # wrap geometry, we say that the 'type' property defines if it is a
        # geometry
        if 'type' in node:
            return values.Geometry(node)

        # just return objects for example `like` wildcards
        else:
            return node

    if not isinstance(node, list):
        raise ValueError(f'Invalid node class {type(node)}')

    op = node[0]
    arguments = [_parse_node(sub) for sub in node[1:]]

    if op in ['all', 'any']:
        cls = ast.And if op == 'all' else ast.Or
        parent = arguments[0]
        for argument in arguments[1:]:
            parent = cls(parent, argument)
        return parent

    elif op == '!':
        return ast.Not(*arguments)

    elif op in COMPARISON_MAP:
        return COMPARISON_MAP[op](*arguments)

    elif op == 'like':
        wildcard = '%'
        if len(arguments) > 2:
            wildcard = arguments[2].get('wildCard', '%')
        return ast.Like(
            arguments[0],
            arguments[1],
            nocase=False,
            wildcard=wildcard,
            singlechar=None,
            escapechar=None,
            not_=False,
        )

    elif op == 'in':
        return ast.In(arguments[0], arguments[1:], not_=False)

    elif op in SPATIAL_PREDICATES_MAP:
        cls = SPATIAL_PREDICATES_MAP[op]
        return cls(*arguments)

    elif op in TEMPORAL_PREDICATES_MAP:
        cls = TEMPORAL_PREDICATES_MAP[op]

        # parse strings to datetimes
        arguments = [
            parse_datetime(arg) if isinstance(arg, str) else arg
            for arg in arguments
        ]
        if len(arguments) == 3:
            if isinstance(arguments[0], datetime) and \
                    isinstance(arguments[1], datetime):
                arguments = [
                    values.Interval(arguments[0], arguments[1]),
                    arguments[2],
                ]
            if isinstance(arguments[1], datetime) and \
                    isinstance(arguments[2], datetime):
                arguments = [
                    arguments[0],
                    values.Interval(arguments[1], arguments[2]),
                ]

        return cls(*arguments)

    # special property getters
    elif op in ['id', 'geometry']:
        return ast.Attribute(op)

    # normal property getter
    elif op == 'get':
        return ast.Attribute(arguments[0])

    elif op == 'bbox':
        pass  # TODO

    elif op in ARITHMETIC_MAP:
        cls = ARITHMETIC_MAP[op]
        return cls(*arguments)

    elif op in ['%', 'floor', 'ceil', 'abs', '^', 'min', 'max']:
        return ast.Function(FUNCTION_MAP.get(op, op), arguments)

    else:
        raise ValueError(f'Invalid expression operation \'{op}\'')


def parse(jfe: Union[str, list, dict]) -> ast.Node:
    """ Parses the given JFE expression (either a string or an already
        parsed JSON) to an AST.
        If a string is passed, it will be parsed as JSON.

        https://github.com/tschaub/ogcapi-features/tree/json-array-expression/extensions/cql/jfe
    """
    if isinstance(jfe, str):
        jfe = json.loads(jfe)

    return _parse_node(jfe)
