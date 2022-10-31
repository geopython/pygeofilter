from functools import reduce
from operator import add, and_, eq, ge, gt, le, lt, mul, ne, or_, sub, truediv

import shapely

from ...util import like_pattern_to_re


def combine(sub_filters, combinator: str):
    """Combine filters using a logical combinator"""
    assert combinator in ("AND", "OR")
    op = and_ if combinator == "AND" else or_
    return reduce(lambda acc, q: op(acc, q) if acc is not None else q, sub_filters)


def negate(sub_filter):
    """Negate a filter, opposing its meaning."""
    return ~sub_filter


OP_MAP = {
    "<": lt,
    "<=": le,
    ">": gt,
    ">=": ge,
    "<>": ne,
    "=": eq,
}


def compare(lhs, rhs, op):
    return OP_MAP[op](lhs, rhs)


def between(lhs, low, high, not_):
    result = lhs.between(low, high)
    if not_:
        result = ~result
    return result


def like(lhs, pattern, nocase, wildcard, singlechar, escapechar, not_):
    regex = like_pattern_to_re(
        pattern, nocase, wildcard, singlechar, escapechar or "\\"
    )
    result = lhs.str.match(regex)
    if not_:
        result = ~result
    return result


def contains(lhs, items, not_):
    # TODO: check if dataframe or scalar
    result = lhs.isin(items)
    if not_:
        result = ~result
    return result


def null(lhs, not_):
    result = lhs.isnull()
    if not_:
        result = ~result
    return result


def temporal(lhs, time_or_period, op):
    pass
    # TODO implement


SPATIAL_OP_MAP = {
    "INTERSECTS": "intersects",
    "DISJOINT": "disjoint",
    "CONTAINS": "contains",
    "WITHIN": "within",
    "TOUCHES": "touches",
    "CROSSES": "crosses",
    "OVERLAPS": "overlaps",
    "EQUALS": "geom_equals",
}


def spatial(lhs, rhs, op):
    assert op in SPATIAL_OP_MAP
    return getattr(lhs, SPATIAL_OP_MAP[op])(rhs)


def bbox(lhs, minx, miny, maxx, maxy, crs=None):
    box = shapely.geometry.Polygon.from_bounds(minx, miny, maxx, maxy)
    # TODO: handle CRS
    return lhs.intersects(box)


def attribute(df, name, field_mapping=None):
    if field_mapping:
        name = field_mapping[name]
    return df[name]


OP_TO_FUNC = {"+": add, "-": sub, "*": mul, "/": truediv}


def arithmetic(lhs, rhs, op):
    """Create an arithmetic filter"""
    return OP_TO_FUNC[op](lhs, rhs)
