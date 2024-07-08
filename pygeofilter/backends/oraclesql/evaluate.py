# ------------------------------------------------------------------------------
#
# Project: pygeofilter <https://github.com/geopython/pygeofilter>
# Authors: Andreas Kosubek <andreas.kosubek@ama.gv.at>
#          Bernhard Mallinger <bernhard.mallinger@eox.at>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2023 Agrar Markt Austria
# Copyright (C) 2024 EOX IT Services GmbH
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
from typing import Any, Dict, Optional, Tuple

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


class OracleSQLEvaluator(Evaluator):
    bind_variables: Dict[str, Any]

    def __init__(self, attribute_map: Dict[str, str], function_map: Dict[str, str]):
        self.attribute_map = attribute_map
        self.function_map = function_map

        self.with_bind_variables = False
        self.bind_variables = {}
        # Counter for bind variables
        self.b_cnt = 0

    @handle(ast.Not)
    def not_(self, node, sub):
        return f"NOT {sub}"

    @handle(ast.And, ast.Or)
    def combination(self, node, lhs, rhs):
        return f"({lhs} {node.op.value} {rhs})"

    @handle(ast.Comparison, subclasses=True)
    def comparison(self, node, lhs, rhs):
        if self.with_bind_variables:
            self.bind_variables[f"{lhs}_{self.b_cnt}"] = rhs
            sql = f"({lhs} {COMPARISON_OP_MAP[node.op]} :{lhs}_{self.b_cnt})"
            self.b_cnt += 1
        else:
            sql = f"({lhs} {COMPARISON_OP_MAP[node.op]} {rhs})"
        return sql

    @handle(ast.Between)
    def between(self, node, lhs, low, high):
        if self.with_bind_variables:
            self.bind_variables[f"{lhs}_high_{self.b_cnt}"] = high
            self.bind_variables[f"{lhs}_low_{self.b_cnt}"] = low
            sql = (
                f"({lhs} {'NOT ' if node.not_ else ''}BETWEEN "
                f":{lhs}_low_{self.b_cnt} AND :{lhs}_high_{self.b_cnt})"
            )
            self.b_cnt += 1
        else:
            sql = f"({lhs} {'NOT ' if node.not_ else ''}BETWEEN " f"{low} AND {high})"
        return sql

    @handle(ast.Like)
    def like(self, node, lhs):
        pattern = node.pattern
        if node.wildcard != "%":
            pattern = pattern.replace(node.wildcard, "%")
        if node.singlechar != "_":
            pattern = pattern.replace(node.singlechar, "_")

        if self.with_bind_variables:
            self.bind_variables[f"{lhs}_{self.b_cnt}"] = pattern
            sql = f"{lhs} {'NOT ' if node.not_ else ''}LIKE "
            sql += f":{lhs}_{self.b_cnt} ESCAPE '{node.escapechar}'"

        else:
            sql = f"{lhs} {'NOT ' if node.not_ else ''}LIKE "
            sql += f"'{pattern}' ESCAPE '{node.escapechar}'"

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
        geo_json = json.dumps(
            {
                "type": "Polygon",
                "coordinates": [
                    [
                        [node.minx, node.miny],
                        [node.minx, node.maxy],
                        [node.maxx, node.maxy],
                        [node.maxx, node.miny],
                        [node.minx, node.miny],
                    ]
                ],
            }
        )
        srid = 4326
        param = "mask=ANYINTERACT"

        if self.with_bind_variables:
            self.bind_variables[f"geo_json_{self.b_cnt}"] = geo_json
            self.bind_variables[f"srid_{self.b_cnt}"] = srid
            geom_sql = (
                f"SDO_UTIL.FROM_JSON(geometry => :geo_json_{self.b_cnt}, "
                f"srid => :srid_{self.b_cnt})"
            )
            self.b_cnt += 1
        else:
            geom_sql = (
                f"SDO_UTIL.FROM_JSON(geometry => '{geo_json}', " f"srid => {srid})"
            )

        sql = f"SDO_RELATE({lhs}, {geom_sql}, '{param}') = 'TRUE'"
        return sql

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
        # TODO Read CRS information from
        #      node and translate to SRID
        srid = 4326
        geo_json = json.dumps(node.geometry)
        print(geo_json)
        if self.with_bind_variables:
            self.bind_variables[f"geo_json_{self.b_cnt}"] = geo_json
            self.bind_variables[f"srid_{self.b_cnt}"] = srid
            sql = (
                f"SDO_UTIL.FROM_JSON(geometry => :geo_json_{self.b_cnt}, "
                f"srid => :srid_{self.b_cnt})"
            )
            self.b_cnt += 1
        else:
            sql = f"SDO_UTIL.FROM_JSON(geometry => '{geo_json}', " f"srid => {srid})"
        return sql

    @handle(values.Envelope)
    def envelope(self, node: values.Envelope):
        # TODO Read CRS information from
        #      node and translate to SRID
        srid = 4326
        geo_json = json.dumps(node.geometry)
        if self.with_bind_variables:
            self.bind_variables[f"geo_json_{self.b_cnt}"] = geo_json
            self.bind_variables[f"srid_{self.b_cnt}"] = srid
            sql = (
                f"SDO_UTIL.FROM_JSON(geometry => :geo_json_{self.b_cnt}, "
                f"srid => :srid_{self.b_cnt})"
            )
            self.b_cnt += 1
        else:
            sql = f"SDO_UTIL.FROM_JSON(geometry => '{geo_json}', " f"srid => {srid})"
        return sql


def to_sql_where(
    root: ast.Node,
    field_mapping: Dict[str, str],
    function_map: Optional[Dict[str, str]] = None,
) -> str:
    orcle = OracleSQLEvaluator(field_mapping, function_map or {})
    orcle.with_bind_variables = False
    return orcle.evaluate(root)


def to_sql_where_with_bind_variables(
    root: ast.Node,
    field_mapping: Dict[str, str],
    function_map: Optional[Dict[str, str]] = None,
) -> Tuple[str, Dict[str, Any]]:
    orcle = OracleSQLEvaluator(field_mapping, function_map or {})
    orcle.with_bind_variables = True
    orcle.bind_variables = {}
    return orcle.evaluate(root), orcle.bind_variables
