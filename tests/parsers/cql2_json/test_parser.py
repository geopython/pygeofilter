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
from datetime import date, datetime, timedelta

from dateparser.timezone_parser import StaticTzInfo
from pygeoif import geometry

from pygeofilter import ast, values
from pygeofilter.parsers.cql2_json import parse


def normalize_geom(geometry):
    if hasattr(geometry, "__geo_interface__"):
        geometry = geometry.__geo_interface__
    return json.loads(json.dumps(geometry))


def test_attribute_eq_literal():
    result = parse('{ "op": "eq", "args":[{ "property": "attr" }, "A"]}')
    assert result == ast.Equal(
        ast.Attribute("attr"),
        "A",
    )


def test_attribute_lt_literal():
    result = parse('{"op": "lt", "args": [{ "property": "attr" }, 5]}')
    assert result == ast.LessThan(
        ast.Attribute("attr"),
        5.0,
    )


def test_attribute_lte_literal():
    result = parse('{ "op": "lte", "args": [{ "property": "attr" }, 5]}')
    assert result == ast.LessEqual(
        ast.Attribute("attr"),
        5.0,
    )


def test_attribute_gt_literal():
    result = parse('{ "op": "gt", "args": [{ "property": "attr" }, 5]}')
    assert result == ast.GreaterThan(
        ast.Attribute("attr"),
        5.0,
    )


def test_attribute_gte_literal():
    result = parse('{"op": "gte", "args":[{ "property": "attr" }, 5]}')
    assert result == ast.GreaterEqual(
        ast.Attribute("attr"),
        5.0,
    )


def test_attribute_between():
    result = parse({"op": "between", "args": [{"property": "attr"}, [2, 5]]})
    assert result == ast.Between(
        ast.Attribute("attr"),
        2,
        5,
        False,
    )


def test_attribute_between_negative_positive():
    result = parse({"op": "between", "args": [{"property": "attr"}, [-1, 1]]})
    assert result == ast.Between(
        ast.Attribute("attr"),
        -1,
        1,
        False,
    )


def test_string_like():
    result = parse(
        {
            "op": "like",
            "args": [
                {"property": "attr"},
                "some%",
            ],
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


def test_attribute_in_list():
    result = parse(
        {
            "op": "in",
            "args": [
                {"property": "attr"},
                [1, 2, 3, 4],
            ],
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


def test_attribute_is_null():
    result = parse({"op": "isNull", "args": {"property": "attr"}})
    assert result == ast.IsNull(ast.Attribute("attr"), False)


def test_attribute_before():
    result = parse(
        {
            "op": "t_before",
            "args": [
                {"property": "attr"},
                {"timestamp": "2000-01-01T00:00:01Z"},
            ],
        }
    )
    assert result == ast.TimeBefore(
        ast.Attribute("attr"),
        datetime(2000, 1, 1, 0, 0, 1, tzinfo=StaticTzInfo("Z", timedelta(0))),
    )

    result = parse(
        {
            "op": "t_before",
            "args": [
                {"property": "attr"},
                {"date": "2000-01-01"},
            ],
        }
    )
    assert result == ast.TimeBefore(
        ast.Attribute("attr"),
        date(2000, 1, 1),
    )


def test_attribute_after_dt_dt():
    result = parse(
        {
            "op": "t_after",
            "args": [
                {"property": "attr"},
                {"interval": ["2000-01-01T00:00:00Z", "2000-01-01T00:00:01Z"]},
            ],
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
    result = parse(
        {
            "op": "t_meets",
            "args": [
                {"property": "attr"},
                {"interval": ["2000-01-01T00:00:00Z", "PT4S"]},
            ],
        }
    )
    assert result == ast.TimeMeets(
        ast.Attribute("attr"),
        values.Interval(
            datetime(2000, 1, 1, 0, 0, 0, tzinfo=StaticTzInfo("Z", timedelta(0))),
            timedelta(seconds=4),
        ),
    )


def test_attribute_metby_dr_dt():
    result = parse(
        {
            "op": "t_metby",
            "args": [
                {"property": "attr"},
                {"interval": ["PT4S", "2000-01-01T00:00:03Z"]},
            ],
        }
    )
    assert result == ast.TimeMetBy(
        ast.Attribute("attr"),
        values.Interval(
            timedelta(seconds=4),
            datetime(2000, 1, 1, 0, 0, 3, tzinfo=StaticTzInfo("Z", timedelta(0))),
        ),
    )


def test_attribute_toverlaps_open_dt():
    result = parse(
        {
            "op": "t_overlaps",
            "args": [
                {"property": "attr"},
                {"interval": ["..", "2000-01-01T00:00:03Z"]},
            ],
        }
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
        {
            "op": "t_overlappedby",
            "args": [
                {"property": "attr"},
                {"interval": ["2000-01-01T00:00:03Z", ".."]},
            ],
        }
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
    result = parse({"op": "a_equals", "args": [{"property": "arrayattr"}, [1, 2, 3]]})
    assert result == ast.ArrayEquals(
        ast.Attribute("arrayattr"),
        [1, 2, 3],
    )


def test_attribute_aoverlaps():
    result = parse({"op": "a_overlaps", "args": [{"property": "arrayattr"}, [1, 2, 3]]})
    assert result == ast.ArrayOverlaps(
        ast.Attribute("arrayattr"),
        [1, 2, 3],
    )


def test_attribute_acontains():
    result = parse({"op": "a_contains", "args": [{"property": "arrayattr"}, [1, 2, 3]]})
    assert result == ast.ArrayContains(
        ast.Attribute("arrayattr"),
        [1, 2, 3],
    )


def test_attribute_acontainedby():
    result = parse(
        {"op": "a_containedby", "args": [{"property": "arrayattr"}, [1, 2, 3]]}
    )
    assert result == ast.ArrayContainedBy(
        ast.Attribute("arrayattr"),
        [1, 2, 3],
    )


# Spatial predicate


def test_intersects_attr_point():
    result = parse(
        {
            "op": "s_intersects",
            "args": [
                {"property": "geometry"},
                {
                    "type": "Point",
                    "coordinates": [1, 1],
                },
            ],
        }
    )
    assert result == ast.GeometryIntersects(
        ast.Attribute("geometry"),
        values.Geometry(normalize_geom(geometry.Point(1, 1).__geo_interface__)),
    )


def test_disjoint_linestring_attr():
    result = parse(
        {
            "op": "s_disjoint",
            "args": [
                {
                    "type": "LineString",
                    "coordinates": [[1, 1], [2, 2]],
                    "bbox": [1.0, 1.0, 2.0, 2.0],
                },
                {"property": "geometry"},
            ],
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
            "op": "s_contains",
            "args": [
                {"property": "geometry"},
                {
                    "type": "Polygon",
                    "coordinates": [[[1, 1], [2, 2], [0, 3], [1, 1]]],
                    "bbox": [0.0, 1.0, 2.0, 3.0],
                },
            ],
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
            "op": "s_within",
            "args": [
                {
                    "type": "MultiPolygon",
                    "coordinates": [[[[1, 1], [2, 2], [0, 3], [1, 1]]]],
                    "bbox": [0.0, 1.0, 2.0, 3.0],
                },
                {"property": "geometry"},
            ],
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
            "op": "s_touches",
            "args": [
                {"property": "geometry"},
                {
                    "type": "MultiLineString",
                    "coordinates": [[[1, 1], [2, 2]], [[0, 3], [1, 1]]],
                    "bbox": [0.0, 1.0, 2.0, 3.0],
                },
            ],
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
            "op": "s_crosses",
            "args": [
                {"property": "geometry"},
                {
                    "type": "MultiLineString",
                    "coordinates": [[[1, 1], [2, 2]], [[0, 3], [1, 1]]],
                    "bbox": [0.0, 1.0, 2.0, 3.0],
                },
            ],
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
            "op": "s_overlaps",
            "args": [
                {"property": "geometry"},
                {
                    "type": "MultiLineString",
                    "coordinates": [[[1, 1], [2, 2]], [[0, 3], [1, 1]]],
                    "bbox": [0.0, 1.0, 2.0, 3.0],
                },
            ],
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


def test_attribute_arithmetic_add():
    result = parse(
        {
            "op": "eq",
            "args": [{"property": "attr"}, {"op": "+", "args": [5, 2]}],
        }
    )
    assert result == ast.Equal(
        ast.Attribute("attr"),
        ast.Add(
            5,
            2,
        ),
    )


def test_attribute_arithmetic_sub():
    result = parse(
        {
            "op": "eq",
            "args": [{"property": "attr"}, {"op": "-", "args": [5, 2]}],
        }
    )
    assert result == ast.Equal(
        ast.Attribute("attr"),
        ast.Sub(
            5,
            2,
        ),
    )


def test_attribute_arithmetic_mul():
    result = parse(
        {
            "op": "eq",
            "args": [{"property": "attr"}, {"op": "*", "args": [5, 2]}],
        }
    )
    assert result == ast.Equal(
        ast.Attribute("attr"),
        ast.Mul(
            5,
            2,
        ),
    )


def test_attribute_arithmetic_div():
    result = parse(
        {
            "op": "eq",
            "args": [{"property": "attr"}, {"op": "/", "args": [5, 2]}],
        }
    )
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
            "op": "eq",
            "args": [
                {"property": "attr"},
                {
                    "op": "+",
                    "args": [
                        3,
                        {"op": "*", "args": [5, 2]},
                    ],
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
            "op": "eq",
            "args": [
                {"property": "attr"},
                {
                    "op": "-",
                    "args": [
                        {"op": "/", "args": [3, 5]},
                        2,
                    ],
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
            "op": "eq",
            "args": [
                {"property": "attr"},
                {
                    "op": "/",
                    "args": [
                        3,
                        {"op": "-", "args": [5, 2]},
                    ],
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
            "op": "eq",
            "args": [
                {"property": "attr"},
                {"function": {"name": "myfunc", "arguments": []}},
            ],
        }
    )
    assert result == ast.Equal(
        ast.Attribute("attr"),
        ast.Function("myfunc", []),
    )


def test_function_single_arg():
    result = parse(
        {
            "op": "eq",
            "args": [
                {"property": "attr"},
                {"function": {"name": "myfunc", "arguments": [1]}},
            ],
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
            "op": "eq",
            "args": [
                {"property": "attr"},
                {
                    "function": {
                        "name": "myfunc",
                        "arguments": [{"property": "other_attr"}, "abc"],
                    }
                },
            ],
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
