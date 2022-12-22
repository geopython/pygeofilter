# Common configurations for cql2 parsers and evaluators.
from typing import Dict, Type, Union

from . import ast

# https://github.com/opengeospatial/ogcapi-features/tree/master/cql2


COMPARISON_MAP: Dict[str, Type[ast.Node]] = {
    "=": ast.Equal,
    "eq": ast.Equal,
    "<>": ast.NotEqual,
    "!=": ast.NotEqual,
    "ne": ast.NotEqual,
    "<": ast.LessThan,
    "lt": ast.LessThan,
    "<=": ast.LessEqual,
    "lte": ast.LessEqual,
    ">": ast.GreaterThan,
    "gt": ast.GreaterThan,
    ">=": ast.GreaterEqual,
    "gte": ast.GreaterEqual,
    "like": ast.Like,
}

SPATIAL_PREDICATES_MAP: Dict[str, Type[ast.SpatialComparisonPredicate]] = {
    "s_intersects": ast.GeometryIntersects,
    "s_equals": ast.GeometryEquals,
    "s_disjoint": ast.GeometryDisjoint,
    "s_touches": ast.GeometryTouches,
    "s_within": ast.GeometryWithin,
    "s_overlaps": ast.GeometryOverlaps,
    "s_crosses": ast.GeometryCrosses,
    "s_contains": ast.GeometryContains,
}

TEMPORAL_PREDICATES_MAP: Dict[str, Type[ast.TemporalPredicate]] = {
    "t_before": ast.TimeBefore,
    "t_after": ast.TimeAfter,
    "t_meets": ast.TimeMeets,
    "t_metby": ast.TimeMetBy,
    "t_overlaps": ast.TimeOverlaps,
    "t_overlappedby": ast.TimeOverlappedBy,
    "t_begins": ast.TimeBegins,
    "t_begunby": ast.TimeBegunBy,
    "t_during": ast.TimeDuring,
    "t_contains": ast.TimeContains,
    "t_ends": ast.TimeEnds,
    "t_endedby": ast.TimeEndedBy,
    "t_equals": ast.TimeEquals,
    "t_intersects": ast.TimeOverlaps,
}


ARRAY_PREDICATES_MAP: Dict[str, Type[ast.ArrayPredicate]] = {
    "a_equals": ast.ArrayEquals,
    "a_contains": ast.ArrayContains,
    "a_containedby": ast.ArrayContainedBy,
    "a_overlaps": ast.ArrayOverlaps,
}

ARITHMETIC_MAP: Dict[str, Type[ast.Arithmetic]] = {
    "+": ast.Add,
    "-": ast.Sub,
    "*": ast.Mul,
    "/": ast.Div,
}

CONDITION_MAP: Dict[str, Type[ast.Node]] = {
    "and": ast.And,
    "or": ast.Or,
    "not": ast.Not,
    "isNull": ast.IsNull,
}

BINARY_OP_PREDICATES_MAP: Dict[
    str,
    Union[
        Type[ast.Node],
        Type[ast.Comparison],
        Type[ast.SpatialComparisonPredicate],
        Type[ast.TemporalPredicate],
        Type[ast.ArrayPredicate],
        Type[ast.Arithmetic],
    ],
] = {
    **COMPARISON_MAP,
    **SPATIAL_PREDICATES_MAP,
    **TEMPORAL_PREDICATES_MAP,
    **ARRAY_PREDICATES_MAP,
    **ARITHMETIC_MAP,
    **CONDITION_MAP,
}


def get_op(node: ast.Node) -> Union[str, None]:
    # Get the cql2 operator string from a node.
    for k, v in BINARY_OP_PREDICATES_MAP.items():
        if isinstance(node, v):
            return k
    return None
