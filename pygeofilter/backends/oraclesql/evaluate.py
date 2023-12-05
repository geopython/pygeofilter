# ------------------------------------------------------------------------------
#
# Project: pygeofilter <https://github.com/geopython/pygeofilter>
# Authors: Andreas Kosubek <andreas.kosubek@ama.gv.at>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2023 Agrar Markt Austria
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

from typing import Dict, Optional

import shapely.geometry

from ... import ast, values
from ..evaluator import Evaluator, handle

COMPARISON_OP_MAP = {
    ast.ComparisonOp.EQ: "=",
    ast.ComparisonOp.NE: "<>",
    ast.ComparisonOp.LT: "<",
    ast.ComparisonOp.LE: "<=",
    ast.ComparisonOp.GT: ">",
    ast.ComparisonOp.GE: ">=",
}


ARITHMETIC_OP_MAP = {
    ast.ArithmeticOp.ADD: "+",
    ast.ArithmeticOp.SUB: "-",
    ast.ArithmeticOp.MUL: "*",
    ast.ArithmeticOp.DIV: "/",
}

SPATIAL_COMPARISON_OP_MAP = {
    ast.SpatialComparisonOp.INTERSECTS: "ANYINTERACT",
    ast.SpatialComparisonOp.DISJOINT: "DISJOINT",
    ast.SpatialComparisonOp.CONTAINS: "CONTAINS",
    ast.SpatialComparisonOp.WITHIN: "INSIDE",
    ast.SpatialComparisonOp.TOUCHES: "TOUCH",
    ast.SpatialComparisonOp.CROSSES: "OVERLAPBDYDISJOINT",
    ast.SpatialComparisonOp.OVERLAPS: "OVERLAPBDYINTERSECT",
    ast.SpatialComparisonOp.EQUALS: "EQUAL",
}

WITH_BINDS = False

BIND_VARIABLES = {}


class OracleSQLEvaluator(Evaluator):
    def __init__(
        self, attribute_map: Dict[str, str], function_map: Dict[str, str]
    ):
        self.attribute_map = attribute_map
        self.function_map = function_map

    @handle(ast.Not)
    def not_(self, node, sub):
        return f"NOT {sub}"

    @handle(ast.And, ast.Or)
    def combination(self, node, lhs, rhs):
        return f"({lhs} {node.op.value} {rhs})"

    @handle(ast.Comparison, subclasses=True)
    def comparison(self, node, lhs, rhs):
        if WITH_BINDS:
            BIND_VARIABLES[f"{lhs}"] = rhs
            sql = f"({lhs} {COMPARISON_OP_MAP[node.op]} :{lhs})"
        else:
            sql = f"({lhs} {COMPARISON_OP_MAP[node.op]} {rhs})"
        return sql

    @handle(ast.Between)
    def between(self, node, lhs, low, high):
        if WITH_BINDS:
            BIND_VARIABLES[f"{lhs}_high"] = high
            BIND_VARIABLES[f"{lhs}_low"] = low
            sql = f"({lhs} {'NOT ' if node.not_ else ''}BETWEEN :{lhs}_low AND :{lhs}_high)"
        else:
            sql = f"({lhs} {'NOT ' if node.not_ else ''}BETWEEN {low} AND {high})"
        return sql

    @handle(ast.Like)
    def like(self, node, lhs):
        pattern = node.pattern
        if node.wildcard != "%":
            # TODO: not preceded by escapechar
            pattern = pattern.replace(node.wildcard, "%")
        if node.singlechar != "_":
            # TODO: not preceded by escapechar
            pattern = pattern.replace(node.singlechar, "_")

        if WITH_BINDS:
            BIND_VARIABLES[f"{lhs}"] = pattern
            sql = f"{lhs} {'NOT ' if node.not_ else ''}LIKE "
            sql += f":{lhs} ESCAPE '{node.escapechar}'"

        else:
            sql = f"{lhs} {'NOT ' if node.not_ else ''}LIKE "
            sql += f"'{pattern}' ESCAPE '{node.escapechar}'"

        # TODO: handle node.nocase
        return sql

    @handle(ast.In)
    def in_(self, node, lhs, *options):
        return f"{lhs} {'NOT ' if node.not_ else ''}IN ({', '.join(options)})"

    @handle(ast.IsNull)
    def null(self, node, lhs):
        return f"{lhs} IS {'NOT ' if node.not_ else ''}NULL"

    @handle(ast.SpatialComparisonPredicate, subclasses=True)
    def spatial_operation(self, node, lhs, rhs):
        param = f"mask={SPATIAL_COMPARISON_OP_MAP[node.op]}"
        func = f"SDO_RELATE({lhs}, {rhs}, '{param}') = 'TRUE'"
        return func

    @handle(ast.BBox)
    def bbox(self, node, lhs):
        bbox = "SDO_GEOMETRY()"
        param = f"mask={ast.SpatialComparisonOp.INTERSECTS}"
        func = f"SDO_RELATE({lhs}, {bbox}, '{param}') = 'TRUE'"
        return func

    @handle(ast.Attribute)
    def attribute(self, node: ast.Attribute):
        return f"{self.attribute_map[node.name]}"

    @handle(ast.Arithmetic, subclasses=True)
    def arithmetic(self, node: ast.Arithmetic, lhs, rhs):
        op = ARITHMETIC_OP_MAP[node.op]
        return f"({lhs} {op} {rhs})"

    @handle(ast.Function)
    def function(self, node, *arguments):
        func = self.function_map[node.name]
        return f"{func}({','.join(arguments)})"

    @handle(*values.LITERALS)
    def literal(self, node):
        if isinstance(node, str):
            return f"'{node}'"
        else:
            return node

    @handle(values.Geometry)
    def geometry(self, node: values.Geometry):
        wkb_hex = shapely.geometry.shape(node).wkb_hex
        if WITH_BINDS:
            BIND_VARIABLES["wkb"] = wkb_hex
            sql = "SDO_UTIL.FROM_WKBGEOMETRY(:wkb)"
        else:
            sql = f"SDO_UTIL.FROM_WKBGEOMETRY('{wkb_hex}')"
        return sql

    @handle(values.Envelope)
    def envelope(self, node: values.Envelope):
        wkb_hex = shapely.geometry.box(
            node.x1, node.y1, node.x2, node.y2
        ).wkb_hex
        if WITH_BINDS:
            BIND_VARIABLES["wkb"] = wkb_hex
            sql = "SDO_UTIL.FROM_WKBGEOMETRY(:wkb)"
        else:
            sql = f"SDO_UTIL.FROM_WKBGEOMETRY('{wkb_hex}')"
        return sql


def to_sql_where(
    root: ast.Node,
    field_mapping: Dict[str, str],
    function_map: Optional[Dict[str, str]] = None,
) -> str:
    global WITH_BINDS
    WITH_BINDS = False
    return OracleSQLEvaluator(field_mapping, function_map or {}).evaluate(root)


def to_sql_where_with_binds(
    root: ast.Node,
    field_mapping: Dict[str, str],
    function_map: Optional[Dict[str, str]] = None,
) -> str:
    orcle = OracleSQLEvaluator(field_mapping, function_map or {})
    global WITH_BINDS
    WITH_BINDS = True
    global BIND_VARIABLES
    BIND_VARIABLES = {}
    return orcle.evaluate(root), BIND_VARIABLES
