from datetime import date, datetime, timedelta
import re

import shapely.geometry

from ... import ast
from ... import values
from ...evaluator import Evaluator, handle
from ...util import encode_duration


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


def maybe_bracket(node: ast.Node, encoded: str) -> str:
    if isinstance(node, (ast.Not, ast.Combination, ast.Comparison, ast.Arithmetic)):
        return f"({encoded})"
    return encoded


class ECQLEvaluator(Evaluator):
    @handle(ast.Not)
    def not_(self, node: ast.Not, sub):
        return f"NOT {sub}"

    @handle(ast.And, ast.Or)
    def combination(self, node: ast.Combination, lhs, rhs):
        if isinstance(node.lhs, ast.Combination):
            lhs = f"({lhs})"
        if isinstance(node.rhs, ast.Combination):
            rhs = f"({rhs})"
        return f"{lhs} {node.op.value} {rhs}"

    @handle(ast.Comparison, subclasses=True)
    def comparison(self, node: ast.Comparison, lhs, rhs):
        return f"{lhs} {COMPARISON_OP_MAP[node.op]} {rhs}"

    @handle(ast.Between)
    def between(self, node, lhs, low, high):
        return f"{lhs} {'NOT ' if node.not_ else ''}BETWEEN {low} AND {high}"

    @handle(ast.Like)
    def like(self, node: ast.Like, lhs):
        pattern = node.pattern
        if node.wildcard != "%":
            # TODO: not preceded by escapechar
            pattern = pattern.replace(node.wildcard, "%")
        if node.singlechar != "_":
            # TODO: not preceded by escapechar
            pattern = pattern.replace(node.singlechar, "_")

        return f"{lhs} {'NOT ' if node.not_ else ''}{'I' if node.nocase else ''}LIKE '{pattern}'"

    @handle(ast.In)
    def in_(self, node: ast.In, lhs, *options):
        return f"{lhs} {'NOT ' if node.not_ else ''}IN ({', '.join(options)})"

    @handle(ast.IsNull)
    def null(self, node: ast.IsNull, lhs):
        return f"{lhs} IS {'NOT ' if node.not_ else ''}NULL"

    @handle(ast.Exists)
    def exists(self, node: ast.Exists, lhs):
        return f"{lhs} {'DOES-NOT-EXIST' if node.not_ else 'EXISTS'}"

    @handle(ast.Include)
    def include(self, node: ast.Include):
        return "EXCLUDE" if node.not_ else "INCLUDE"

    @handle(ast.TemporalPredicate, subclasses=True)
    def temporal(self, node: ast.TemporalPredicate, lhs, rhs):
        if isinstance(node, ast.TimeBefore):
            return f"{lhs} BEFORE {rhs}"
        elif isinstance(node, ast.TimeBeforeOrDuring):
            return f"{lhs} BEFORE OR DURING {rhs}"
        elif isinstance(node, ast.TimeDuring):
            return f"{lhs} DURING {rhs}"
        elif isinstance(node, ast.TimeDuringOrAfter):
            return f"{lhs} DURING OR AFTER {rhs}"
        elif isinstance(node, ast.TimeAfter):
            return f"{lhs} AFTER {rhs}"
        else:
            raise NotImplementedError(f"{node.op} is not implemented")

    @handle(ast.SpatialComparisonPredicate, subclasses=True)
    def spatial_operation(self, node: ast.SpatialComparisonPredicate, lhs, rhs):
        return f"{node.op.value}({lhs}, {rhs})"

    @handle(ast.BBox)
    def bbox(self, node: ast.BBox, lhs):
        if not node.crs:
            return f"BBOX({lhs}, {node.minx}, {node.miny}, {node.maxx}, {node.maxy})"
        else:
            return f"BBOX({lhs}, {node.minx}, {node.miny}, {node.maxx}, {node.maxy}, '{node.crs}')"

    @handle(ast.Relate)
    def relate(self, node: ast.Relate, lhs, rhs):
        return f"RELATE({lhs}, {rhs}, '{node.pattern}')"

    @handle(ast.SpatialDistancePredicate, subclasses=True)
    def spatial_distance_predicate(self, node: ast.SpatialDistancePredicate, lhs, rhs):
        return f"{node.op.value}({lhs}, {rhs}, {node.distance}, {node.units})"

    @handle(ast.Attribute)
    def attribute(self, node: ast.Attribute):
        is_cname = re.match(r"[a-zA-Z_][a-zA-Z0-9_]*", node.name) is not None
        return node.name if is_cname else f'"{node.name}"'

    @handle(ast.Arithmetic, subclasses=True)
    def arithmetic(self, node: ast.Arithmetic, lhs, rhs):
        def arity(node):
            if isinstance(node, (ast.Sub, ast.Add)):
                return 1
            elif isinstance(node, (ast.Div, ast.Mul)):
                return 2

        node_arity = arity(node)
        lhs_arity = arity(node.lhs)
        rhs_arity = arity(node.rhs)
        if lhs_arity and node_arity > lhs_arity:
            lhs = f"({lhs})"
        if rhs_arity and node_arity > rhs_arity:
            rhs = f"({rhs})"

        return f"{lhs} {node.op.value} {rhs}"

    @handle(ast.Function)
    def function(self, node: ast.Function, *arguments):
        return f"{node.name}({', '.join(arguments)})"

    @handle(*values.LITERALS)
    def literal(self, node):
        if isinstance(node, str):
            return f"'{node}'"
        elif isinstance(node, (datetime, date)):
            return node.isoformat().replace("+00:00", "Z")
        elif isinstance(node, timedelta):
            return encode_duration(node)
        elif isinstance(node, bool):
            return str(node).upper()
        elif isinstance(node, float):
            return str(int(node) if node.is_integer() else node)
        else:
            return str(node)

    @handle(values.Interval)
    def interval(self, node: values.Interval, start, end):
        return f"{self.literal(node.start)} / {self.literal(node.end)}"

    @handle(values.Geometry)
    def geometry(self, node: values.Geometry):
        return shapely.geometry.shape(node).wkt

    @handle(values.Envelope)
    def envelope(self, node: values.Envelope):
        return f"ENVELOPE ({node.x1} {node.y1} {node.x2} {node.y2})"


def encode(root: ast.Node) -> str:
    return ECQLEvaluator().evaluate(root)
