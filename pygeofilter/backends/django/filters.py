# ------------------------------------------------------------------------------
#
# Project: pygeofilter <https://github.com/geopython/pygeofilter>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2019 EOX IT Services GmbH
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


from datetime import datetime, timedelta
from functools import reduce
from operator import add, and_, mul, or_, sub, truediv
from typing import Dict, List, Optional, Union

from django.contrib.gis.gdal import SpatialReference
from django.contrib.gis.geos import Polygon
from django.contrib.gis.measure import D
from django.db.models import F, Q, Value
from django.db.models.expressions import Expression

ArithmeticType = Union[Expression, F, Value, int, float]

# ------------------------------------------------------------------------------
# Filters
# ------------------------------------------------------------------------------


def combine(sub_filters: List[Q], combinator: str = "AND") -> Q:
    """Combine filters using a logical combinator"""
    op = and_ if combinator == "AND" else or_
    return reduce(lambda acc, q: op(acc, q) if acc else q, sub_filters)


def negate(sub_filter: Q) -> Q:
    """Negate a filter, opposing its meaning."""
    return ~sub_filter


OP_TO_COMP = {"<": "lt", "<=": "lte", ">": "gt", ">=": "gte", "<>": None, "=": "exact"}

INVERT_COMP: Dict[Optional[str], str] = {
    "lt": "gt",
    "lte": "gte",
    "gt": "lt",
    "gte": "lte",
}


def compare(
    lhs: Union[F, Value],
    rhs: Union[F, Value],
    op: str,
    mapping_choices: Optional[Dict[str, Dict[str, str]]] = None,
) -> Q:
    """Compare a filter with an expression using a comparison operation

    :param lhs: the field to compare
    :type lhs: :class:`django.db.models.F`
    :param rhs: the filter expression
    :type rhs: :class:`django.db.models.F`
    :param op: a string denoting the operation. one of ``"<"``, ``"<="``,
               ``">"``, ``">="``, ``"<>"``, ``"="``
    :type op: str
    :param mapping_choices: a dict to lookup potential choices for a
                            certain field.
    :type mapping_choices: dict[str, str]
    :return: a comparison expression object
    :rtype: :class:`django.db.models.Q`
    """
    comp = OP_TO_COMP[op]

    # if the left hand side is not a field reference, the comparison
    # can be be inverted to try if the right hand side is a field
    # reference.
    if not isinstance(lhs, F):
        lhs, rhs = rhs, lhs
        comp = INVERT_COMP.get(comp, comp)

    # if neither lhs and rhs are fields, we have to fail here
    if not isinstance(lhs, F):
        raise ValueError(f"Unable to compare non-field {lhs}")

    field_name = lhs.name

    if mapping_choices and field_name in mapping_choices:
        try:
            if isinstance(rhs, str):
                rhs = mapping_choices[field_name][rhs]
            elif hasattr(rhs, "value"):
                rhs = Value(mapping_choices[field_name][rhs.value])

        except KeyError as e:
            raise AssertionError("Invalid field value %s" % e)

    if comp:
        return Q(**{"%s__%s" % (lhs.name, comp): rhs})
    return ~Q(**{field_name: rhs})


def between(
    lhs: F, low: Union[F, Value], high: Union[F, Value], not_: bool = False
) -> Q:
    """Create a filter to match elements that have a value within a certain
    range.

    :param lhs: the field to compare
    :type lhs: :class:`django.db.models.F`
    :param low: the lower value of the range
    :type low:
    :param high: the upper value of the range
    :type high:
    :param not_: whether the range shall be inclusive (the default) or
                 exclusive
    :type not_: bool
    :return: a comparison expression object
    :rtype: :class:`django.db.models.Q`
    """
    q = Q(**{"%s__range" % lhs.name: (low, high)})
    return ~q if not_ else q


def like(
    lhs: F,
    pattern: str,
    nocase: bool = False,
    not_: bool = False,
    mapping_choices: Optional[Dict[str, Dict[str, str]]] = None,
) -> Q:
    """Create a filter to filter elements according to a string attribute
    using wildcard expressions.

    :param lhs: the field to compare
    :type lhs: :class:`django.db.models.F`
    :param rhs: the wildcard pattern: a string containing any number of '%'
                characters as wildcards.
    :type rhs: str
    :param case: whether the lookup shall be done case sensitively or not
    :type case: bool
    :param not_: whether the range shall be inclusive (the default) or
                 exclusive
    :type not_: bool
    :param mapping_choices: a dict to lookup potential choices for a
                            certain field.
    :type mapping_choices: dict[str, str]
    :return: a comparison expression object
    :rtype: :class:`django.db.models.Q`
    """
    parts = pattern.split("%")
    length = len(parts)

    if mapping_choices and lhs.name in mapping_choices:
        # special case when choices are given for the field:
        # compare statically and use 'in' operator to check if contained
        cmp_av = [
            (a, a.lower() if nocase else a) for a in mapping_choices[lhs.name].keys()
        ]

        for idx, part in enumerate(parts):
            if not part:
                continue

            cmp_p = part.lower() if nocase else part

            if idx == 0 and length > 1:  # startswith
                cmp_av = [a for a in cmp_av if a[1].startswith(cmp_p)]
            elif idx == 0:  # exact matching
                cmp_av = [a for a in cmp_av if a[1] == cmp_p]
            elif idx == length - 1:  # endswith
                cmp_av = [a for a in cmp_av if a[1].endswith(cmp_p)]
            else:  # middle
                cmp_av = [a for a in cmp_av if cmp_p in a[1]]

        q = Q(
            **{"%s__in" % lhs.name: [mapping_choices[lhs.name][a[0]] for a in cmp_av]}
        )

    else:
        i = "i" if nocase else ""
        q = None

        for idx, part in enumerate(parts):
            if not part:
                continue

            if idx == 0 and length > 1:  # startswith
                new_q = Q(**{"%s__%s" % (lhs.name, "%sstartswith" % i): part})
            elif idx == 0:  # exact matching
                new_q = Q(**{"%s__%s" % (lhs.name, "%sexact" % i): part})
            elif idx == length - 1:  # endswith
                new_q = Q(**{"%s__%s" % (lhs.name, "%sendswith" % i): part})
            else:  # middle
                new_q = Q(**{"%s__%s" % (lhs.name, "%scontains" % i): part})

            q = q & new_q if q else new_q

    return ~q if not_ else q


def contains(
    lhs: F,
    items: List[Union[F, Value]],
    not_: bool = False,
    mapping_choices: Optional[Dict[str, Dict[str, str]]] = None,
) -> Q:
    """Create a filter to match elements attribute to be in a list of choices.

    :param lhs: the field to compare
    :type lhs: :class:`django.db.models.F`
    :param items: a list of choices
    :type items: list
    :param not_: whether the range shall be inclusive (the default) or
                 exclusive
    :type not_: bool
    :param mapping_choices: a dict to lookup potential choices for a
                            certain field.
    :type mapping_choices: dict[str, str]
    :return: a comparison expression object
    :rtype: :class:`django.db.models.Q`
    """

    if mapping_choices is not None and lhs.name in mapping_choices:

        def map_value(
            item: Union[str, Value], choices: Dict[str, str]
        ) -> Union[str, Value]:
            try:
                if isinstance(item, str):
                    item = choices[item]
                elif isinstance(item, Value):
                    item = Value(choices[item.value])

            except KeyError as e:
                raise AssertionError("Invalid field value %s" % e)
            return item

        items = [map_value(item, mapping_choices[lhs.name]) for item in items]

    q = Q(**{"%s__in" % lhs.name: items})
    return ~q if not_ else q


def null(lhs: F, not_: bool = False) -> Q:
    """Create a filter to match elements whose attribute is (not) null

    :param lhs: the field to compare
    :type lhs: :class:`django.db.models.F`
    :param not_: whether the range shall be inclusive (the default) or
                 exclusive
    :type not_: bool
    :return: a comparison expression object
    :rtype: :class:`django.db.models.Q`
    """
    return Q(**{"%s__isnull" % lhs.name: not not_})


def temporal(lhs: F, time_or_period: Value, op: str) -> Q:
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
    assert op in ("BEFORE", "BEFORE OR DURING", "DURING", "DURING OR AFTER", "AFTER")
    time_or_period = time_or_period.value
    low: Union[datetime, timedelta, None] = None
    high: Union[datetime, timedelta, None] = None
    if op in ("BEFORE", "AFTER"):
        assert isinstance(time_or_period, datetime)
        if op == "BEFORE":
            high = time_or_period
        else:
            low = time_or_period
    else:
        low, high = time_or_period
        low = low.value if isinstance(low, Value) else low
        high = high.value if isinstance(high, Value) else high
        assert isinstance(low, datetime) or isinstance(high, datetime)

        if isinstance(low, timedelta) and isinstance(high, datetime):
            low = high - low
        if isinstance(low, datetime) and isinstance(high, timedelta):
            high = low + high

    if low and high:
        return Q(**{"%s__range" % lhs.name: (low, high)})
    elif low:
        return Q(**{"%s__gte" % lhs.name: low})
    else:
        return Q(**{"%s__lte" % lhs.name: high})


def time_interval(
    time_or_period: Value,
    containment: str = "overlaps",
    begin_time_field: str = "begin_time",
    end_time_field: str = "end_time",
) -> Q:
    """ """

    gt_op = "__gte"
    lt_op = "__lte"

    is_slice = len(time_or_period) == 1
    if len(time_or_period) == 1:
        is_slice = True
        value = time_or_period[0]
    else:
        is_slice = False
        low, high = time_or_period

    if is_slice or (high == low and containment == "overlaps"):
        return Q(
            **{
                begin_time_field + "__lte": time_or_period[0],
                end_time_field + "__gte": time_or_period[0],
            }
        )

    elif high == low:
        return Q(**{begin_time_field + "__gte": value, end_time_field + "__lte": value})

    else:
        q = Q()
        # check if the temporal bounds must be strictly contained
        if containment == "contains":
            if high is not None:
                q &= Q(**{end_time_field + lt_op: high})
            if low is not None:
                q &= Q(**{begin_time_field + gt_op: low})
        # or just overlapping
        else:
            if high is not None:
                q &= Q(**{begin_time_field + lt_op: high})
            if low is not None:
                q &= Q(**{end_time_field + gt_op: low})
        return q


UNITS_LOOKUP = {"kilometers": "km", "meters": "m"}


INVERT_SPATIAL_OP = {
    "WITHIN": "CONTAINS",
    "CONTAINS": "WITHIN",
}


def spatial(
    lhs: Union[F, Value],
    rhs: Union[F, Value],
    op: str,
    pattern: Optional[str] = None,
    distance: Optional[float] = None,
    units: Optional[str] = None,
) -> Q:
    """Create a spatial filter for the given spatial attribute.

    :param lhs: the field to compare
    :type lhs: :class:`django.db.models.F`
    :param rhs: the time instant or time span to use as a filter
    :type rhs:
    :param op: the comparison operation. one of ``"INTERSECTS"``,
               ``"DISJOINT"``, `"CONTAINS"``, ``"WITHIN"``,
               ``"TOUCHES"``, ``"CROSSES"``, ``"OVERLAPS"``,
               ``"EQUALS"``, ``"RELATE"``, ``"DWITHIN"``, ``"BEYOND"``
    :type op: str
    :param pattern: the spatial relation pattern
    :type pattern: str
    :param distance: the distance value for distance based lookups:
                     ``"DWITHIN"`` and ``"BEYOND"``
    :type distance: float
    :param units: the units the distance is expressed in
    :type units: str
    :return: a comparison expression object
    :rtype: :class:`django.db.models.Q`
    """

    assert op in (
        "INTERSECTS",
        "DISJOINT",
        "CONTAINS",
        "WITHIN",
        "TOUCHES",
        "CROSSES",
        "OVERLAPS",
        "EQUALS",
        "RELATE",
        "DWITHIN",
        "BEYOND",
    )

    # if the left hand side is not a field reference, the comparison
    # can be be inverted to try if the right hand side is a field
    # reference.
    if not isinstance(lhs, F):
        lhs, rhs = rhs, lhs
        op = INVERT_SPATIAL_OP.get(op, op)

    # if neither lhs and rhs are fields, we have to fail here
    if not isinstance(lhs, F):
        raise ValueError(f"Unable to compare non-field {lhs}")

    return Q(**{"%s__%s" % (lhs.name, op.lower()): rhs})


def spatial_relate(lhs: Union[F, Value], rhs: Union[F, Value], pattern: str) -> Q:

    if not isinstance(lhs, F):
        # TODO: cannot yet invert pattern -> raise
        raise ValueError(f"Unable to compare non-field {lhs}")

    return Q(**{"%s__relate" % lhs.name: (rhs, pattern)})


def spatial_distance(
    lhs: Union[F, Value], rhs: Union[F, Value], op: str, distance: float, units: str
) -> Q:
    if not isinstance(lhs, F):
        lhs, rhs = rhs, lhs

    # if neither lhs and rhs are fields, we have to fail here
    if not isinstance(lhs, F):
        raise ValueError(f"Unable to compare non-field {lhs}")

    # TODO: maybe use D.unit_attname(units)
    d = D(**{UNITS_LOOKUP[units]: distance})
    if op == "DWITHIN":
        return Q(**{"%s__distance_lte" % lhs.name: (rhs, d, "spheroid")})
    return Q(**{"%s__distance_gte" % lhs.name: (rhs, d, "spheroid")})


def bbox(
    lhs: F,
    minx: float,
    miny: float,
    maxx,
    maxy: float,
    crs: Optional[str] = None,
    bboverlaps: bool = True,
) -> Q:
    """Create a bounding box filter for the given spatial attribute.

    :param lhs: the field to compare
    :param minx: the lower x part of the bbox
    :type minx: float
    :param miny: the lower y part of the bbox
    :type miny: float
    :param maxx: the upper x part of the bbox
    :type maxx: float
    :param maxy: the upper y part of the bbox
    :type maxy: float
    :param crs: the CRS the bbox is expressed in
    :type crs: str
    :type lhs: :class:`django.db.models.F`
    :return: a comparison expression object
    :rtype: :class:`django.db.models.Q`
    """
    box = Polygon.from_bbox((minx, miny, maxx, maxy))

    if crs:
        box.srid = SpatialReference(crs).srid
        box.transform(4326)

    if bboverlaps:
        return Q(**{"%s__bboverlaps" % lhs.name: box})
    return Q(**{"%s__intersects" % lhs.name: box})


def attribute(name: str, field_mapping: Optional[Dict[str, str]] = None) -> F:
    """Create an attribute lookup expression using a field mapping dictionary.

    :param name: the field filter name
    :type name: str
    :param field_mapping: the dictionary to use as a lookup.
    :rtype: :class:`django.db.models.F`
    """
    if field_mapping:
        field = field_mapping.get(name, name)
    else:
        field = name
    return F(field)


def literal(value) -> Value:
    return Value(value)


OP_TO_FUNC = {"+": add, "-": sub, "*": mul, "/": truediv}


def arithmetic(lhs: ArithmeticType, rhs: ArithmeticType, op: str) -> ArithmeticType:
    """Create an arithmetic filter

    :param lhs: left hand side of the arithmetic expression. either a
                scalar or a field lookup or another type of expression
    :param rhs: same as `lhs`
    :param op: the arithmetic operation. one of ``"+"``, ``"-"``, ``"*"``,
               ``"/"``
    :rtype: :class:`django.db.models.F`
    """
    func = OP_TO_FUNC[op]
    return func(lhs, rhs)
