from datetime import timedelta
from functools import reduce
from inspect import signature
from typing import Callable, Dict, Optional

from pygeoif import shape
from sqlalchemy import and_, func, not_, null, or_


def parse_bbox(box, srid: Optional[int] = None):
    minx, miny, maxx, maxy = box
    return func.ST_GeomFromEWKT(
        f"SRID={4326 if srid is None else srid};POLYGON(("
        f"{minx} {miny}, {minx} {maxy}, "
        f"{maxx} {maxy}, {maxx} {miny}, "
        f"{minx} {miny}))"
    )


def parse_geometry(geom: dict):
    crs_identifier = (
        geom.get("crs", {})
        .get("properties", {})
        .get("name", "urn:ogc:def:crs:EPSG::4326")
    )
    srid = crs_identifier.rpartition("::")[-1]
    wkt = shape(geom).wkt
    return func.ST_GeomFromEWKT(f"SRID={srid};{wkt}")


# ------------------------------------------------------------------------------
# Filters
# ------------------------------------------------------------------------------
class Operator:

    OPERATORS: Dict[str, Callable] = {
        "is_null": lambda f, a=None: f.is_(None),
        "is_not_null": lambda f, a=None: f.isnot(None),
        "==": lambda f, a: f == a,
        "=": lambda f, a: f == a,
        "eq": lambda f, a: f == a,
        "!=": lambda f, a: f != a,
        "<>": lambda f, a: f != a,
        "ne": lambda f, a: f != a,
        ">": lambda f, a: f > a,
        "gt": lambda f, a: f > a,
        "<": lambda f, a: f < a,
        "lt": lambda f, a: f < a,
        ">=": lambda f, a: f >= a,
        "ge": lambda f, a: f >= a,
        "<=": lambda f, a: f <= a,
        "le": lambda f, a: f <= a,
        "like": lambda f, a: f.like(a),
        "ilike": lambda f, a: f.ilike(a),
        "not_ilike": lambda f, a: ~f.ilike(a),
        "in": lambda f, a: f.in_(a),
        "not_in": lambda f, a: ~f.in_(a),
        "any": lambda f, a: f.any(a),
        "not_any": lambda f, a: func.not_(f.any(a)),
        "INTERSECTS": lambda f, a: f.ST_Intersects(a),
        "DISJOINT": lambda f, a: f.ST_Disjoint(a),
        "CONTAINS": lambda f, a: f.ST_Contains(a),
        "WITHIN": lambda f, a: f.ST_Within(a),
        "TOUCHES": lambda f, a: f.ST_Touches(a),
        "CROSSES": lambda f, a: f.ST_Crosses(a),
        "OVERLAPS": lambda f, a: f.ST_Overlaps(a),
        "EQUALS": lambda f, a: f.ST_Equals(a),
        "RELATE": lambda f, a, pattern: f.ST_Relate(a, pattern),
        "DWITHIN": lambda f, a, distance: f.ST_Dwithin(a, distance),
        "BEYOND": lambda f, a, distance: ~f.ST_Dwithin(a, distance),
        "+": lambda f, a: f + a,
        "-": lambda f, a: f - a,
        "*": lambda f, a: f * a,
        "/": lambda f, a: f / a,
    }

    def __init__(self, operator: Optional[str] = None):
        if not operator:
            operator = "=="

        if operator not in self.OPERATORS:
            raise Exception("Operator `{}` not valid.".format(operator))

        self.operator = operator
        self.function = self.OPERATORS[operator]
        self.arity = len(signature(self.function).parameters)


def combine(sub_filters, combinator: str = "AND"):
    """Combine filters using a logical combinator

    :param sub_filters: the filters to combine
    :param combinator: a string: "AND" / "OR"
    :return: the combined filter
    """
    assert combinator in ("AND", "OR")
    _op = and_ if combinator == "AND" else or_

    def test(acc, q):
        return _op(acc, q)

    return reduce(test, sub_filters)


def negate(sub_filter):
    """Negate a filter, opposing its meaning.

    :param sub_filter: the filter to negate
    :return: the negated filter
    """
    return not_(sub_filter)


def runop(lhs, rhs=None, op: str = "=", negate: bool = False):
    """Compare a filter with an expression using a comparison operation

    :param lhs: the field to compare
    :param rhs: the filter expression
    :param op: a string denoting the operation.
    :return: a comparison expression object
    """
    _op = Operator(op)

    if negate:
        return not_(_op.function(lhs, rhs))
    return _op.function(lhs, rhs)


def between(lhs, low, high, negate=False):
    """Create a filter to match elements that have a value within a certain
    range.

    :param lhs: the field to compare
    :param low: the lower value of the range
    :param high: the upper value of the range
    :param not_: whether the range shall be inclusive (the default) or
                 exclusive
    :return: a comparison expression object
    """
    l_op = Operator("<=")
    g_op = Operator(">=")
    if negate:
        return not_(and_(g_op.function(lhs, low), l_op.function(lhs, high)))
    return and_(g_op.function(lhs, low), l_op.function(lhs, high))


def like(lhs, rhs, case=False, negate=False):
    """Create a filter to filter elements according to a string attribute
    using wildcard expressions.

    :param lhs: the field to compare
    :param rhs: the wildcard pattern: a string containing any number of '%'
                characters as wildcards.
    :param case: whether the lookup shall be done case sensitively or not
    :param not_: whether the range shall be inclusive (the default) or
                 exclusive
    :return: a comparison expression object
    """
    if case:
        _op = Operator("like")
    else:
        _op = Operator("ilike")

    if negate:
        return not_(_op.function(lhs, rhs))
    return _op.function(lhs, rhs)


def temporal(lhs, time_or_period, op):
    """Create a temporal filter for the given temporal attribute.

    :param lhs: the field to compare
    :type lhs: :class:`django.db.models.F`
    :param time_or_period: the time instant or time span to use as a filter
    :type time_or_period: :class:`datetime.datetime` or a tuple of two
                          datetimes or a tuple of one datetime and one
                          :class:`datetime.timedelta`
    :param op: the comparison operation. one of ``"BEFORE"``,
               ``"BEFORE OR DURING"``, ``"DURING"``, ``"DURING OR AFTER"``,
               ``"AFTER"``.
    :type op: str
    :return: a comparison expression object
    :rtype: :class:`django.db.models.Q`
    """
    low = None
    high = None
    equal = None
    if op in ("BEFORE", "AFTER"):
        if op == "BEFORE":
            high = time_or_period
        else:
            low = time_or_period
    elif op == "TEQUALS":
        equal = time_or_period
    else:
        low, high = time_or_period

        if isinstance(low, timedelta):
            low = high - low
        if isinstance(high, timedelta):
            high = low + high
    if low is not None or high is not None:
        if low is not None and high is not None:
            return between(lhs, low, high)
        elif low is not None:
            return runop(lhs, low, ">=")
        else:
            return runop(lhs, high, "<=")
    elif equal is not None:
        return runop(lhs, equal, "==")


UNITS_LOOKUP = {"kilometers": "km", "meters": "m"}


def spatial(lhs, rhs, op, pattern=None, distance=None, units=None):
    """Create a spatial filter for the given spatial attribute.

    :param lhs: the field to compare
    :param rhs: the time instant or time span to use as a filter
    :param op: the comparison operation. one of ``"INTERSECTS"``,
               ``"DISJOINT"``, `"CONTAINS"``, ``"WITHIN"``,
               ``"TOUCHES"``, ``"CROSSES"``, ``"OVERLAPS"``,
               ``"EQUALS"``, ``"RELATE"``, ``"DWITHIN"``, ``"BEYOND"``
    :param pattern: the spatial relation pattern
    :param distance: the distance value for distance based lookups:
                     ``"DWITHIN"`` and ``"BEYOND"``
    :param units: the units the distance is expressed in
    :return: a comparison expression object
    """

    _op = Operator(op)
    if op == "RELATE":
        return _op.function(lhs, rhs, pattern)
    elif op in ("DWITHIN", "BEYOND"):
        if units == "kilometers":
            distance = distance / 1000
        elif units == "miles":
            distance = distance / 1609
        return _op.function(lhs, rhs, distance)
    else:
        return _op.function(lhs, rhs)


def bbox(lhs, minx, miny, maxx, maxy, crs=4326):
    """Create a bounding box filter for the given spatial attribute.

    :param lhs: the field to compare
    :param minx: the lower x part of the bbox
    :param miny: the lower y part of the bbox
    :param maxx: the upper x part of the bbox
    :param maxy: the upper y part of the bbox
    :param crs: the CRS the bbox is expressed in
    :return: a comparison expression object
    """

    return lhs.ST_Intersects(parse_bbox([minx, miny, maxx, maxy], crs))


def attribute(name, field_mapping={}, undefined_as_null: Optional[bool] = None):
    """Create an attribute lookup expression using a field mapping dictionary.

    :param name: the field filter name
    :param field_mapping: the dictionary to use as a lookup.
    :param undefined_as_null: how to handle a name not present in field_mapping
        (None (default) - leave as-is; True - treat as null; False - throw error)
    """
    if undefined_as_null is None:
        return field_mapping.get(name, name)
    if undefined_as_null:
        # return null object if name is not found in field_mapping
        return field_mapping.get(name, null())
    # undefined_as_null is False, so raise KeyError if name not found
    return field_mapping[name]


def literal(value):
    return value
