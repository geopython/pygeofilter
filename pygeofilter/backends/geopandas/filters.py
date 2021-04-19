from operator import (
    and_, or_, lt, le, gt, ge, ne, eq, add, sub, mul, truediv
)
from datetime import datetime, timedelta
from functools import reduce

import shapely

from ...util import like_pattern_to_re


def combine(sub_filters, combinator: str):
    """ Combine filters using a logical combinator """
    assert combinator in ("AND", "OR")
    op = and_ if combinator == "AND" else or_
    return reduce(lambda acc, q: op(acc, q) if acc else q, sub_filters)


def negate(sub_filter):
    """ Negate a filter, opposing its meaning. """
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
    """ Compare a filter with an expression using a comparison operation """

    return OP_MAP[op](lhs, rhs)


def between(lhs, low, high, not_):
    return low <= lhs <= high


def like(lhs, pattern, nocase, wildcard, single_char, escape_char):
    regex = like_pattern_to_re(
        pattern,
        nocase,
        wildcard,
        single_char,
        escape_char
    )
    return lhs.str.match(regex)



def contains(lhs, items, not_):
    # TODO: check if dataframe or scalar
    return lhs.isin(items)


def null(lhs):
    return lhs.isnull()


def temporal(lhs, time_or_period, op):
    pass
    # TODO implement


def spatial(lhs, rhs, op):
    assert op in (
        "INTERSECTS", "DISJOINT", "CONTAINS", "WITHIN", "TOUCHES", "CROSSES",
        "OVERLAPS", "EQUALS",
        # TODO: "RELATE", "DWITHIN", "BEYOND"
    )

    return getattr(lhs, op.lower())(rhs)


def bbox(lhs, minx, miny, maxx, maxy, crs=None):
    box = shapely.geometry.Polygon.from_bounds(minx, miny, maxx, maxy)
    # TODO: handle CRS
    return lhs.intersects(box)


def attribute(df, name, field_mapping=None):
    if field_mapping:
        name = field_mapping[name]
    return df[name]


OP_TO_FUNC = {
    "+": add,
    "-": sub,
    "*": mul,
    "/": truediv
}


def arithmetic(lhs, rhs, op):
    """ Create an arithmetic filter """
    return OP_TO_FUNC[op](lhs, rhs)
