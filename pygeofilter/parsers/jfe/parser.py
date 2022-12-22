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

import json
from datetime import datetime
from typing import Any, Dict, List, Type, Union, cast

from ... import ast, values
from ...util import parse_datetime

COMPARISON_MAP: Dict[str, Type] = {
    "==": ast.Equal,
    "!=": ast.NotEqual,
    "<": ast.LessThan,
    "<=": ast.LessEqual,
    ">": ast.GreaterThan,
    ">=": ast.GreaterEqual,
}

SPATIAL_PREDICATES_MAP = {
    "intersects": ast.GeometryIntersects,
    "within": ast.GeometryWithin,
}

TEMPORAL_PREDICATES_MAP = {
    "before": ast.TimeBefore,
    "after": ast.TimeAfter,
    "during": ast.TimeDuring,
}

ARITHMETIC_MAP = {
    "+": ast.Add,
    "-": ast.Sub,
    "*": ast.Mul,
    "/": ast.Div,
}

FUNCTION_MAP = {
    "%": "mod",
    "^": "pow",
}

ParseResult = Union[
    ast.Node,
    str,
    float,
    int,
    datetime,
    values.Geometry,
    values.Interval,
    Dict[Any, Any],  # TODO: for like wildcards.
]


def _parse_node(node: Union[list, dict]) -> ParseResult:  # noqa: C901
    if isinstance(node, (str, float, int)):
        return node
    elif isinstance(node, dict):
        # wrap geometry, we say that the 'type' property defines if it is a
        # geometry
        if "type" in node:
            return values.Geometry(node)

        # just return objects for example `like` wildcards
        else:
            return node

    if not isinstance(node, list):
        raise ValueError(f"Invalid node class {type(node)}")

    op = node[0]
    arguments = [_parse_node(sub) for sub in node[1:]]

    if op in ["all", "any"]:
        cls = ast.And if op == "all" else ast.Or
        return cls.from_items(*arguments)

    elif op == "!":
        return ast.Not(*cast(List[ast.Node], arguments))

    elif op in COMPARISON_MAP:
        return COMPARISON_MAP[op](*arguments)

    elif op == "like":
        wildcard = "%"
        if len(arguments) > 2:
            wildcard = cast(dict, arguments[2]).get("wildCard", "%")
        return ast.Like(
            cast(ast.Node, arguments[0]),
            cast(str, arguments[1]),
            nocase=False,
            wildcard=wildcard,
            singlechar=".",
            escapechar="\\",
            not_=False,
        )

    elif op == "in":
        assert isinstance(arguments[0], ast.Node)
        return ast.In(
            cast(ast.Node, arguments[0]),
            cast(List[ast.AstType], arguments[1:]),
            not_=False,
        )

    elif op in SPATIAL_PREDICATES_MAP:
        return SPATIAL_PREDICATES_MAP[op](*cast(List[ast.SpatialAstType], arguments))

    elif op in TEMPORAL_PREDICATES_MAP:
        # parse strings to datetimes
        dt_args = [
            parse_datetime(arg) if isinstance(arg, str) else arg for arg in arguments
        ]
        if len(arguments) == 3:
            if isinstance(dt_args[0], datetime) and isinstance(dt_args[1], datetime):
                dt_args = [
                    values.Interval(dt_args[0], dt_args[1]),
                    dt_args[2],
                ]
            if isinstance(dt_args[1], datetime) and isinstance(dt_args[2], datetime):
                dt_args = [
                    dt_args[0],
                    values.Interval(dt_args[1], dt_args[2]),
                ]

        return TEMPORAL_PREDICATES_MAP[op](*cast(List[ast.TemporalAstType], dt_args))

    # special property getters
    elif op in ["id", "geometry"]:
        return ast.Attribute(op)

    # normal property getter
    elif op == "get":
        return ast.Attribute(arguments[0])

    elif op == "bbox":
        pass  # TODO

    elif op in ARITHMETIC_MAP:
        return ARITHMETIC_MAP[op](*cast(List[ast.ScalarAstType], arguments))

    elif op in ["%", "floor", "ceil", "abs", "^", "min", "max"]:
        return ast.Function(
            FUNCTION_MAP.get(op, op), cast(List[ast.AstType], arguments)
        )

    raise ValueError(f"Invalid expression operation '{op}'")


def parse(jfe: Union[str, list, dict]) -> ast.Node:
    """Parses the given JFE expression (either a string or an already
    parsed JSON) to an AST.
    If a string is passed, it will be parsed as JSON.

    https://github.com/tschaub/ogcapi-features/tree/json-array-expression/extensions/cql/jfe
    """
    if isinstance(jfe, str):
        root = json.loads(jfe)
    else:
        root = jfe

    return cast(ast.Node, _parse_node(root))
