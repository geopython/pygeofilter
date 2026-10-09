"""Unit conversion for the SQLAlchemy backend's distance predicates.

Kept out of ``test_evaluate.py`` on purpose: that module is skipped wholesale
when ``mod_spatialite`` is missing and it comments out its ``DWITHIN`` cases
because spatialite has no ``ST_DWithin``. The conversion below needs neither a
database nor a spatial extension, so it is covered here and runs everywhere.
"""

import pytest
from geoalchemy2 import Geometry
from sqlalchemy import Column, MetaData, String, Table

from pygeofilter.backends.sqlalchemy import filters
from pygeofilter.backends.sqlalchemy.evaluate import to_filter
from pygeofilter.parsers.ecql import parse as parse_ecql


class _Expression:
    """Stand-in for the expression an operator returns.

    ``BEYOND`` negates the operator's result, so the fake survives ``~``.
    """

    def __init__(self, distance=None):
        self.distance = distance

    def __invert__(self):
        return self


class _GeometryColumn:
    """Records the radius handed to ``ST_Dwithin`` instead of building SQL."""

    def __init__(self):
        self.distance = None

    def ST_Dwithin(self, other, distance):
        self.distance = distance
        return _Expression(distance)

    def ST_Intersects(self, other):
        return _Expression()


@pytest.mark.parametrize(
    "units, distance, expected",
    [
        ("meters", 10, 10.0),
        ("kilometers", 5, 5000.0),
        ("feet", 100, 30.48),
        ("miles", 1, 1609.344),
        ("statute miles", 1, 1609.344),
        ("nautical miles", 1, 1852.0),
        ("furlongs", 3, 3.0),  # unknown units pass through unchanged
        (None, 10, 10),  # no units: value untouched
    ],
)
def test_dwithin_converts_to_metres(units, distance, expected):
    column = _GeometryColumn()
    filters.spatial(
        column, "POINT(0 0)", "DWITHIN", distance=distance, units=units
    )
    assert column.distance == pytest.approx(expected)


@pytest.mark.parametrize(
    "units, distance, expected",
    [("kilometers", 5, 5000.0), ("nautical miles", 2, 3704.0), (None, 7, 7)],
)
def test_beyond_converts_to_metres(units, distance, expected):
    column = _GeometryColumn()
    filters.spatial(
        column, "POINT(0 0)", "BEYOND", distance=distance, units=units
    )
    assert column.distance == pytest.approx(expected)


def test_non_distance_operator_leaves_no_radius():
    column = _GeometryColumn()
    filters.spatial(column, "POINT(0 0)", "INTERSECTS")
    assert column.distance is None


def _compiled_sql(cql: str) -> str:
    table = Table(
        "record",
        MetaData(),
        Column("identifier", String, primary_key=True),
        Column("geometry", Geometry(geometry_type="MULTIPOLYGON", srid=4326)),
    )
    ast = parse_ecql(cql)
    statement = to_filter(ast, field_mapping={"geometry": table.c.geometry})
    return str(statement.compile(compile_kwargs={"literal_binds": True}))


@pytest.mark.parametrize(
    "distance, units, expected, wrong",
    [
        (5, "kilometers", "5000", "0.005"),
        (100, "feet", "30.48", "328.084"),
    ],
)
def test_distance_reaches_sql_in_metres(distance, units, expected, wrong):
    """End-to-end: the radius must be multiplied, not divided."""
    sql = _compiled_sql(f"DWITHIN(geometry, POINT(0 0), {distance}, {units})")
    assert expected in sql
    assert wrong not in sql
