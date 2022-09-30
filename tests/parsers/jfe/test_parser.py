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

import json
from datetime import datetime, timedelta

from dateparser.timezone_parser import StaticTzInfo
from pygeoif import geometry

from pygeofilter.parsers.jfe import parse
from pygeofilter import ast
from pygeofilter import values


def normalize_geom(geometry):
    if hasattr(geometry, '__geo_interface__'):
        geometry = geometry.__geo_interface__
    return json.loads(json.dumps(geometry))


def test_attribute_eq_literal():
    result = parse('["==", ["get", "attr"], "A"]')
    assert result == ast.Equal(
        ast.Attribute('attr'),
        'A',
    )


def test_attribute_lt_literal():
    result = parse('["<", ["get", "attr"], 5]')
    assert result == ast.LessThan(
        ast.Attribute('attr'),
        5.0,
    )


def test_attribute_lte_literal():
    result = parse('["<=", ["get", "attr"], 5]')
    assert result == ast.LessEqual(
        ast.Attribute('attr'),
        5.0,
    )


def test_attribute_gt_literal():
    result = parse('[">", ["get", "attr"], 5]')
    assert result == ast.GreaterThan(
        ast.Attribute('attr'),
        5.0,
    )


def test_attribute_gte_literal():
    result = parse('[">=", ["get", "attr"], 5]')
    assert result == ast.GreaterEqual(
        ast.Attribute('attr'),
        5.0,
    )


def test_attribute_ne_literal():
    result = parse('["!=", ["get", "attr"], 5]')
    assert result == ast.NotEqual(
        ast.Attribute('attr'),
        5.0,
    )


def test_string_like():
    result = parse(['like', ['get', 'attr'], 'some%'])
    assert result == ast.Like(
        ast.Attribute('attr'),
        'some%',
        nocase=False,
        wildcard='%',
        singlechar='.',
        escapechar='\\',
        not_=False,
    )


def test_string_like_wildcard():
    result = parse(['like', ['get', 'attr'], 'some*', {'wildCard': '*'}])
    assert result == ast.Like(
        ast.Attribute('attr'),
        'some*',
        nocase=False,
        wildcard='*',
        singlechar='.',
        escapechar='\\',
        not_=False,
    )


def test_attribute_in_list():
    result = parse(['in', ['get', 'attr'], 1, 2, 3, 4])
    assert result == ast.In(
        ast.Attribute('attr'), [
            1,
            2,
            3,
            4,
        ],
        False
    )


def test_id_in_list():
    result = parse(['in', ['id'], 'someID', 'anotherID'])
    assert result == ast.In(
        ast.Attribute('id'), [
            'someID',
            'anotherID'
        ],
        False
    )


def test_attribute_before():
    result = parse(['before', ['get', 'attr'], '2000-01-01T00:00:01Z'])
    assert result == ast.TimeBefore(
        ast.Attribute('attr'),
        datetime(
            2000, 1, 1, 0, 0, 1,
            tzinfo=StaticTzInfo('Z', timedelta(0))
        ),
    )


def test_attribute_after_dt_dt():
    result = parse([
        'after', ['get', 'attr'],
        '2000-01-01T00:00:00Z', '2000-01-01T00:00:01Z'
    ])

    assert result == ast.TimeAfter(
        ast.Attribute('attr'),
        values.Interval(
            datetime(
                2000, 1, 1, 0, 0, 0,
                tzinfo=StaticTzInfo('Z', timedelta(0))
            ),
            datetime(
                2000, 1, 1, 0, 0, 1,
                tzinfo=StaticTzInfo('Z', timedelta(0))
            ),
        ),
    )


def test_attribute_during_dt_dt():
    result = parse([
        'during', ['get', 'attr'],
        '2000-01-01T00:00:00Z', '2000-01-01T00:00:01Z'
    ])

    assert result == ast.TimeDuring(
        ast.Attribute('attr'),
        values.Interval(
            datetime(
                2000, 1, 1, 0, 0, 0,
                tzinfo=StaticTzInfo('Z', timedelta(0))
            ),
            datetime(
                2000, 1, 1, 0, 0, 1,
                tzinfo=StaticTzInfo('Z', timedelta(0))
            ),
        ),
    )


def test_intersects_attr_point():
    result = parse([
        'intersects',
        ['geometry'],
        {
            'type': 'Point',
            'coordinates': [1, 1],
        }
    ])
    assert result == ast.GeometryIntersects(
        ast.Attribute('geometry'),
        values.Geometry(
            normalize_geom(
                geometry.Point(1, 1).__geo_interface__
            )
        ),
    )


def test_within_multipolygon_attr():
    result = parse([
        'within',
        {
            'type': 'MultiPolygon',
            'coordinates': [
                [[[1, 1], [2, 2], [0, 3], [1, 1]]]
            ],
            'bbox': [0.0, 1.0, 2.0, 3.0]
        },
        ['geometry'],
    ])
    assert result == ast.GeometryWithin(
        values.Geometry(
            normalize_geom(
                geometry.MultiPolygon.from_polygons(
                    geometry.Polygon([(1, 1), (2, 2), (0, 3), (1, 1)])
                ).__geo_interface__
            ),
        ),
        ast.Attribute('geometry'),
    )


def test_logical_all():
    result = parse([
        'all',
        ['>', ['get', 'height'], 50],
        ['==', ['get', 'type'], 'commercial'],
        ['get', 'occupied']
    ])
    assert result == ast.And(
        ast.And(
            ast.GreaterThan(
                ast.Attribute('height'),
                50,
            ),
            ast.Equal(
                ast.Attribute('type'),
                'commercial'
            )
        ),
        ast.Attribute('occupied')
    )


def test_logical_any():
    result = parse([
        'any',
        ['<', ['get', 'height'], 50],
        ['!', ['get', 'occupied']]
    ])
    assert result == ast.Or(
        ast.LessThan(
            ast.Attribute('height'),
            50,
        ),
        ast.Not(
            ast.Attribute('occupied')
        )
    )


def test_attribute_arithmetic_add():
    result = parse(['==', ['get', 'attr'], ['+', 5, 2]])
    assert result == ast.Equal(
        ast.Attribute('attr'),
        ast.Add(
            5,
            2,
        ),
    )


def test_attribute_arithmetic_sub():
    result = parse(['==', ['get', 'attr'], ['-', 5, 2]])
    assert result == ast.Equal(
        ast.Attribute('attr'),
        ast.Sub(
            5,
            2,
        ),
    )


def test_attribute_arithmetic_mul():
    result = parse(['==', ['get', 'attr'], ['*', 5, 2]])
    assert result == ast.Equal(
        ast.Attribute('attr'),
        ast.Mul(
            5,
            2,
        ),
    )


def test_attribute_arithmetic_div():
    result = parse(['==', ['get', 'attr'], ['/', 5, 2]])
    assert result == ast.Equal(
        ast.Attribute('attr'),
        ast.Div(
            5,
            2,
        ),
    )


def test_attribute_arithmetic_add_mul():
    result = parse(['==', ['get', 'attr'], ['+', 3, ['*', 5, 2]]])
    assert result == ast.Equal(
        ast.Attribute('attr'),
        ast.Add(
            3,
            ast.Mul(
                5,
                2,
            ),
        ),
    )


def test_attribute_arithmetic_div_sub():
    result = parse(['==', ['get', 'attr'], ['-', ['/', 3, 5], 2]])
    assert result == ast.Equal(
        ast.Attribute('attr'),
        ast.Sub(
            ast.Div(
                3,
                5,
            ),
            2,
        ),
    )


def test_attribute_arithmetic_div_sub_bracketted():
    result = parse(['==', ['get', 'attr'], ['/', 3, ['-', 5, 2]]])
    assert result == ast.Equal(
        ast.Attribute('attr'),
        ast.Div(
            3,
            ast.Sub(
                5,
                2,
            ),
        ),
    )


def test_arithmetic_modulo():
    result = parse(['==', ['get', 'attr'], ['%', 3, 7]])
    assert result == ast.Equal(
        ast.Attribute('attr'),
        ast.Function(
            'mod',
            [3, 7],
        ),
    )


def test_arithmetic_floor():
    result = parse(['==', ['floor', ['get', 'age']], 42])
    assert result == ast.Equal(
        ast.Function(
            'floor', [
                ast.Attribute('age'),
            ],
        ),
        42
    )


def test_arithmetic_ceil():
    result = parse(['==', ['ceil', ['get', 'age']], 42])
    assert result == ast.Equal(
        ast.Function(
            'ceil', [
                ast.Attribute('age'),
            ],
        ),
        42
    )


def test_arithmetic_abs():
    result = parse(['>', ['abs', ['get', 'delta']], 1])
    assert result == ast.GreaterThan(
        ast.Function(
            'abs', [
                ast.Attribute('delta'),
            ],
        ),
        1
    )


def test_arithmetic_pow():
    result = parse(['>', ['^', ['get', 'size'], 2], 100])
    assert result == ast.GreaterThan(
        ast.Function(
            'pow', [
                ast.Attribute('size'),
                2
            ],
        ),
        100
    )


def test_arithmetic_min():
    result = parse(['>', ['min', ['get', 'wins'], ['get', 'ties']], 10])
    assert result == ast.GreaterThan(
        ast.Function(
            'min', [
                ast.Attribute('wins'),
                ast.Attribute('ties'),
            ],
        ),
        10
    )


def test_arithmetic_max():
    result = parse(['>', ['max', ['get', 'wins'], ['get', 'ties']], 10])
    assert result == ast.GreaterThan(
        ast.Function(
            'max', [
                ast.Attribute('wins'),
                ast.Attribute('ties'),
            ],
        ),
        10
    )
