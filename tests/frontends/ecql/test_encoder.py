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
from pygeofilter.frontends.ecql.encoder import encode


def test_attribute_eq_literal():
    assert encode(
        ast.Equal(
            ast.Attribute("attr"),
            "A",
        )
    ) == "attr = 'A'"


def test_attribute_lt_literal():
    assert encode(
        ast.LessThan(
            ast.Attribute("attr"),
            5.0,
        )
    ) == "attr < 5"


def test_attribute_lte_literal():
    assert encode(
        ast.LessEqual(
            ast.Attribute("attr"),
            5.0,
        )
    ) == "attr <= 5"


def test_attribute_gt_literal():
    assert encode(
        ast.GreaterThan(
            ast.Attribute("attr"),
            5.0,
        )
    ) == "attr > 5"


def test_attribute_gte_literal():
    assert encode(
        ast.GreaterEqual(
            ast.Attribute("attr"),
            5.0,
        )
    ) == "attr >= 5"


def test_attribute_ne_literal():
    assert encode(
        ast.NotEqual(
            ast.Attribute("attr"),
            5,
        )
    ) == "attr <> 5"


def test_attribute_between():
    assert encode(
        ast.Between(
            ast.Attribute("attr"),
            2,
            5,
            False,
        )
    ) == "attr BETWEEN 2 AND 5"


def test_attribute_not_between():
    assert encode(
        ast.Between(
            ast.Attribute("attr"),
            2,
            5,
            True,
        )
    ) == "attr NOT BETWEEN 2 AND 5"


def test_attribute_between_negative_positive():
    assert encode(
        ast.Between(
            ast.Attribute("attr"),
            -1,
            1,
            False,
        )
    ) == "attr BETWEEN -1 AND 1"


def test_string_like():
    assert encode(
        ast.Like(
            ast.Attribute("attr"),
            "some%",
            nocase=False,
            not_=False,
            wildcard="%",
            singlechar=".",
            escapechar="\\",
        )
    ) == "attr LIKE 'some%'"


def test_string_ilike():
    assert encode(
        ast.Like(
            ast.Attribute("attr"),
            "some%",
            nocase=True,
            not_=False,
            wildcard="%",
            singlechar=".",
            escapechar="\\",
        )
    ) == "attr ILIKE 'some%'"


def test_string_not_like():
    assert encode(
        ast.Like(
            ast.Attribute("attr"),
            "some%",
            nocase=False,
            not_=True,
            wildcard="%",
            singlechar=".",
            escapechar="\\",
        )
    ) == "attr NOT LIKE 'some%'"


def test_string_not_ilike():
    assert encode(
        ast.Like(
            ast.Attribute("attr"),
            "some%",
            nocase=True,
            not_=True,
            wildcard="%",
            singlechar=".",
            escapechar="\\",
        )
    ) == "attr NOT ILIKE 'some%'"


def test_attribute_in_list():
    assert encode(
        ast.In(
            ast.Attribute("attr"),
            [
                1,
                2,
                3,
                4,
            ],
            False,
        )
    ) == "attr IN (1, 2, 3, 4)"


def test_attribute_not_in_list():
    assert encode(
        ast.In(
            ast.Attribute("attr"),
            [
                "A",
                "B",
                "C",
                "D",
            ],
            True,
        )
    ) == "attr NOT IN ('A', 'B', 'C', 'D')"


def test_attribute_is_null():
    assert encode(ast.IsNull(ast.Attribute("attr"), False)) == "attr IS NULL"


def test_attribute_is_not_null():
    assert encode(ast.IsNull(ast.Attribute("attr"), True)) == "attr IS NOT NULL"


def test_attribute_exists():
    assert encode(ast.Exists(ast.Attribute("attr"), False)) == "attr EXISTS"


def test_attribute_does_not_exist():
    assert encode(ast.Exists(ast.Attribute("attr"), True)) == "attr DOES-NOT-EXIST"


def test_include():
    assert encode(ast.Include(False)) == "INCLUDE"


def test_exclude():
    assert encode(ast.Include(True)) == "EXCLUDE"


# Temporal predicate


def test_attribute_before():
    assert encode(
        ast.TimeBefore(
            ast.Attribute("attr"),
            datetime(2000, 1, 1, 0, 0, 1, tzinfo=StaticTzInfo("Z", timedelta(0))),
        )
    ) == "attr BEFORE 2000-01-01T00:00:01Z"


def test_attribute_before_or_during_dt_dt():
    assert encode(
        ast.TimeBeforeOrDuring(
            ast.Attribute("attr"),
            values.Interval(
                datetime(2000, 1, 1, 0, 0, 0, tzinfo=StaticTzInfo("Z", timedelta(0))),
                datetime(2000, 1, 1, 0, 0, 1, tzinfo=StaticTzInfo("Z", timedelta(0))),
            ),
        )
    ) == "attr BEFORE OR DURING 2000-01-01T00:00:00Z / 2000-01-01T00:00:01Z"


def test_attribute_before_or_during_dt_dr():
    assert encode(
        ast.TimeBeforeOrDuring(
            ast.Attribute("attr"),
            values.Interval(
                datetime(2000, 1, 1, 0, 0, 0, tzinfo=StaticTzInfo("Z", timedelta(0))),
                timedelta(seconds=4),
            ),
        )
    ) == "attr BEFORE OR DURING 2000-01-01T00:00:00Z / PT4S"


def test_attribute_before_or_during_dr_dt():
    assert encode(
        ast.TimeBeforeOrDuring(
            ast.Attribute("attr"),
            values.Interval(
                timedelta(seconds=4),
                datetime(2000, 1, 1, 0, 0, 3, tzinfo=StaticTzInfo("Z", timedelta(0))),
            ),
        )
    ) == "attr BEFORE OR DURING PT4S / 2000-01-01T00:00:03Z"


# Spatial predicate


def test_intersects_attr_point():
    assert encode(
        ast.GeometryIntersects(
            ast.Attribute("geometry"),
            values.Geometry(geometry.Point(1, 1).__geo_interface__),
        )
    ) == "INTERSECTS(geometry, POINT (1 1))"


def test_disjoint_linestring_attr():
    assert encode(
        ast.GeometryDisjoint(
            values.Geometry(
                geometry.LineString([(1, 1), (2, 2)]).__geo_interface__,
            ),
            ast.Attribute("geometry"),
        )
    ) == "DISJOINT(LINESTRING (1 1, 2 2), geometry)"


def test_contains_attr_polygon():
    assert encode(
        ast.GeometryContains(
            ast.Attribute("geometry"),
            values.Geometry(
                geometry.Polygon([(1, 1), (2, 2), (0, 3), (1, 1)]).__geo_interface__,
            ),
        )
    ) == "CONTAINS(geometry, POLYGON ((1 1, 2 2, 0 3, 1 1)))"


def test_within_multipolygon_attr():
    assert encode(
        ast.GeometryWithin(
            values.Geometry(
                geometry.MultiPolygon([
                    geometry.Polygon([(1, 1), (2, 2), (0, 3), (1, 1)])
                ]).__geo_interface__,
            ),
            ast.Attribute("geometry"),
        )
    ) == "WITHIN(MULTIPOLYGON (((1 1, 2 2, 0 3, 1 1))), geometry)"


def test_touches_attr_multilinestring():
    assert encode(
        ast.GeometryTouches(
            ast.Attribute("geometry"),
            values.Geometry(
                geometry.MultiLineString([
                    geometry.LineString([(1, 1), (2, 2)]),
                    geometry.LineString([(0, 3), (1, 1)]),
                ]).__geo_interface__,
            ),
        )
    ) == "TOUCHES(geometry, MULTILINESTRING ((1 1, 2 2), (0 3, 1 1)))"


def test_crosses_attr_multilinestring():
    assert encode(
        ast.GeometryCrosses(
            ast.Attribute("geometry"),
            values.Geometry(
                geometry.MultiLineString([
                    geometry.LineString([(1, 1), (2, 2)]),
                    geometry.LineString([(0, 3), (1, 1)]),
                ]).__geo_interface__,
            ),
        )
    ) == "CROSSES(geometry, MULTILINESTRING ((1 1, 2 2), (0 3, 1 1)))"


def test_overlaps_attr_multilinestring():
    assert encode(
        ast.GeometryOverlaps(
            ast.Attribute("geometry"),
            values.Geometry(
                geometry.MultiLineString([
                    geometry.LineString([(1, 1), (2, 2)]),
                    geometry.LineString([(0, 3), (1, 1)]),
                ]).__geo_interface__,
            ),
        )
    ) == "OVERLAPS(geometry, MULTILINESTRING ((1 1, 2 2), (0 3, 1 1)))"


# def test_intersects_attr_point_ewkt():
#     assert encode(
#         ast.GeometryIntersects(
#             ast.Attribute("geometry"),
#             values.Geometry(geometry.Point(1, 1).__geo_interface__),
#         )
#     ) == "INTERSECTS(geometry, SRID=4326;POINT (1 1))"


def test_intersects_attr_geometrycollection():
    assert encode(
        ast.GeometryIntersects(
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
    ) == (
        "INTERSECTS(geometry, GEOMETRYCOLLECTION (POINT (1 1), "
        "LINESTRING (1 1, 2 2), "
        "POLYGON ((1 1, 2 2, 0 3, 1 1))"
        "))"
    )


# relate


def test_relate_attr_polygon():
    assert encode(
        ast.Relate(
            ast.Attribute("geometry"),
            values.Geometry(
                geometry.Polygon([(1, 1), (2, 2), (0, 3), (1, 1)]).__geo_interface__,
            ),
            pattern="1*T***T**",
        )
    ) == "RELATE(geometry, POLYGON ((1 1, 2 2, 0 3, 1 1)), '1*T***T**')"


# dwithin/beyond


def test_dwithin_attr_polygon():
    assert encode(
        ast.DistanceWithin(
            ast.Attribute("geometry"),
            values.Geometry(
                geometry.Polygon([(1, 1), (2, 2), (0, 3), (1, 1)]).__geo_interface__,
            ),
            distance=5,
            units="feet",
        )
    ) == "DWITHIN(geometry, POLYGON ((1 1, 2 2, 0 3, 1 1)), 5, feet)"


def test_beyond_attr_polygon():
    assert encode(
        ast.DistanceBeyond(
            ast.Attribute("geometry"),
            values.Geometry(
                geometry.Polygon([(1, 1), (2, 2), (0, 3), (1, 1)]).__geo_interface__,
            ),
            distance=5,
            units="nautical miles",
        )
    ) == "BEYOND(geometry, POLYGON ((1 1, 2 2, 0 3, 1 1)), 5, nautical miles)"


# BBox prediacte


def test_bbox_simple():
    assert encode(
        ast.BBox(
            ast.Attribute("geometry"),
            1,
            2,
            3,
            4,
        )
    ) == "BBOX(geometry, 1, 2, 3, 4)"


def test_bbox_crs():
    assert encode(
        ast.BBox(
            ast.Attribute("geometry"),
            1,
            2,
            3,
            4,
            "EPSG:3875",
        )
    ) == "BBOX(geometry, 1, 2, 3, 4, 'EPSG:3875')"


def test_bbox_negative():
    assert encode(
        ast.BBox(
            ast.Attribute("geometry"),
            -3,
            -4,
            -1,
            -2,
            "EPSG:3875",
        )
    ) == "BBOX(geometry, -3, -4, -1, -2, 'EPSG:3875')"


def test_attribute_arithmetic_add():
    assert encode(
        ast.Equal(
            ast.Attribute("attr"),
            ast.Add(
                5,
                2,
            ),
        )
    ) == "attr = 5 + 2"


def test_attribute_arithmetic_sub():
    assert encode(
        ast.Equal(
            ast.Attribute("attr"),
            ast.Sub(
                5,
                2,
            ),
        )
    ) == "attr = 5 - 2"


def test_attribute_arithmetic_mul():
    assert encode(
        ast.Equal(
            ast.Attribute("attr"),
            ast.Mul(
                5,
                2,
            ),
        )
    ) == "attr = 5 * 2"


def test_attribute_arithmetic_div():
    assert encode(
        ast.Equal(
            ast.Attribute("attr"),
            ast.Div(
                5,
                2,
            ),
        )
    ) == "attr = 5 / 2"


def test_attribute_arithmetic_add_mul():
    assert encode(
        ast.Equal(
            ast.Attribute("attr"),
            ast.Add(
                3,
                ast.Mul(
                    5,
                    2,
                ),
            ),
        )
    ) == "attr = 3 + 5 * 2"


def test_attribute_arithmetic_div_sub():
    assert encode(
        ast.Equal(
            ast.Attribute("attr"),
            ast.Sub(
                ast.Div(
                    3,
                    5,
                ),
                2,
            ),
        )
    ) == "attr = 3 / 5 - 2"


def test_attribute_arithmetic_div_sub_bracketted():
    assert encode(
        ast.Equal(
            ast.Attribute("attr"),
            ast.Div(
                3,
                ast.Sub(
                    5,
                    2,
                ),
            ),
        )
    ) == "attr = 3 / (5 - 2)"


# test function expression parsing


def test_function_no_arg():
    assert encode(
        ast.Equal(
            ast.Attribute("attr"),
            ast.Function("myfunc", []),
        )
    ) == "attr = myfunc()"


def test_function_single_arg():
    assert encode(
        ast.Equal(
            ast.Attribute("attr"),
            ast.Function(
                "myfunc",
                [
                    1,
                ],
            ),
        )
    ) == "attr = myfunc(1)"


def test_function_attr_string_arg():
    assert encode(
        ast.Equal(
            ast.Attribute("attr"),
            ast.Function(
                "myfunc",
                [
                    ast.Attribute("other_attr"),
                    "abc",
                ],
            ),
        )
    ) == "attr = myfunc(other_attr, 'abc')"
