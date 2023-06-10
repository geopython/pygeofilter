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

import json
from datetime import datetime, timedelta

from dateparser.timezone_parser import StaticTzInfo
from pygeoif import geometry

from pygeofilter import ast, values
from pygeofilter.frontends.cql_json import parse


def normalize_geom(geometry):
    if hasattr(geometry, "__geo_interface__"):
        geometry = geometry.__geo_interface__
    return json.loads(json.dumps(geometry))


def test_attribute_eq_literal():
    result = parse('{ "eq": [{ "property": "attr" }, "A"]}')
    assert result == ast.Equal(
        ast.Attribute("attr"),
        "A",
    )


def test_attribute_lt_literal():
    result = parse('{ "lt": [{ "property": "attr" }, 5]}')
    assert result == ast.LessThan(
        ast.Attribute("attr"),
        5.0,
    )


def test_attribute_lte_literal():
    result = parse('{ "lte": [{ "property": "attr" }, 5]}')
    assert result == ast.LessEqual(
        ast.Attribute("attr"),
        5.0,
    )


def test_attribute_gt_literal():
    result = parse('{ "gt": [{ "property": "attr" }, 5]}')
    assert result == ast.GreaterThan(
        ast.Attribute("attr"),
        5.0,
    )


def test_attribute_gte_literal():
    result = parse('{ "gte": [{ "property": "attr" }, 5]}')
    assert result == ast.GreaterEqual(
        ast.Attribute("attr"),
        5.0,
    )


# def test_attribute_ne_literal():
#     result = parse('attr <> 5')
#     assert result == ast.ComparisonPredicateNode(
#         ast.Attribute('attr'),
#         5,
#         ast.ComparisonOp('<>'),
#     )


def test_attribute_between():
    result = parse(
        {
            "between": {
                "value": {"property": "attr"},
                "lower": 2,
                "upper": 5,
            }
        }
    )
    assert result == ast.Between(
        ast.Attribute("attr"),
        2,
        5,
        False,
    )


# def test_attribute_not_between():
#     result = parse('attr NOT BETWEEN 2 AND 5')
#     assert result == ast.BetweenPredicateNode(
#         ast.Attribute('attr'),
#         2,
#         5,
#         True,
#     )


def test_attribute_between_negative_positive():
    result = parse(
        {
            "between": {
                "value": {"property": "attr"},
                "lower": -1,
                "upper": 1,
            }
        }
    )
    assert result == ast.Between(
        ast.Attribute("attr"),
        -1,
        1,
        False,
    )


def test_string_like():
    result = parse(
        {
            "like": {
                "like": [
                    {"property": "attr"},
                    "some%",
                ],
                "nocase": False,
            }
        }
    )
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
    result = parse(
        {
            "like": {
                "like": [
                    {"property": "attr"},
                    "some%",
                ],
                "nocase": True,
            }
        }
    )
    assert result == ast.Like(
        ast.Attribute("attr"),
        "some%",
        nocase=True,
        not_=False,
        wildcard="%",
        singlechar=".",
        escapechar="\\",
    )


# def test_string_not_like():
#     result = parse('attr NOT LIKE "some%"')
#     assert result == ast.LikePredicateNode(
#         ast.Attribute('attr'),
#         'some%',
#         nocase=False,
#         not_=True,
#         wildcard='%',
#         singlechar='.',
#         escapechar=None,
#     )


# def test_string_not_ilike():
#     result = parse('attr NOT ILIKE "some%"')
#     assert result == ast.LikePredicateNode(
#         ast.Attribute('attr'),
#         'some%',
#         nocase=True,
#         not_=True,
#         wildcard='%',
#         singlechar='.',
#         escapechar=None,
#     )


def test_attribute_in_list():
    result = parse(
        {
            "in": {
                "value": {"property": "attr"},
                "list": [1, 2, 3, 4],
            }
        }
    )
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


# def test_attribute_not_in_list():
#     result = parse('attr NOT IN ("A", "B", \'C\', \'D\')')
#     assert result == ast.InPredicateNode(
#         ast.Attribute('attr'), [
#             "A",
#             "B",
#             "C",
#             "D",
#         ],
#         True
#     )


def test_attribute_is_null():
    result = parse({"isNull": {"property": "attr"}})
    assert result == ast.IsNull(ast.Attribute("attr"), False)


# def test_attribute_is_not_null():
#     result = parse('attr IS NOT NULL')
#     assert result == ast.NullPredicateNode(
#         ast.Attribute('attr'), True
#     )

# # Temporal predicate


def test_attribute_before():
    result = parse(
        {
            "before": [
                {"property": "attr"},
                "2000-01-01T00:00:01Z",
            ]
        }
    )
    assert result == ast.TimeBefore(
        ast.Attribute("attr"),
        datetime(2000, 1, 1, 0, 0, 1, tzinfo=StaticTzInfo("Z", timedelta(0))),
    )


def test_attribute_after_dt_dt():
    result = parse(
        {
            "after": [
                {"property": "attr"},
                ["2000-01-01T00:00:00Z", "2000-01-01T00:00:01Z"],
            ]
        }
    )

    assert result == ast.TimeAfter(
        ast.Attribute("attr"),
        values.Interval(
            datetime(2000, 1, 1, 0, 0, 0, tzinfo=StaticTzInfo("Z", timedelta(0))),
            datetime(2000, 1, 1, 0, 0, 1, tzinfo=StaticTzInfo("Z", timedelta(0))),
        ),
    )


def test_meets_dt_dr():
    result = parse({"meets": [{"property": "attr"}, ["2000-01-01T00:00:00Z", "PT4S"]]})
    assert result == ast.TimeMeets(
        ast.Attribute("attr"),
        values.Interval(
            datetime(2000, 1, 1, 0, 0, 0, tzinfo=StaticTzInfo("Z", timedelta(0))),
            timedelta(seconds=4),
        ),
    )


def test_attribute_metby_dr_dt():
    result = parse({"metby": [{"property": "attr"}, ["PT4S", "2000-01-01T00:00:03Z"]]})
    assert result == ast.TimeMetBy(
        ast.Attribute("attr"),
        values.Interval(
            timedelta(seconds=4),
            datetime(2000, 1, 1, 0, 0, 3, tzinfo=StaticTzInfo("Z", timedelta(0))),
        ),
    )


def test_attribute_toverlaps_open_dt():
    result = parse(
        {"toverlaps": [{"property": "attr"}, ["..", "2000-01-01T00:00:03Z"]]}
    )
    assert result == ast.TimeOverlaps(
        ast.Attribute("attr"),
        values.Interval(
            None,
            datetime(2000, 1, 1, 0, 0, 3, tzinfo=StaticTzInfo("Z", timedelta(0))),
        ),
    )


def test_attribute_overlappedby_dt_open():
    result = parse(
        {"overlappedby": [{"property": "attr"}, ["2000-01-01T00:00:03Z", ".."]]}
    )
    assert result == ast.TimeOverlappedBy(
        ast.Attribute("attr"),
        values.Interval(
            datetime(2000, 1, 1, 0, 0, 3, tzinfo=StaticTzInfo("Z", timedelta(0))),
            None,
        ),
    )


# Array predicate


def test_attribute_aequals():
    result = parse({"aequals": [{"property": "arrayattr"}, [1, 2, 3]]})
    assert result == ast.ArrayEquals(
        ast.Attribute("arrayattr"),
        [1, 2, 3],
    )


def test_attribute_aoverlaps():
    result = parse({"aoverlaps": [{"property": "arrayattr"}, [1, 2, 3]]})
    assert result == ast.ArrayOverlaps(
        ast.Attribute("arrayattr"),
        [1, 2, 3],
    )


def test_attribute_acontains():
    result = parse({"acontains": [{"property": "arrayattr"}, [1, 2, 3]]})
    assert result == ast.ArrayContains(
        ast.Attribute("arrayattr"),
        [1, 2, 3],
    )


def test_attribute_acontainedby():
    result = parse({"acontainedBy": [{"property": "arrayattr"}, [1, 2, 3]]})
    assert result == ast.ArrayContainedBy(
        ast.Attribute("arrayattr"),
        [1, 2, 3],
    )


# Spatial predicate


def test_intersects_attr_point():
    result = parse(
        {
            "intersects": [
                {"property": "geometry"},
                {
                    "type": "Point",
                    "coordinates": [1, 1],
                },
            ]
        }
    )
    assert result == ast.GeometryIntersects(
        ast.Attribute("geometry"),
        values.Geometry(normalize_geom(geometry.Point(1, 1).__geo_interface__)),
    )


def test_disjoint_linestring_attr():
    result = parse(
        {
            "disjoint": [
                {
                    "type": "LineString",
                    "coordinates": [[1, 1], [2, 2]],
                    "bbox": [1.0, 1.0, 2.0, 2.0],
                },
                {"property": "geometry"},
            ]
        }
    )
    assert result == ast.GeometryDisjoint(
        values.Geometry(
            normalize_geom(geometry.LineString([(1, 1), (2, 2)]).__geo_interface__),
        ),
        ast.Attribute("geometry"),
    )


def test_contains_attr_polygon():
    result = parse(
        {
            "contains": [
                {"property": "geometry"},
                {
                    "type": "Polygon",
                    "coordinates": [[[1, 1], [2, 2], [0, 3], [1, 1]]],
                    "bbox": [0.0, 1.0, 2.0, 3.0],
                },
            ]
        }
    )
    assert result == ast.GeometryContains(
        ast.Attribute("geometry"),
        values.Geometry(
            normalize_geom(
                geometry.Polygon([(1, 1), (2, 2), (0, 3), (1, 1)]).__geo_interface__
            ),
        ),
    )


def test_within_multipolygon_attr():
    result = parse(
        {
            "within": [
                {
                    "type": "MultiPolygon",
                    "coordinates": [[[[1, 1], [2, 2], [0, 3], [1, 1]]]],
                    "bbox": [0.0, 1.0, 2.0, 3.0],
                },
                {"property": "geometry"},
            ]
        }
    )
    assert result == ast.GeometryWithin(
        values.Geometry(
            normalize_geom(
                geometry.MultiPolygon.from_polygons(
                    geometry.Polygon([(1, 1), (2, 2), (0, 3), (1, 1)])
                ).__geo_interface__
            ),
        ),
        ast.Attribute("geometry"),
    )


def test_touches_attr_multilinestring():
    result = parse(
        {
            "touches": [
                {"property": "geometry"},
                {
                    "type": "MultiLineString",
                    "coordinates": [[[1, 1], [2, 2]], [[0, 3], [1, 1]]],
                    "bbox": [0.0, 1.0, 2.0, 3.0],
                },
            ]
        }
    )
    assert result == ast.GeometryTouches(
        ast.Attribute("geometry"),
        values.Geometry(
            normalize_geom(
                geometry.MultiLineString.from_linestrings(
                    geometry.LineString([(1, 1), (2, 2)]),
                    geometry.LineString([(0, 3), (1, 1)]),
                ).__geo_interface__
            ),
        ),
    )


def test_crosses_attr_multilinestring():
    result = parse(
        {
            "crosses": [
                {"property": "geometry"},
                {
                    "type": "MultiLineString",
                    "coordinates": [[[1, 1], [2, 2]], [[0, 3], [1, 1]]],
                    "bbox": [0.0, 1.0, 2.0, 3.0],
                },
            ]
        }
    )
    assert result == ast.GeometryCrosses(
        ast.Attribute("geometry"),
        values.Geometry(
            normalize_geom(
                geometry.MultiLineString.from_linestrings(
                    geometry.LineString([(1, 1), (2, 2)]),
                    geometry.LineString([(0, 3), (1, 1)]),
                ).__geo_interface__
            )
        ),
    )


def test_overlaps_attr_multilinestring():
    result = parse(
        {
            "overlaps": [
                {"property": "geometry"},
                {
                    "type": "MultiLineString",
                    "coordinates": [[[1, 1], [2, 2]], [[0, 3], [1, 1]]],
                    "bbox": [0.0, 1.0, 2.0, 3.0],
                },
            ]
        }
    )
    assert result == ast.GeometryOverlaps(
        ast.Attribute("geometry"),
        values.Geometry(
            normalize_geom(
                geometry.MultiLineString.from_linestrings(
                    geometry.LineString([(1, 1), (2, 2)]),
                    geometry.LineString([(0, 3), (1, 1)]),
                ).__geo_interface__
            ),
        ),
    )


# POINT(1 1)
# LINESTRING(1 1,2 2)
# MULTIPOLYGON(((1 1,2 2,0 3,1 1))
# MULTILINESTRING((1 1,2 2),(0 3,1 1))
# POLYGON((1 1,2 2,0 3,1 1))

# def test_equals_attr_geometrycollection():
#     result = parse('OVERLAPS(geometry, )')
#     assert result == ast.SpatialPredicateNode(
#         ast.Attribute('geometry'),
#         ast.LiteralExpression(
#             geometry.MultiLineString([
#                 geometry.LineString([(1, 1), (2, 2)]),
#                 geometry.LineString([(0, 3), (1, 1)]),
#             ])
#         ),
#         'OVERLAPS'
#     )


# relate

# def test_relate_attr_polygon():
#     result = parse('RELATE(geometry, POLYGON((1 1,2 2,0 3,1 1)),
#          "1*T***T**")')
#     assert result == ast.SpatialPatternPredicateNode(
#         ast.Attribute('geometry'),
#         ast.LiteralExpression(
#             geometry.Polygon([(1, 1), (2, 2), (0, 3), (1, 1)])
#         ),
#         pattern='1*T***T**',
#     )


# # dwithin/beyond

# def test_dwithin_attr_polygon():
#     result = parse('DWITHIN(geometry, POLYGON((1 1,2 2,0 3,1 1)), 5, feet)')
#     print(get_repr(result))
#     assert result == ast.SpatialDistancePredicateNode(
#         ast.Attribute('geometry'),
#         ast.LiteralExpression(
#             geometry.Polygon([(1, 1), (2, 2), (0, 3), (1, 1)])
#         ),
#         ast.SpatialDistanceOp('DWITHIN'),
#         distance=5,
#         units='feet',
#     )


# def test_beyond_attr_polygon():
#     result = parse(
#         'BEYOND(geometry, POLYGON((1 1,2 2,0 3,1 1)), 5, nautical miles)'
#     )
#     print(get_repr(result))
#     assert result == ast.SpatialDistancePredicateNode(
#         ast.Attribute('geometry'),
#         ast.LiteralExpression(
#             geometry.Polygon([(1, 1), (2, 2), (0, 3), (1, 1)])
#         ),
#         ast.SpatialDistanceOp('BEYOND'),
#         distance=5,
#         units='nautical miles',
#     )


# BBox prediacte


# def test_bbox_simple():
#     result = parse('BBOX(geometry, 1, 2, 3, 4)')
#     assert result == ast.BBoxPredicateNode(
#         ast.Attribute('geometry'),
#         ast.LiteralExpression(1),
#         ast.LiteralExpression(2),
#         ast.LiteralExpression(3),
#         ast.LiteralExpression(4),
#     )


# def test_bbox_crs():
#     result = parse('BBOX(geometry, 1, 2, 3, 4, "EPSG:3875")')
#     assert result == ast.BBoxPredicateNode(
#         ast.Attribute('geometry'),
#         ast.LiteralExpression(1),
#         ast.LiteralExpression(2),
#         ast.LiteralExpression(3),
#         ast.LiteralExpression(4),
#         'EPSG:3875',
#     )


def test_attribute_arithmetic_add():
    result = parse({"eq": [{"property": "attr"}, {"+": [5, 2]}]})
    assert result == ast.Equal(
        ast.Attribute("attr"),
        ast.Add(
            5,
            2,
        ),
    )


def test_attribute_arithmetic_sub():
    result = parse({"eq": [{"property": "attr"}, {"-": [5, 2]}]})
    assert result == ast.Equal(
        ast.Attribute("attr"),
        ast.Sub(
            5,
            2,
        ),
    )


def test_attribute_arithmetic_mul():
    result = parse({"eq": [{"property": "attr"}, {"*": [5, 2]}]})
    assert result == ast.Equal(
        ast.Attribute("attr"),
        ast.Mul(
            5,
            2,
        ),
    )


def test_attribute_arithmetic_div():
    result = parse({"eq": [{"property": "attr"}, {"/": [5, 2]}]})
    assert result == ast.Equal(
        ast.Attribute("attr"),
        ast.Div(
            5,
            2,
        ),
    )


def test_attribute_arithmetic_add_mul():
    result = parse(
        {
            "eq": [
                {"property": "attr"},
                {
                    "+": [
                        3,
                        {"*": [5, 2]},
                    ]
                },
            ],
        }
    )
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
    result = parse(
        {
            "eq": [
                {"property": "attr"},
                {
                    "-": [
                        {"/": [3, 5]},
                        2,
                    ]
                },
            ],
        }
    )
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
    result = parse(
        {
            "eq": [
                {"property": "attr"},
                {
                    "/": [
                        3,
                        {"-": [5, 2]},
                    ]
                },
            ],
        }
    )
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
    result = parse(
        {
            "eq": [
                {"property": "attr"},
                {"function": {"name": "myfunc", "arguments": []}},
            ]
        }
    )
    assert result == ast.Equal(
        ast.Attribute("attr"),
        ast.Function("myfunc", []),
    )


def test_function_single_arg():
    result = parse(
        {
            "eq": [
                {"property": "attr"},
                {"function": {"name": "myfunc", "arguments": [1]}},
            ]
        }
    )
    assert result == ast.Equal(
        ast.Attribute("attr"),
        ast.Function(
            "myfunc",
            [1],
        ),
    )


def test_function_attr_string_arg():
    result = parse(
        {
            "eq": [
                {"property": "attr"},
                {
                    "function": {
                        "name": "myfunc",
                        "arguments": [{"property": "other_attr"}, "abc"],
                    }
                },
            ]
        }
    )
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
