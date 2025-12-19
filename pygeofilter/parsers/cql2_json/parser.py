# ------------------------------------------------------------------------------
#
# Project: pygeofilter <https://github.com/geopython/pygeofilter>
# Authors: Fabian Schindler <fabian.schindler@eox.at>,
# David Bitner <bitner@dbspatial.com>
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

import json
from datetime import date, datetime, timedelta
from typing import List, Union, cast

from ... import ast, values
from ...cql2 import BINARY_OP_PREDICATES_MAP
from ...util import parse_date, parse_datetime, parse_duration

# https://github.com/opengeospatial/ogcapi-features/tree/master/cql2


JsonType = Union[dict, list, str, float, int, bool, None]


def walk_cql_json(node: JsonType):  # noqa: C901
    if isinstance(
        node,
        (
            str,
            float,
            int,
            bool,
            date,
            datetime,
            values.Geometry,
            values.Interval,
            values.Envelope,
            ast.Node,
        ),
    ):
        return node

    if isinstance(node, list):
        return [walk_cql_json(sub_node) for sub_node in node]

    if not isinstance(node, dict):
        raise ValueError(f"Invalid type {type(node)}")

    if "filter-lang" in node and node["filter-lang"] != "cql2-json":
        raise Exception(f"Cannot parse {node['filter-lang']} with cql2-json.")

    elif "filter" in node:
        return walk_cql_json(node["filter"])

    # check if we are dealing with a geometry
    if "type" in node and "coordinates" in node:
        # TODO: test if node is actually valid
        return values.Geometry(node)

    elif "bbox" in node:
        return values.Envelope(*node["bbox"])

    elif "date" in node:
        return parse_date(node["date"])

    elif "timestamp" in node:
        return parse_datetime(node["timestamp"])

    elif "interval" in node:
        parsed: List[Union[date, datetime, timedelta, None]] = []
        for value in node["interval"]:
            if value == "..":
                parsed.append(None)
                continue
            try:
                parsed.append(parse_date(value))
            except ValueError:
                try:
                    parsed.append(parse_duration(value))
                except ValueError:
                    parsed.append(parse_datetime(value))

        return values.Interval(*parsed)

    elif "property" in node:
        return ast.Attribute(node["property"])

    elif "function" in node:
        return ast.Function(
            node["function"]["name"],
            cast(List[ast.AstType], walk_cql_json(node["function"]["arguments"])),
        )

    elif "lower" in node:
        return ast.Function("lower", [cast(ast.Node, walk_cql_json(node["lower"]))])

    elif "op" in node:
        op = node["op"]
        args = walk_cql_json(node["args"])

        if op in ("and", "or"):
            return (ast.And if op == "and" else ast.Or).from_items(*args)

        elif op == "not":
            # allow both arrays and objects, the standard is ambigous in
            # that regard
            if isinstance(args, list):
                args = args[0]
            return ast.Not(cast(ast.Node, walk_cql_json(args)))

        elif op == "isNull":
            # like with "not", allow both arrays and objects
            if isinstance(args, list):
                args = args[0]
            return ast.IsNull(cast(ast.Node, walk_cql_json(args)), not_=False)

        elif op == "between":
            return ast.Between(
                cast(ast.Node, walk_cql_json(args[0])),
                cast(ast.ScalarAstType, walk_cql_json(args[1][0])),
                cast(ast.ScalarAstType, walk_cql_json(args[1][1])),
                not_=False,
            )

        elif op == "like":
            return ast.Like(
                cast(ast.Node, walk_cql_json(args[0])),
                pattern=cast(str, args[1]),
                nocase=False,
                wildcard="%",
                singlechar=".",
                escapechar="\\",
                not_=False,
            )

        elif op == "in":
            return ast.In(
                cast(ast.AstType, walk_cql_json(args[0])),
                cast(List[ast.AstType], walk_cql_json(args[1])),
                not_=False,
            )

        elif op in BINARY_OP_PREDICATES_MAP:
            args = [cast(ast.Node, walk_cql_json(arg)) for arg in args]
            return BINARY_OP_PREDICATES_MAP[op](*args)

    raise ValueError(f"Unable to parse expression node {node!r}")


def parse(cql: Union[str, dict]) -> ast.AstType:
    if isinstance(cql, str):
        root = json.loads(cql)
    else:
        root = cql

    return walk_cql_json(root)
