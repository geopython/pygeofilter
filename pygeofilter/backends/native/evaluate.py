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

from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Callable, Dict, Optional, Tuple, Union

import shapely.geometry

from ... import ast, values
from ...util import like_pattern_to_re, parse_datetime
from ..evaluator import Evaluator, handle

COMPARISON_MAP = {
    ast.ComparisonOp.EQ: "==",
    ast.ComparisonOp.NE: "!=",
    ast.ComparisonOp.LT: "<",
    ast.ComparisonOp.LE: "<=",
    ast.ComparisonOp.GT: ">",
    ast.ComparisonOp.GE: ">=",
}

ARITHMETIC_MAP = {
    ast.ArithmeticOp.ADD: "+",
    ast.ArithmeticOp.SUB: "-",
    ast.ArithmeticOp.MUL: "*",
    ast.ArithmeticOp.DIV: "/",
}

ARRAY_COMPARISON_OP_MAP = {
    ast.ArrayComparisonOp.AEQUALS: "==",
    ast.ArrayComparisonOp.ACONTAINS: ">=",
    ast.ArrayComparisonOp.ACONTAINEDBY: "<=",
    ast.ArrayComparisonOp.AOVERLAPS: "&",
}


class NativeEvaluator(Evaluator):
    """This evaluator type allows to create a filter that can be used to
    filter objects or dicts.

    The filter is built using Python expressions which are then parsed
    using eval. The result is a callable object that can be used in any
    circumstance a normal function would.
    The callable object accepts a single parameter: the object to filter
    and returns a boolean if the object matches the filters or not.
    """

    def __init__(
        self,
        function_map: Optional[Dict[str, Callable]] = None,
        attribute_map: Optional[Dict[str, str]] = None,
        use_getattr: bool = True,
        allow_nested_attributes: bool = True,
    ):
        """Constructs a NativeEvaluator.

        Args:
            function_map: a mapping of a function name to a callable
                function.
            attribute_map: a mapping of an external name to an internal
                field of the item to be filtered. The internal field
                specifier can be a JSON-Path that will be resolved against
                the passed in item.
        """
        self.function_map = function_map if function_map is not None else {}
        self.attribute_map = attribute_map
        self.use_getattr = use_getattr
        self.allow_nested_attributes = allow_nested_attributes
        self.locals: Dict[str, Any] = {}
        self.local_count = 0

    def _add_local(self, value: Any) -> str:
        "Add a value as a local variable to the expression."
        self.local_count += 1
        key = f"local_{self.local_count}"
        self.locals[key] = value
        return key

    def _resolve_attribute(self, name):
        """Helper to resolve an attribute, either directly or via the
        integrated ``attribute_map``
        """
        if self.attribute_map is not None:
            if name in self.attribute_map:
                path = self.attribute_map[name]
            elif "*" in self.attribute_map:
                path = self.attribute_map["*"].replace("*", name)
            allow_nested_attributes = True
        else:
            path = name
            allow_nested_attributes = self.allow_nested_attributes

        parts = path.split(".")
        if not allow_nested_attributes and len(parts) > 1:
            raise Exception("Nested attributes are not allowed")

        return parts

    @handle(ast.Not)
    def not_(self, node, sub):
        return f"(not {sub})"

    @handle(ast.And)
    def and_(self, node, lhs, rhs):
        return f"({lhs} and {rhs})"

    @handle(ast.Or)
    def or_(self, node, lhs, rhs):
        return f"({lhs} or {rhs})"

    @handle(ast.Comparison, subclasses=True)
    def comparison(self, node, lhs, rhs):
        op = COMPARISON_MAP[node.op]
        return f"({lhs} {op} {rhs})"

    @handle(ast.Between)
    def between(self, node, lhs, low, high):
        if node.not_:
            return f"({low} > {lhs} or {lhs} > {high})"
        else:
            return f"({low} <= {lhs} <= {high})"

    @handle(ast.Like)
    def like(self, node, lhs):
        maybe_not_inv = "" if node.not_ else "not "
        regex = like_pattern_to_re(
            node.pattern, node.nocase, node.wildcard, node.singlechar, node.escapechar
        )
        key = self._add_local(regex)
        return f"({key}.match({lhs}) is {maybe_not_inv}None)"

    @handle(ast.In)
    def in_(self, node, lhs, *options):
        maybe_not = "not" if node.not_ else ""
        opts = ", ".join([f"{opt}" for opt in options])
        return f"({lhs} {maybe_not} in ({opts}))"

    @handle(ast.IsNull)
    def null(self, node, lhs):
        maybe_not = "not " if node.not_ else ""
        return f"({lhs} is {maybe_not}None)"

    @handle(ast.Exists)
    def exists(self, node, lhs):
        parts = self._resolve_attribute(node.lhs.name)
        maybe_not = "not " if node.not_ else ""
        if self.use_getattr:
            cur = "item"
            for part in parts[:-1]:
                cur = f"getattr({cur}, {part!r}, None)"
            return f"({maybe_not}hasattr({cur}, {parts[-1]!r}))"
        else:
            getters = "".join(f".get({part!r}, {{}})" for part in parts[:-1])
            return f"{parts[-1]!r} {maybe_not}in item{getters}"

    @handle(ast.TemporalPredicate, subclasses=True)
    def temporal(self, node, lhs, rhs):
        return (
            f"(relate_intervals(to_interval({lhs}),"
            f"to_interval({rhs})) == "
            f"ast.TemporalComparisonOp.{node.op.name})"
        )

    @handle(ast.ArrayPredicate, subclasses=True)
    def array(self, node, lhs, rhs):
        op = ARRAY_COMPARISON_OP_MAP[node.op]
        return f"bool(set({lhs}) {op} set({rhs}))"

    @handle(ast.SpatialComparisonPredicate, subclasses=True)
    def spatial_operation(self, node, lhs, rhs):
        return f"(getattr(ensure_spatial({lhs}), " f"{node.op.value.lower()!r})({rhs}))"

    @handle(ast.Relate)
    def spatial_pattern(self, node, lhs, rhs):
        return f"(ensure_spatial({lhs}).relate_pattern({rhs}, {node.pattern!r}))"

    @handle(ast.BBox)
    def bbox(self, node, lhs):
        bbox_local = self._add_local(
            shapely.geometry.Polygon.from_bounds(
                node.minx, node.miny, node.maxx, node.maxy
            )
        )
        return f"(ensure_spatial({lhs}).intersects({bbox_local}))"

    @handle(ast.Attribute)
    def attribute(self, node):
        parts = self._resolve_attribute(node.name)
        if self.use_getattr:
            cur = "item"
            for part in parts:
                cur = f"getattr({cur}, {part!r}, None)"
            return cur
        else:
            getters = "".join(f".get({part!r})" for part in parts)
            return f"item{getters}"

    @handle(ast.Arithmetic, subclasses=True)
    def arithmetic(self, node, lhs, rhs):
        op = ARITHMETIC_MAP[node.op]
        return f"({lhs}) {op} ({rhs})"

    @handle(ast.Function)
    def function(self, node, *arguments):
        args = ", ".join([f"({arg})" for arg in arguments])
        return f"{node.name}({args})"

    @handle(*values.LITERALS)
    def literal(self, node):
        key = self._add_local(node)
        return key

    @handle(values.Interval)
    def interval(self, node, low, high):
        return f"values.Interval({low}, {high})"

    @handle(values.Geometry)
    def geometry(self, node):
        key = self._add_local(shapely.geometry.shape(node))
        return key

    @handle(values.Envelope)
    def envelope(self, node):
        key = self._add_local(
            shapely.geometry.Polygon.from_bounds(node.x1, node.y1, node.x2, node.y2)
        )
        return key

    def adopt_result(self, result):
        """Turns the compiled expression into a callable object using
        ``eval``. Literals are passed in as well as the function map.
        """
        expression = f"lambda item: {result}"
        globals_ = {
            "relate_intervals": relate_intervals,
            "to_interval": to_interval,
            "ensure_spatial": ensure_spatial,
            "ast": ast,
            "values": values,
        }
        if not set(globals_).isdisjoint(set(self.function_map)):
            raise ValueError(
                f"globals collision {list(globals_)} and " f"{list(self.function_map)}"
            )

        globals_.update(self.function_map)
        globals_.update(self.locals)

        # clear any locals for later use
        self.locals.clear()

        return eval(expression, globals_)


MaybeInterval = Union[values.Interval, date, datetime, str, None]
InternalInterval = Tuple[Optional[datetime], Optional[datetime]]


def _interval_to_internal_interval(value: values.Interval) -> InternalInterval:
    low = value.start
    high = value.end

    # convert low and high dates to their respective datetime
    # by using 00:00 time for the low part and 23:59:59 for the high
    # part
    if isinstance(low, date):
        low = datetime.combine(low, time.min, timezone.utc)
    if isinstance(high, date):
        high = datetime.combine(high, time.max, timezone.utc)

    # low and high are now either datetimes, timedeltas or None

    if isinstance(low, timedelta):
        if isinstance(high, datetime):
            low = high - low
        else:
            raise ValueError(f"Cannot combine {low} with {high}")
    elif isinstance(high, timedelta):
        if isinstance(low, datetime):
            high = low + high
        else:
            raise ValueError(f"Cannot combine {low} with {high}")

    return (low, high)


def to_interval(value: MaybeInterval) -> InternalInterval:
    """Converts the given value to an interval tuple of ``start``/``stop``
    as Python datetime objects.

    - ``values.Interval`` objects are expanded to two datetimes:
        - two datetimes are returned as such
        - a date is transformed to a datetime, where the ``time``
          component is either ``time.min`` for start or ``time.max``
          for then end component.
        - if either the start or end is a ``timedelta`` object, that value
          is either added to the start value or subtracted from the end
          value.
    - ``date`` objects are transformed to two datetimes for the
      ``time.min`` and ``time.end`` of that date in UTC.
    - ``datetime`` and ``str`` objects are an interval with both
      start and end of the same value. Strings are parsed beforehand.
    - ``None`` is simply returned as ``(None, None)``
    """

    if isinstance(value, str):
        value = parse_datetime(value)
        if not value.tzinfo:
            value = value.replace(tzinfo=timezone.utc)
        return (value, value)

    elif isinstance(value, values.Interval):
        return _interval_to_internal_interval(value)

    elif isinstance(value, datetime):
        return (value, value)

    elif isinstance(value, date):
        return (
            datetime.combine(value, time.min, timezone.utc),
            datetime.combine(value, time.max, timezone.utc),
        )

    elif value is None:
        return (None, None)

    raise ValueError(f"Invalid type {type(value)}")


def relate_intervals(  # noqa: C901
    lhs: InternalInterval, rhs: InternalInterval
) -> ast.TemporalComparisonOp:
    """Relates two intervals (tuples of two ``datetime`` or ``None`` values)
    and returns the associated ``ast.TemporalComparisonOp`` value.
    """
    ll, lh = lhs
    rl, rh = rhs
    if ll is None or lh is None or rl is None or rh is None:
        # TODO: handle open ended intervals (None on either side)
        return ast.TemporalComparisonOp.DISJOINT
    elif lh < rl:
        return ast.TemporalComparisonOp.BEFORE
    elif ll > rh:
        return ast.TemporalComparisonOp.AFTER
    elif lh == rl:
        return ast.TemporalComparisonOp.MEETS
    elif ll == rh:
        return ast.TemporalComparisonOp.METBY
    elif ll < rl and rl < lh < rh:
        return ast.TemporalComparisonOp.TOVERLAPS
    elif rl < ll < rh and lh > rh:
        return ast.TemporalComparisonOp.OVERLAPPEDBY
    elif ll == rl and lh < rh:
        return ast.TemporalComparisonOp.BEGINS
    elif ll == rl and lh > rh:
        return ast.TemporalComparisonOp.BEGUNBY
    elif ll > rl and lh < rh:
        return ast.TemporalComparisonOp.DURING
    elif ll < rl and lh > rh:
        return ast.TemporalComparisonOp.TCONTAINS
    elif ll > rl and lh == rh:
        return ast.TemporalComparisonOp.ENDS
    elif ll < rl and lh == rh:
        return ast.TemporalComparisonOp.ENDEDBY
    elif ll == rl and lh == rh:
        return ast.TemporalComparisonOp.TEQUALS

    raise ValueError(f"Error relating intervals [{ll}, {lh}] and [{rl}, {rh}]")


def ensure_spatial(value: Any) -> shapely.geometry.base.BaseGeometry:
    """Ensures that a given value is a shapely geometry. If it is already
    it is passed through, otherwise it is tried to be parsed via
    ``shapely.geometry.shape``.
    """
    if isinstance(value, shapely.geometry.base.BaseGeometry):
        return value
    return shapely.geometry.shape(value)
