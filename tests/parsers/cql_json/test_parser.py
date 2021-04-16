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

from pygeofilter.parsers.cql_json import parse
from pygeofilter.ast import get_repr
from pygeofilter import ast


def test_attribute_eq_literal():
    result = parse('{ "eq": [{ "property": "attr" }, "A"]}')
    assert result == ast.ComparisonPredicateNode(
        ast.AttributeExpression('attr'),
        'A',
        ast.ComparisonOp('='),
    )


def test_attribute_lt_literal():
    result = parse('{ "lt": [{ "property": "attr" }, 5]}')
    assert result == ast.ComparisonPredicateNode(
        ast.AttributeExpression('attr'),
        5.0,
        ast.ComparisonOp('<'),
    )


def test_attribute_lte_literal():
    result = parse('{ "lte": [{ "property": "attr" }, 5]}')
    assert result == ast.ComparisonPredicateNode(
        ast.AttributeExpression('attr'),
        5.0,
        ast.ComparisonOp('<='),
    )


def test_attribute_gt_literal():
    result = parse('{ "gt": [{ "property": "attr" }, 5]}')
    assert result == ast.ComparisonPredicateNode(
        ast.AttributeExpression('attr'),
        5.0,
        ast.ComparisonOp('>'),
    )


def test_attribute_gte_literal():
    result = parse('{ "gte": [{ "property": "attr" }, 5]}')
    assert result == ast.ComparisonPredicateNode(
        ast.AttributeExpression('attr'),
        5.0,
        ast.ComparisonOp('>='),
    )


# def test_attribute_ne_literal():
#     result = parse('attr <> 5')
#     assert result == ast.ComparisonPredicateNode(
#         ast.AttributeExpression('attr'),
#         5,
#         ast.ComparisonOp('<>'),
#     )


def test_attribute_between():
    result = parse({
        "between": {
            "value": {
                "property": "attr"
            },
            "lower": 2,
            "upper": 5,
        }
    })
    assert result == ast.BetweenPredicateNode(
        ast.AttributeExpression('attr'),
        2,
        5,
        False,
    )


# def test_attribute_not_between():
#     result = parse('attr NOT BETWEEN 2 AND 5')
#     assert result == ast.BetweenPredicateNode(
#         ast.AttributeExpression('attr'),
#         2,
#         5,
#         True,
#     )


def test_attribute_between_negative_positive():
    result = parse({
        "between": {
            "value": {
                "property": "attr"
            },
            "lower": -1,
            "upper": 1,
        }
    })
    assert result == ast.BetweenPredicateNode(
        ast.AttributeExpression('attr'),
        -1,
        1,
        False,
    )


def test_string_like():
    result = parse({
        "like": {
            "like": [
                {"property": "attr"},
                "some%",
            ],
            "nocase": False,
        }
    })
    assert result == ast.LikePredicateNode(
        ast.AttributeExpression('attr'),
        'some%',
        nocase=False,
        not_=False,
        wildcard='%',
        singlechar='.',
        escapechar='\\',
    )


def test_string_ilike():
    result = parse({
        "like": {
            "like": [
                {"property": "attr"},
                "some%",
            ],
            "nocase": True,
        }
    })
    assert result == ast.LikePredicateNode(
        ast.AttributeExpression('attr'),
        'some%',
        nocase=True,
        not_=False,
        wildcard='%',
        singlechar='.',
        escapechar='\\',
    )


# def test_string_not_like():
#     result = parse('attr NOT LIKE "some%"')
#     assert result == ast.LikePredicateNode(
#         ast.AttributeExpression('attr'),
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
#         ast.AttributeExpression('attr'),
#         'some%',
#         nocase=True,
#         not_=True,
#         wildcard='%',
#         singlechar='.',
#         escapechar=None,
#     )


def test_attribute_in_list():
    result = parse({
        "in": {
            "value": {"property": "attr"},
            "list": [1, 2, 3, 4],
        }
    })
    assert result == ast.InPredicateNode(
        ast.AttributeExpression('attr'), [
            1,
            2,
            3,
            4,
        ],
        False
    )


# def test_attribute_not_in_list():
#     result = parse('attr NOT IN ("A", "B", \'C\', \'D\')')
#     assert result == ast.InPredicateNode(
#         ast.AttributeExpression('attr'), [
#             "A",
#             "B",
#             "C",
#             "D",
#         ],
#         True
#     )


def test_attribute_is_null():
    result = parse({
        "isNull": {"property": "attr"}
    })
    assert result == ast.NullPredicateNode(
        ast.AttributeExpression('attr'), False
    )


# def test_attribute_is_not_null():
#     result = parse('attr IS NOT NULL')
#     assert result == ast.NullPredicateNode(
#         ast.AttributeExpression('attr'), True
#     )

# # Temporal predicate


def test_attribute_before():
    result = parse({
        "before": [
            {"property": "attr"},
            "2000-01-01T00:00:01Z",
        ]
    })
    assert result == ast.TemporalPredicateNode(
        ast.AttributeExpression('attr'),
        datetime(
            2000, 1, 1, 0, 0, 1,
            tzinfo=StaticTzInfo('Z', timedelta(0))
        ),
        ast.TemporalComparisonOp('BEFORE'),
    )


def test_attribute_after_dt_dt():
    result = parse({
        "after": [
            {"property": "attr"},
            ["2000-01-01T00:00:00Z", "2000-01-01T00:00:01Z"]
        ]
    })

    assert result == ast.TemporalPredicateNode(
        ast.AttributeExpression('attr'),
        [
            datetime(
                2000, 1, 1, 0, 0, 0,
                tzinfo=StaticTzInfo('Z', timedelta(0))
            ),
            datetime(
                2000, 1, 1, 0, 0, 1,
                tzinfo=StaticTzInfo('Z', timedelta(0))
            ),
        ],
        ast.TemporalComparisonOp('AFTER'),
    )


def test_meets_dt_dr():
    result = parse({
        "meets": [
            {"property": "attr"},
            ["2000-01-01T00:00:00Z", "PT4S"]
        ]
    })
    assert result == ast.TemporalPredicateNode(
        ast.AttributeExpression('attr'),
        [
            datetime(
                2000, 1, 1, 0, 0, 0,
                tzinfo=StaticTzInfo('Z', timedelta(0))
            ),
            timedelta(seconds=4),
        ],
        ast.TemporalComparisonOp('MEETS'),
    )


def test_attribute_metby_dr_dt():
    result = parse({
        "metby": [
            {"property": "attr"},
            ["PT4S", "2000-01-01T00:00:03Z"]
        ]
    })
    assert result == ast.TemporalPredicateNode(
        ast.AttributeExpression('attr'),
        [
            timedelta(seconds=4),
            datetime(
                2000, 1, 1, 0, 0, 3,
                tzinfo=StaticTzInfo('Z', timedelta(0))
            ),
        ],
        ast.TemporalComparisonOp('METBY'),
    )


def test_attribute_toverlaps_open_dt():
    result = parse({
        "toverlaps": [
            {"property": "attr"},
            ["..", "2000-01-01T00:00:03Z"]
        ]
    })
    assert result == ast.TemporalPredicateNode(
        ast.AttributeExpression('attr'),
        [
            None,
            datetime(
                2000, 1, 1, 0, 0, 3,
                tzinfo=StaticTzInfo('Z', timedelta(0))
            ),
        ],
        ast.TemporalComparisonOp('TOVERLAPS'),
    )


def test_attribute_overlappedby_dt_open():
    result = parse({
        "overlappedby": [
            {"property": "attr"},
            ["2000-01-01T00:00:03Z", ".."]
        ]
    })
    assert result == ast.TemporalPredicateNode(
        ast.AttributeExpression('attr'),
        [
            datetime(
                2000, 1, 1, 0, 0, 3,
                tzinfo=StaticTzInfo('Z', timedelta(0))
            ),
            None,
        ],
        ast.TemporalComparisonOp('OVERLAPPEDBY'),
    )

# Spatial predicate


def test_intersects_attr_point():
    result = parse({
        "intersects": [
            {"property": "geometry"},
            {
                "type": "Point",
                "coordinates": [1, 1],
            }
        ]
    })
    assert result == ast.SpatialOperationPredicateNode(
        ast.AttributeExpression('geometry'),
        json.loads(json.dumps(geometry.Point(1, 1).__geo_interface__)),
        ast.SpatialComparisonOp('INTERSECTS'),
    )


def test_disjoint_linestring_attr():
    result = parse({
        "disjoint": [
            {
                "type": "LineString",
                "coordinates": [[1, 1], [2, 2]],
                "bbox": [1.0, 1.0, 2.0, 2.0]
            },
            {"property": "geometry"},
        ]
    })
    assert result == ast.SpatialOperationPredicateNode(
        json.loads(json.dumps(geometry.LineString([(1, 1), (2, 2)]).__geo_interface__)),
        ast.AttributeExpression('geometry'),
        ast.SpatialComparisonOp('DISJOINT'),
    )


def test_contains_attr_polygon():
    result = parse({
        "contains": [
            {"property": "geometry"},
            {
                "type": "Polygon",
                "coordinates": [
                    [[1, 1], [2, 2], [0, 3], [1, 1]]
                ],
                'bbox': [0.0, 1.0, 2.0, 3.0]
            },
        ]
    })
    assert result == ast.SpatialOperationPredicateNode(
        ast.AttributeExpression('geometry'),
        json.loads(json.dumps(geometry.Polygon([(1, 1), (2, 2), (0, 3), (1, 1)]).__geo_interface__)),
        ast.SpatialComparisonOp('CONTAINS'),
    )


def test_within_multipolygon_attr():
    result = parse({
        "within": [
            {
                "type": "MultiPolygon",
                "coordinates": [
                    [[[1, 1], [2, 2], [0, 3], [1, 1]]]
                ],
                'bbox': [0.0, 1.0, 2.0, 3.0]
            },
            {"property": "geometry"},
        ]
    })
    assert result == ast.SpatialOperationPredicateNode(
        json.loads(json.dumps(
            geometry.MultiPolygon([
                geometry.Polygon([(1, 1), (2, 2), (0, 3), (1, 1)])
            ]).__geo_interface__
        )),
        ast.AttributeExpression('geometry'),
        ast.SpatialComparisonOp('WITHIN'),
    )


def test_touches_attr_multilinestring():
    result = parse({
        "touches": [
            {"property": "geometry"},
            {
                "type": "MultiLineString",
                "coordinates": [[[1, 1], [2, 2]], [[0, 3], [1, 1]]],
                "bbox": [0.0, 1.0, 2.0, 3.0]
            },
        ]
    })
    assert result == ast.SpatialOperationPredicateNode(
        ast.AttributeExpression('geometry'),
        json.loads(json.dumps(
            geometry.MultiLineString([
                geometry.LineString([(1, 1), (2, 2)]),
                geometry.LineString([(0, 3), (1, 1)]),
            ]).__geo_interface__
        )),
        ast.SpatialComparisonOp('TOUCHES'),
    )


def test_crosses_attr_multilinestring():
    result = parse({
        "crosses": [
            {"property": "geometry"},
            {
                "type": "MultiLineString",
                "coordinates": [[[1, 1], [2, 2]], [[0, 3], [1, 1]]],
                "bbox": [0.0, 1.0, 2.0, 3.0]
            },
        ]
    })
    assert result == ast.SpatialOperationPredicateNode(
        ast.AttributeExpression('geometry'),
        json.loads(json.dumps(
            geometry.MultiLineString([
                geometry.LineString([(1, 1), (2, 2)]),
                geometry.LineString([(0, 3), (1, 1)]),
            ]).__geo_interface__
        )),
        ast.SpatialComparisonOp('CROSSES'),
    )


def test_overlaps_attr_multilinestring():
    result = parse({
        "overlaps": [
            {"property": "geometry"},
            {
                "type": "MultiLineString",
                "coordinates": [[[1, 1], [2, 2]], [[0, 3], [1, 1]]],
                "bbox": [0.0, 1.0, 2.0, 3.0]
            },
        ]
    })
    assert result == ast.SpatialOperationPredicateNode(
        ast.AttributeExpression('geometry'),
        json.loads(json.dumps(
            geometry.MultiLineString([
                geometry.LineString([(1, 1), (2, 2)]),
                geometry.LineString([(0, 3), (1, 1)]),
            ]).__geo_interface__
        )),
        ast.SpatialComparisonOp('OVERLAPS'),
    )


# POINT(1 1)
# LINESTRING(1 1,2 2)
# MULTIPOLYGON(((1 1,2 2,0 3,1 1))
# MULTILINESTRING((1 1,2 2),(0 3,1 1))
# POLYGON((1 1,2 2,0 3,1 1))

# def test_equals_attr_geometrycollection():
#     result = parse('OVERLAPS(geometry, )')
#     assert result == ast.SpatialPredicateNode(
#         ast.AttributeExpression('geometry'),
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
#     result = parse('RELATE(geometry, POLYGON((1 1,2 2,0 3,1 1)), "1*T***T**")')
#     assert result == ast.SpatialPatternPredicateNode(
#         ast.AttributeExpression('geometry'),
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
#         ast.AttributeExpression('geometry'),
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
#         ast.AttributeExpression('geometry'),
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
#         ast.AttributeExpression('geometry'),
#         ast.LiteralExpression(1),
#         ast.LiteralExpression(2),
#         ast.LiteralExpression(3),
#         ast.LiteralExpression(4),
#     )


# def test_bbox_crs():
#     result = parse('BBOX(geometry, 1, 2, 3, 4, "EPSG:3875")')
#     assert result == ast.BBoxPredicateNode(
#         ast.AttributeExpression('geometry'),
#         ast.LiteralExpression(1),
#         ast.LiteralExpression(2),
#         ast.LiteralExpression(3),
#         ast.LiteralExpression(4),
#         'EPSG:3875',
#     )


def test_attribute_arithmetic_add():
    result = parse({
        "eq": [
            {"property": "attr"},
            {"+": [5, 2]}
        ]
    })
    assert result == ast.ComparisonPredicateNode(
        ast.AttributeExpression('attr'),
        ast.ArithmeticExpressionNode(
            5,
            2,
            ast.ArithmeticOp('+'),
        ),
        ast.ComparisonOp('='),
    )


def test_attribute_arithmetic_sub():
    result = parse({
        "eq": [
            {"property": "attr"},
            {"-": [5, 2]}
        ]
    })
    assert result == ast.ComparisonPredicateNode(
        ast.AttributeExpression('attr'),
        ast.ArithmeticExpressionNode(
            5,
            2,
            ast.ArithmeticOp('-'),
        ),
        ast.ComparisonOp('='),
    )


def test_attribute_arithmetic_mul():
    result = parse({
        "eq": [
            {"property": "attr"},
            {"*": [5, 2]}
        ]
    })
    assert result == ast.ComparisonPredicateNode(
        ast.AttributeExpression('attr'),
        ast.ArithmeticExpressionNode(
            5,
            2,
            ast.ArithmeticOp('*'),
        ),
        ast.ComparisonOp('='),
    )


def test_attribute_arithmetic_div():
    result = parse({
        "eq": [
            {"property": "attr"},
            {"/": [5, 2]}
        ]
    })
    assert result == ast.ComparisonPredicateNode(
        ast.AttributeExpression('attr'),
        ast.ArithmeticExpressionNode(
            5,
            2,
            ast.ArithmeticOp('/'),
        ),
        ast.ComparisonOp('='),
    )


def test_attribute_arithmetic_add_mul():
    result = parse({
        "eq": [
            {"property": "attr"},
            {"+": [
                3,
                {"*": [5, 2]},
            ]},
        ],
    })
    assert result == ast.ComparisonPredicateNode(
        ast.AttributeExpression('attr'),
        ast.ArithmeticExpressionNode(
            3,
            ast.ArithmeticExpressionNode(
                5,
                2,
                ast.ArithmeticOp('*'),
            ),
            ast.ArithmeticOp('+'),
        ),
        ast.ComparisonOp('='),
    )


def test_attribute_arithmetic_div_sub():
    result = parse({
        "eq": [
            {"property": "attr"},
            {"-": [
                {"/": [3, 5]},
                2,
            ]},
        ],
    })
    assert result == ast.ComparisonPredicateNode(
        ast.AttributeExpression('attr'),
        ast.ArithmeticExpressionNode(
            ast.ArithmeticExpressionNode(
                3,
                5,
                ast.ArithmeticOp('/'),
            ),
            2,
            ast.ArithmeticOp('-'),
        ),
        ast.ComparisonOp('='),
    )


def test_attribute_arithmetic_div_sub_bracketted():
    result = parse({
        "eq": [
            {"property": "attr"},
            {"/": [
                3,
                {"-": [5, 2]},
            ]},
        ],
    })
    assert result == ast.ComparisonPredicateNode(
        ast.AttributeExpression('attr'),
        ast.ArithmeticExpressionNode(
            3,
            ast.ArithmeticExpressionNode(
                5,
                2,
                ast.ArithmeticOp('-'),
            ),
            ast.ArithmeticOp('/'),
        ),
        ast.ComparisonOp('='),
    )

# test function expression parsing


def test_function_no_arg():
    result = parse({
        "eq": [
            {"property": "attr"},
            {
                "function": {
                    "name": "myfunc",
                    "arguments": []
                }
            }
        ]
    })
    assert result == ast.ComparisonPredicateNode(
        ast.AttributeExpression('attr'),
        ast.FunctionExpressionNode(
            'myfunc', [
            ]
        ),
        ast.ComparisonOp('='),
    )


def test_function_single_arg():
    result = parse({
        "eq": [
            {"property": "attr"},
            {
                "function": {
                    "name": "myfunc",
                    "arguments": [1]
                }
            }
        ]
    })
    assert result == ast.ComparisonPredicateNode(
        ast.AttributeExpression('attr'),
        ast.FunctionExpressionNode(
            'myfunc',
            [1],
        ),
        ast.ComparisonOp('='),
    )


def test_function_attr_string_arg():
    result = parse({
        "eq": [
            {"property": "attr"},
            {
                "function": {
                    "name": "myfunc",
                    "arguments": [
                        {"property": "other_attr"},
                        "abc"
                    ]
                }
            }
        ]
    })
    assert result == ast.ComparisonPredicateNode(
        ast.AttributeExpression('attr'),
        ast.FunctionExpressionNode(
            'myfunc', [
                ast.AttributeExpression('other_attr'),
                "abc",
            ]
        ),
        ast.ComparisonOp('='),
    )
