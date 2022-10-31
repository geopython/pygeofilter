from datetime import date, datetime

import geopandas
import numpy as np
import pytest
from shapely.geometry import Point

from pygeofilter.backends.geopandas.evaluate import to_filter
from pygeofilter.parsers.ecql import parse


@pytest.fixture
def data():
    return geopandas.GeoDataFrame(
        {
            "str_attr": ["this is a test", "this is another test"],
            "maybe_str_attr": [None, "not null"],
            "int_attr": [5, 8],
            "float_attr": [5.5, 8.5],
            "date_attr": [date(2010, 1, 1), date(2010, 1, 10)],
            "datetime_attr": [datetime(2010, 1, 1), datetime(2010, 1, 10)],
            "point_attr": geopandas.GeoSeries([Point(1, 1), Point(2, 2)]),
        }
    )


def filter_(ast, data):
    function_map = {
        "sin": np.sin,
    }

    return data[to_filter(data, ast, {}, function_map)]


def test_comparison(data):
    result = filter_(parse("int_attr = 5"), data)
    assert len(result) == 1 and result.index[0] == 0

    result = filter_(parse("int_attr < 6"), data)
    assert len(result) == 1 and result.index[0] == 0

    result = filter_(parse("int_attr > 6"), data)
    assert len(result) == 1 and result.index[0] == 1

    result = filter_(parse("int_attr <= 5"), data)
    assert len(result) == 1 and result.index[0] == 0

    result = filter_(parse("int_attr >= 8"), data)
    assert len(result) == 1 and result.index[0] == 1

    result = filter_(parse("int_attr <> 5"), data)
    assert len(result) == 1 and result.index[0] == 1


def test_combination(data):
    result = filter_(parse("int_attr = 5 AND float_attr < 6.0"), data)
    assert len(result) == 1 and result.index[0] == 0

    result = filter_(parse("int_attr = 5 AND float_attr < 6.0"), data)
    assert len(result) == 1 and result.index[0] == 0


def test_between(data):
    result = filter_(parse("float_attr BETWEEN 4 AND 6"), data)
    assert len(result) == 1 and result.index[0] == 0

    result = filter_(parse("int_attr NOT BETWEEN 4 AND 6"), data)
    assert len(result) == 1 and result.index[0] == 1


def test_like(data):
    result = filter_(parse("str_attr LIKE 'this is . test'"), data)
    assert len(result) == 1 and result.index[0] == 0

    result = filter_(parse("str_attr LIKE 'this is % test'"), data)
    assert len(result) == 2

    result = filter_(parse("str_attr NOT LIKE '% another test'"), data)
    assert len(result) == 1 and result.index[0] == 0

    result = filter_(parse("str_attr NOT LIKE 'this is . test'"), data)
    assert len(result) == 1 and result.index[0] == 1

    result = filter_(parse("str_attr ILIKE 'THIS IS . TEST'"), data)
    assert len(result) == 1 and result.index[0] == 0

    result = filter_(parse("str_attr ILIKE 'THIS IS % TEST'"), data)
    assert len(result) == 2


def test_in(data):
    result = filter_(parse("int_attr IN ( 1, 2, 3, 4, 5 )"), data)
    assert len(result) == 1 and result.index[0] == 0

    result = filter_(parse("int_attr NOT IN ( 1, 2, 3, 4, 5 )"), data)
    assert len(result) == 1 and result.index[0] == 1


def test_null(data):
    result = filter_(parse("maybe_str_attr IS NULL"), data)
    assert len(result) == 1 and result.index[0] == 0

    result = filter_(parse("maybe_str_attr IS NOT NULL"), data)
    assert len(result) == 1 and result.index[0] == 1


# TODO: possible?
# def test_has_attr(data):
#     result = filter_(parse('extra_attr EXISTS'), data)
#     assert len(result) == 1 and result[0] is data[0]

#     result = filter_(parse('extra_attr DOES-NOT-EXIST'), data)
#     assert len(result) == 1 and result[0] is data[1]


# def test_temporal(data):
#     result = filter_(
#         parse('date_attr BEFORE 2010-01-08T00:00:00.00Z'),
#         data
#     )
#     assert len(result) == 1 and result.index[0] == 0

#     result = filter_(
#         parse('date_attr AFTER 2010-01-08T00:00:00.00+01:00'),
#         data
#     )
#     assert len(result) == 1 and result.index[0] == 1


def test_spatial(data):
    result = filter_(
        parse("INTERSECTS(point_attr, ENVELOPE (0 1 0 1))"),
        data,
    )
    assert len(result) == 1 and result.index[0] == 0

    result = filter_(
        parse("EQUALS(point_attr, POINT(2 2))"),
        data,
    )
    assert len(result) == 1 and result.index[0] == 1


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
    assert len(result) == 1 and result.index[0] == 0


def test_function(data):
    result = filter_(
        parse("sin(float_attr) BETWEEN -0.75 AND -0.70"),
        data,
    )
    assert len(result) == 1 and result.index[0] == 0
