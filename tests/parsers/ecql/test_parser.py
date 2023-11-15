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

from dateparser.timezone_parser import StaticTzInfo
from pygeoif import geometry

from pygeofilter import ast, values
from pygeofilter.parsers.ecql import parse


def test_namespace_attribute_eq_literal():
    result = parse("ns:attr = 'A'")
    assert result == ast.Equal(
        ast.Attribute("ns:attr"),
        "A",
    )


def test_attribute_eq_literal():
    result = parse("attr = 'A'")
    assert result == ast.Equal(
        ast.Attribute("attr"),
        "A",
    )


def test_attribute_lt_literal():
    result = parse("attr < 5")
    assert result == ast.LessThan(
        ast.Attribute("attr"),
        5.0,
    )


def test_attribute_lte_literal():
    result = parse("attr <= 5")
    assert result == ast.LessEqual(
        ast.Attribute("attr"),
        5.0,
    )


def test_attribute_gt_literal():
    result = parse("attr > 5")
    assert result == ast.GreaterThan(
        ast.Attribute("attr"),
        5.0,
    )


def test_attribute_gte_literal():
    result = parse("attr >= 5")
    assert result == ast.GreaterEqual(
        ast.Attribute("attr"),
        5.0,
    )


def test_attribute_ne_literal():
    result = parse("attr <> 5")
    assert result == ast.NotEqual(
        ast.Attribute("attr"),
        5,
    )


def test_attribute_between():
    result = parse("attr BETWEEN 2 AND 5")
    assert result == ast.Between(
        ast.Attribute("attr"),
        2,
        5,
        False,
    )


def test_attribute_not_between():
    result = parse("attr NOT BETWEEN 2 AND 5")
    assert result == ast.Between(
        ast.Attribute("attr"),
        2,
        5,
        True,
    )


def test_attribute_between_negative_positive():
    result = parse("attr BETWEEN -1 AND 1")
    assert result == ast.Between(
        ast.Attribute("attr"),
        -1,
        1,
        False,
    )


def test_string_like():
    result = parse("attr LIKE 'some%'")
    assert result == ast.Like(
        ast.Attribute("attr"),
        "some%",
        nocase=False,
        not_=False,
        wildcard="%",
        singlechar=".",
        escapechar="\\",
    )


def test_string_ilike():
    result = parse("attr ILIKE 'some%'")
    assert result == ast.Like(
        ast.Attribute("attr"),
        "some%",
        nocase=True,
        not_=False,
        wildcard="%",
        singlechar=".",
        escapechar="\\",
    )


def test_string_not_like():
    result = parse("attr NOT LIKE 'some%'")
    assert result == ast.Like(
        ast.Attribute("attr"),
        "some%",
        nocase=False,
        not_=True,
        wildcard="%",
        singlechar=".",
        escapechar="\\",
    )


def test_string_not_ilike():
    result = parse("attr NOT ILIKE 'some%'")
    assert result == ast.Like(
        ast.Attribute("attr"),
        "some%",
        nocase=True,
        not_=True,
        wildcard="%",
        singlechar=".",
        escapechar="\\",
    )


def test_attribute_in_list():
    result = parse("attr IN (1, 2, 3, 4)")
    assert result == ast.In(
        ast.Attribute("attr"),
        [
            1,
            2,
            3,
            4,
        ],
        False,
    )


def test_attribute_not_in_list():
    result = parse("attr NOT IN ('A', 'B', 'C', 'D')")
    assert result == ast.In(
        ast.Attribute("attr"),
        [
            "A",
            "B",
            "C",
            "D",
        ],
        True,
    )


def test_attribute_is_null():
    result = parse("attr IS NULL")
    assert result == ast.IsNull(ast.Attribute("attr"), False)


def test_attribute_is_not_null():
    result = parse("attr IS NOT NULL")
    assert result == ast.IsNull(ast.Attribute("attr"), True)


def test_attribute_exists():
    result = parse("attr EXISTS")
    assert result == ast.Exists(ast.Attribute("attr"), False)


def test_attribute_does_not_exist():
    result = parse("attr DOES-NOT-EXIST")
    assert result == ast.Exists(ast.Attribute("attr"), True)


def test_include():
    result = parse("INCLUDE")
    assert result == ast.Include(False)


def test_exclude():
    result = parse("EXCLUDE")
    assert result == ast.Include(True)


# Temporal predicate


def test_attribute_before():
    result = parse("attr BEFORE 2000-01-01T00:00:01Z")
    assert result == ast.TimeBefore(
        ast.Attribute("attr"),
        datetime(2000, 1, 1, 0, 0, 1, tzinfo=StaticTzInfo("Z", timedelta(0))),
    )


def test_attribute_before_or_during_dt_dt():
    result = parse("attr BEFORE OR DURING 2000-01-01T00:00:00Z / 2000-01-01T00:00:01Z")
    assert result == ast.TimeBeforeOrDuring(
        ast.Attribute("attr"),
        values.Interval(
            datetime(2000, 1, 1, 0, 0, 0, tzinfo=StaticTzInfo("Z", timedelta(0))),
            datetime(2000, 1, 1, 0, 0, 1, tzinfo=StaticTzInfo("Z", timedelta(0))),
        ),
    )


def test_attribute_before_or_during_dt_dr():
    result = parse("attr BEFORE OR DURING 2000-01-01T00:00:00Z / PT4S")
    assert result == ast.TimeBeforeOrDuring(
        ast.Attribute("attr"),
        values.Interval(
            datetime(2000, 1, 1, 0, 0, 0, tzinfo=StaticTzInfo("Z", timedelta(0))),
            timedelta(seconds=4),
        ),
    )


def test_attribute_before_or_during_dr_dt():
    result = parse("attr BEFORE OR DURING PT4S / 2000-01-01T00:00:03Z")
    assert result == ast.TimeBeforeOrDuring(
        ast.Attribute("attr"),
        values.Interval(
            timedelta(seconds=4),
            datetime(2000, 1, 1, 0, 0, 3, tzinfo=StaticTzInfo("Z", timedelta(0))),
        ),
    )


# Spatial predicate


def test_intersects_attr_point():
    result = parse("INTERSECTS(geometry, POINT(1 1))")
    assert result == ast.GeometryIntersects(
        ast.Attribute("geometry"),
        values.Geometry(geometry.Point(1, 1).__geo_interface__),
    )


def test_disjoint_linestring_attr():
    result = parse("DISJOINT(LINESTRING(1 1,2 2), geometry)")
    assert result == ast.GeometryDisjoint(
        values.Geometry(
            geometry.LineString([(1, 1), (2, 2)]).__geo_interface__,
        ),
        ast.Attribute("geometry"),
    )


def test_contains_attr_polygon():
    result = parse("CONTAINS(geometry, POLYGON((1 1,2 2,0 3,1 1)))")
    assert result == ast.GeometryContains(
        ast.Attribute("geometry"),
        values.Geometry(
            geometry.Polygon([(1, 1), (2, 2), (0, 3), (1, 1)]).__geo_interface__,
        ),
    )


def test_within_multipolygon_attr():
    result = parse("WITHIN(MULTIPOLYGON(((1 1,2 2,0 3,1 1))), geometry)")
    assert result == ast.GeometryWithin(
        values.Geometry(
            geometry.MultiPolygon.from_polygons(
                geometry.Polygon([(1, 1), (2, 2), (0, 3), (1, 1)])
            ).__geo_interface__,
        ),
        ast.Attribute("geometry"),
    )


def test_touches_attr_multilinestring():
    result = parse("TOUCHES(geometry, MULTILINESTRING((1 1,2 2),(0 3,1 1)))")
    assert result == ast.GeometryTouches(
        ast.Attribute("geometry"),
        values.Geometry(
            geometry.MultiLineString.from_linestrings(
                geometry.LineString([(1, 1), (2, 2)]),
                geometry.LineString([(0, 3), (1, 1)]),
            ).__geo_interface__,
        ),
    )


def test_crosses_attr_multilinestring():
    result = parse("CROSSES(geometry, MULTILINESTRING((1 1,2 2),(0 3,1 1)))")
    assert result == ast.GeometryCrosses(
        ast.Attribute("geometry"),
        values.Geometry(
            geometry.MultiLineString.from_linestrings(
                geometry.LineString([(1, 1), (2, 2)]),
                geometry.LineString([(0, 3), (1, 1)]),
            ).__geo_interface__,
        ),
    )


def test_overlaps_attr_multilinestring():
    result = parse("OVERLAPS(geometry, MULTILINESTRING((1 1,2 2),(0 3,1 1)))")
    assert result == ast.GeometryOverlaps(
        ast.Attribute("geometry"),
        values.Geometry(
            geometry.MultiLineString.from_linestrings(
                geometry.LineString([(1, 1), (2, 2)]),
                geometry.LineString([(0, 3), (1, 1)]),
            ).__geo_interface__,
        ),
    )


def test_intersects_attr_point_ewkt():
    result = parse("INTERSECTS(geometry, SRID=4326;POINT(1 1))")
    assert (
        result.rhs.geometry["crs"]["properties"]["name"] == "urn:ogc:def:crs:EPSG::4326"
    )
    assert result == ast.GeometryIntersects(
        ast.Attribute("geometry"),
        values.Geometry(geometry.Point(1, 1).__geo_interface__),
    )


def test_intersects_attr_geometrycollection():
    result = parse(
        "INTERSECTS(geometry, GEOMETRYCOLLECTION(POINT(1 1),"
        "LINESTRING(1 1,2 2),"
        "POLYGON((1 1,2 2,0 3,1 1))"
        "))"
    )
    assert result == ast.GeometryIntersects(
        ast.Attribute("geometry"),
        values.Geometry(
            geometry.GeometryCollection(
                [
                    geometry.Point(1, 1),
                    geometry.LineString([(1, 1), (2, 2)]),
                    geometry.Polygon([(1, 1), (2, 2), (0, 3), (1, 1)]),
                ]
            ).__geo_interface__
        ),
    )


# relate


def test_relate_attr_polygon():
    result = parse("RELATE(geometry, POLYGON((1 1,2 2,0 3,1 1)), '1*T***T**')")
    assert result == ast.Relate(
        ast.Attribute("geometry"),
        values.Geometry(
            geometry.Polygon([(1, 1), (2, 2), (0, 3), (1, 1)]).__geo_interface__,
        ),
        pattern="1*T***T**",
    )


# dwithin/beyond


def test_dwithin_attr_polygon():
    result = parse("DWITHIN(geometry, POLYGON((1 1,2 2,0 3,1 1)), 5, feet)")
    assert result == ast.DistanceWithin(
        ast.Attribute("geometry"),
        values.Geometry(
            geometry.Polygon([(1, 1), (2, 2), (0, 3), (1, 1)]).__geo_interface__,
        ),
        distance=5,
        units="feet",
    )


def test_beyond_attr_polygon():
    result = parse("BEYOND(geometry, POLYGON((1 1,2 2,0 3,1 1)), 5, nautical miles)")
    assert result == ast.DistanceBeyond(
        ast.Attribute("geometry"),
        values.Geometry(
            geometry.Polygon([(1, 1), (2, 2), (0, 3), (1, 1)]).__geo_interface__,
        ),
        distance=5,
        units="nautical miles",
    )


# BBox prediacte


def test_bbox_simple():
    result = parse("BBOX(geometry, 1, 2, 3, 4)")
    assert result == ast.BBox(
        ast.Attribute("geometry"),
        1,
        2,
        3,
        4,
    )


def test_bbox_crs():
    result = parse("BBOX(geometry, 1, 2, 3, 4, 'EPSG:3875')")
    assert result == ast.BBox(
        ast.Attribute("geometry"),
        1,
        2,
        3,
        4,
        "EPSG:3875",
    )


def test_bbox_negative():
    result = parse("BBOX(geometry, -3, -4, -1, -2, 'EPSG:3875')")
    assert result == ast.BBox(
        ast.Attribute("geometry"),
        -3,
        -4,
        -1,
        -2,
        "EPSG:3875",
    )


def test_attribute_arithmetic_add():
    result = parse("attr = 5 + 2")
    assert result == ast.Equal(
        ast.Attribute("attr"),
        ast.Add(
            5,
            2,
        ),
    )


def test_attribute_arithmetic_sub():
    result = parse("attr = 5 - 2")
    assert result == ast.Equal(
        ast.Attribute("attr"),
        ast.Sub(
            5,
            2,
        ),
    )


def test_attribute_arithmetic_mul():
    result = parse("attr = 5 * 2")
    assert result == ast.Equal(
        ast.Attribute("attr"),
        ast.Mul(
            5,
            2,
        ),
    )


def test_attribute_arithmetic_div():
    result = parse("attr = 5 / 2")
    assert result == ast.Equal(
        ast.Attribute("attr"),
        ast.Div(
            5,
            2,
        ),
    )


def test_attribute_arithmetic_add_mul():
    result = parse("attr = 3 + 5 * 2")
    assert result == ast.Equal(
        ast.Attribute("attr"),
        ast.Add(
            3,
            ast.Mul(
                5,
                2,
            ),
        ),
    )


def test_attribute_arithmetic_div_sub():
    result = parse("attr = 3 / 5 - 2")
    assert result == ast.Equal(
        ast.Attribute("attr"),
        ast.Sub(
            ast.Div(
                3,
                5,
            ),
            2,
        ),
    )


def test_attribute_arithmetic_div_sub_bracketted():
    result = parse("attr = 3 / (5 - 2)")
    assert result == ast.Equal(
        ast.Attribute("attr"),
        ast.Div(
            3,
            ast.Sub(
                5,
                2,
            ),
        ),
    )


# test function expression parsing


def test_function_no_arg():
    result = parse("attr = myfunc()")
    assert result == ast.Equal(
        ast.Attribute("attr"),
        ast.Function("myfunc", []),
    )


def test_function_single_arg():
    result = parse("attr = myfunc(1)")
    assert result == ast.Equal(
        ast.Attribute("attr"),
        ast.Function(
            "myfunc",
            [
                1,
            ],
        ),
    )


def test_function_attr_string_arg():
    result = parse("attr = myfunc(other_attr, 'abc')")
    assert result == ast.Equal(
        ast.Attribute("attr"),
        ast.Function(
            "myfunc",
            [
                ast.Attribute("other_attr"),
                "abc",
            ],
        ),
    )
