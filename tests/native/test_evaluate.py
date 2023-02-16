import math
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import List, Optional

import pytest
from shapely.geometry import Point

from pygeofilter import ast
from pygeofilter.backends.native.evaluate import NativeEvaluator
from pygeofilter.parsers.ecql import parse


@dataclass
class Nested:
    str_attr: str


@dataclass
class Record:
    str_attr: str
    maybe_str_attr: Optional[str]
    int_attr: int
    float_attr: float
    date_attr: date
    datetime_attr: datetime
    point_attr: Point
    array_attr: List[int]
    nested_attr: Nested


@pytest.fixture
def data():
    data = [
        Record(
            "this is a test",
            None,
            5,
            5.5,
            date(2010, 1, 1),
            datetime(2010, 1, 1, tzinfo=timezone.utc),
            Point(1, 1),
            [2, 3],
            Nested("this is a test"),
        ),
        Record(
            "this is another test",
            "not null",
            8,
            8.5,
            date(2010, 1, 10),
            datetime(2010, 1, 10, tzinfo=timezone.utc),
            Point(2, 2),
            [1, 2, 3, 4, 5],
            Nested("this is another test"),
        ),
    ]

    data[0].extra_attr = 123

    return data


def filter_(ast, data):
    filter_expr = NativeEvaluator(
        math.__dict__,
        allow_nested_attributes=True,
    ).evaluate(ast)

    return [record for record in data if filter_expr(record)]


@pytest.fixture
def data_json():
    data = [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": (1, 1)},
            "properties": {
                "str_attr": "this is a test",
                "maybe_str_attr": None,
                "int_attr": 5,
                "float_attr": 5.5,
                "date_attr": "2010-01-01",
                "datetime_attr": "2010-01-01T00:00:00Z",
                "array_attr": [2, 3],
                "extra_attr": 123,
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": (2, 2)},
            "properties": {
                "str_attr": "this is another test",
                "maybe_str_attr": "not null",
                "int_attr": 8,
                "float_attr": 8.5,
                "date_attr": "2010-01-10",
                "datetime_attr": "2010-01-10T00:00:00Z",
                "array_attr": [1, 2, 3, 4, 5],
            },
        },
    ]

    return data


def filter_json(ast, data):
    attr_map = {"point_attr": "geometry", "*": "properties.*"}
    filter_expr = NativeEvaluator(math.__dict__, attr_map, use_getattr=False).evaluate(
        ast
    )
    return [record for record in data if filter_expr(record)]


def test_comparison(data):
    result = filter_(parse("int_attr = 5"), data)
    assert len(result) == 1 and result[0] is data[0]

    result = filter_(parse("int_attr < 6"), data)
    assert len(result) == 1 and result[0] is data[0]

    result = filter_(parse("int_attr > 6"), data)
    assert len(result) == 1 and result[0] is data[1]

    result = filter_(parse("int_attr <= 5"), data)
    assert len(result) == 1 and result[0] is data[0]

    result = filter_(parse("int_attr >= 8"), data)
    assert len(result) == 1 and result[0] is data[1]

    result = filter_(parse("int_attr <> 5"), data)
    assert len(result) == 1 and result[0] is data[1]


def test_comparison_json(data_json):
    result = filter_json(parse("int_attr = 5"), data_json)
    assert len(result) == 1 and result[0] is data_json[0]

    result = filter_json(parse("int_attr < 6"), data_json)
    assert len(result) == 1 and result[0] is data_json[0]

    result = filter_json(parse("int_attr > 6"), data_json)
    assert len(result) == 1 and result[0] is data_json[1]

    result = filter_json(parse("int_attr <= 5"), data_json)
    assert len(result) == 1 and result[0] is data_json[0]

    result = filter_json(parse("int_attr >= 8"), data_json)
    assert len(result) == 1 and result[0] is data_json[1]

    result = filter_json(parse("int_attr <> 5"), data_json)
    assert len(result) == 1 and result[0] is data_json[1]


def test_combination(data):
    result = filter_(parse("int_attr = 5 AND float_attr < 6.0"), data)
    assert len(result) == 1 and result[0] is data[0]

    result = filter_(parse("int_attr = 5 AND float_attr < 6.0"), data)
    assert len(result) == 1 and result[0] is data[0]


def test_combination_json(data_json):
    result = filter_json(parse("int_attr = 5 AND float_attr < 6.0"), data_json)
    assert len(result) == 1 and result[0] is data_json[0]

    result = filter_json(parse("int_attr = 5 AND float_attr < 6.0"), data_json)
    assert len(result) == 1 and result[0] is data_json[0]


def test_between(data):
    result = filter_(parse("float_attr BETWEEN 4 AND 6"), data)
    assert len(result) == 1 and result[0] is data[0]

    result = filter_(parse("int_attr NOT BETWEEN 4 AND 6"), data)
    assert len(result) == 1 and result[0] is data[1]


def test_between_json(data_json):
    result = filter_json(parse("float_attr BETWEEN 4 AND 6"), data_json)
    assert len(result) == 1 and result[0] is data_json[0]

    result = filter_json(parse("int_attr NOT BETWEEN 4 AND 6"), data_json)
    assert len(result) == 1 and result[0] is data_json[1]


def test_like(data):
    result = filter_(parse("str_attr LIKE 'this is . test'"), data)
    assert len(result) == 1 and result[0] is data[0]

    result = filter_(parse("str_attr LIKE 'this is % test'"), data)
    assert len(result) == 2

    result = filter_(parse("str_attr NOT LIKE '% another test'"), data)
    assert len(result) == 1 and result[0] is data[0]

    result = filter_(parse("str_attr NOT LIKE 'this is . test'"), data)
    assert len(result) == 1 and result[0] is data[1]

    result = filter_(parse("str_attr ILIKE 'THIS IS . TEST'"), data)
    assert len(result) == 1 and result[0] is data[0]

    result = filter_(parse("str_attr ILIKE 'THIS IS % TEST'"), data)
    assert len(result) == 2


def test_like_json(data_json):
    result = filter_json(parse("str_attr LIKE 'this is . test'"), data_json)
    assert len(result) == 1 and result[0] is data_json[0]

    result = filter_json(parse("str_attr LIKE 'this is % test'"), data_json)
    assert len(result) == 2

    result = filter_json(parse("str_attr NOT LIKE '% another test'"), data_json)
    assert len(result) == 1 and result[0] is data_json[0]

    result = filter_json(parse("str_attr NOT LIKE 'this is . test'"), data_json)
    assert len(result) == 1 and result[0] is data_json[1]

    result = filter_json(parse("str_attr ILIKE 'THIS IS . TEST'"), data_json)
    assert len(result) == 1 and result[0] is data_json[0]

    result = filter_json(parse("str_attr ILIKE 'THIS IS % TEST'"), data_json)
    assert len(result) == 2


def test_in(data):
    result = filter_(parse("int_attr IN ( 1, 2, 3, 4, 5 )"), data)
    assert len(result) == 1 and result[0] is data[0]

    result = filter_(parse("int_attr NOT IN ( 1, 2, 3, 4, 5 )"), data)
    assert len(result) == 1 and result[0] is data[1]


def test_in_json(data_json):
    result = filter_json(parse("int_attr IN ( 1, 2, 3, 4, 5 )"), data_json)
    assert len(result) == 1 and result[0] is data_json[0]

    result = filter_json(parse("int_attr NOT IN ( 1, 2, 3, 4, 5 )"), data_json)
    assert len(result) == 1 and result[0] is data_json[1]


def test_null(data):
    result = filter_(parse("maybe_str_attr IS NULL"), data)
    assert len(result) == 1 and result[0] is data[0]

    result = filter_(parse("maybe_str_attr IS NOT NULL"), data)
    assert len(result) == 1 and result[0] is data[1]


def test_null_json(data_json):
    result = filter_json(parse("maybe_str_attr IS NULL"), data_json)
    assert len(result) == 1 and result[0] is data_json[0]

    result = filter_json(parse("maybe_str_attr IS NOT NULL"), data_json)
    assert len(result) == 1 and result[0] is data_json[1]


def test_has_attr(data):
    result = filter_(parse("extra_attr EXISTS"), data)
    assert len(result) == 1 and result[0] is data[0]

    result = filter_(parse("extra_attr DOES-NOT-EXIST"), data)
    assert len(result) == 1 and result[0] is data[1]


def test_has_attr_json(data_json):
    result = filter_json(parse("extra_attr EXISTS"), data_json)
    assert len(result) == 1 and result[0] is data_json[0]

    result = filter_json(parse("extra_attr DOES-NOT-EXIST"), data_json)
    assert len(result) == 1 and result[0] is data_json[1]


def test_temporal(data):
    result = filter_(parse("date_attr BEFORE 2010-01-08T00:00:00.00Z"), data)
    assert len(result) == 1 and result[0] is data[0]

    result = filter_(parse("date_attr AFTER 2010-01-08T00:00:00.00+01:00"), data)
    assert len(result) == 1 and result[0] is data[1]


def test_temporal_json(data_json):
    result = filter_json(parse("date_attr BEFORE 2010-01-08T00:00:00.00Z"), data_json)
    assert len(result) == 1 and result[0] is data_json[0]

    result = filter_json(
        parse("date_attr AFTER 2010-01-08T00:00:00.00+01:00"), data_json
    )
    assert len(result) == 1 and result[0] is data_json[1]


def test_array(data):
    result = filter_(
        ast.ArrayEquals(
            ast.Attribute("array_attr"),
            [2, 3],
        ),
        data,
    )
    assert len(result) == 1 and result[0] is data[0]

    result = filter_(
        ast.ArrayContains(
            ast.Attribute("array_attr"),
            [1, 2, 3, 4],
        ),
        data,
    )
    assert len(result) == 1 and result[0] is data[1]

    result = filter_(
        ast.ArrayContainedBy(
            ast.Attribute("array_attr"),
            [1, 2, 3, 4],
        ),
        data,
    )
    assert len(result) == 1 and result[0] is data[0]

    result = filter_(
        ast.ArrayOverlaps(
            ast.Attribute("array_attr"),
            [5, 6, 7],
        ),
        data,
    )
    assert len(result) == 1 and result[0] is data[1]


def test_array_json(data_json):
    result = filter_json(
        ast.ArrayEquals(
            ast.Attribute("array_attr"),
            [2, 3],
        ),
        data_json,
    )
    assert len(result) == 1 and result[0] is data_json[0]

    result = filter_json(
        ast.ArrayContains(
            ast.Attribute("array_attr"),
            [1, 2, 3, 4],
        ),
        data_json,
    )
    assert len(result) == 1 and result[0] is data_json[1]

    result = filter_json(
        ast.ArrayContainedBy(
            ast.Attribute("array_attr"),
            [1, 2, 3, 4],
        ),
        data_json,
    )
    assert len(result) == 1 and result[0] is data_json[0]

    result = filter_json(
        ast.ArrayOverlaps(
            ast.Attribute("array_attr"),
            [5, 6, 7],
        ),
        data_json,
    )
    assert len(result) == 1 and result[0] is data_json[1]


def test_spatial(data):
    result = filter_(
        parse("INTERSECTS(point_attr, ENVELOPE (0 1 0 1))"),
        data,
    )
    assert len(result) == 1 and result[0] is data[0]

    result = filter_(
        parse("EQUALS(point_attr, POINT(2 2))"),
        data,
    )
    assert len(result) == 1 and result[0] is data[1]

    result = filter_(
        parse("BBOX(point_attr, 0.5, 0.5, 1.5, 1.5)"),
        data,
    )
    assert len(result) == 1 and result[0] is data[0]


def test_spatial_json(data_json):
    result = filter_json(
        parse("INTERSECTS(point_attr, ENVELOPE (0 1 0 1))"),
        data_json,
    )
    assert len(result) == 1 and result[0] is data_json[0]

    result = filter_json(
        parse("EQUALS(point_attr, POINT(2 2))"),
        data_json,
    )
    assert len(result) == 1 and result[0] is data_json[1]

    result = filter_json(
        parse("BBOX(point_attr, 0.5, 0.5, 1.5, 1.5)"),
        data_json,
    )
    assert len(result) == 1 and result[0] is data_json[0]


def test_arithmetic(data):
    result = filter_(
        parse("int_attr = float_attr - 0.5"),
        data,
    )
    assert len(result) == 2

    result = filter_(
        parse("int_attr = 5 + 20 / 2 - 10"),
        data,
    )
    assert len(result) == 1 and result[0] is data[0]


def test_arithmetic_json(data_json):
    result = filter_json(
        parse("int_attr = float_attr - 0.5"),
        data_json,
    )
    assert len(result) == 2

    result = filter_json(
        parse("int_attr = 5 + 20 / 2 - 10"),
        data_json,
    )
    assert len(result) == 1 and result[0] is data_json[0]


def test_function(data):
    result = filter_(
        parse("sin(float_attr) BETWEEN -0.75 AND -0.70"),
        data,
    )
    assert len(result) == 1 and result[0] is data[0]


def test_function_json(data_json):
    result = filter_json(
        parse("sin(float_attr) BETWEEN -0.75 AND -0.70"),
        data_json,
    )
    assert len(result) == 1 and result[0] is data_json[0]


def test_nested(data):
    result = filter_(
        parse("\"nested_attr.str_attr\" = 'this is a test'"),
        data,
    )
    assert len(result) == 1 and result[0] is data[0]
