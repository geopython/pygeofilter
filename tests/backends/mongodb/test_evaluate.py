# pylint: disable=W0621,C0114,C0115,C0116,C0103

import pymongo
import pytest
from pymongo import MongoClient

from pygeofilter.parsers.ecql import parse
from pygeofilter.backends.mongodb import to_filter
from pygeofilter.util import parse_datetime
from pygeofilter import ast


@pytest.fixture
def client():
    return MongoClient()


@pytest.fixture
def db(client):
    return client["test-db"]


@pytest.fixture
def collection(db):
    return db["test-collection"]


@pytest.fixture
def data(collection):
    collection.create_index([
        ("geometry", pymongo.GEOSPHERE),
        ("center", pymongo.GEOSPHERE),
        # ("identifier"),
    ])
    id_a = collection.insert_one({
        "identifier": "A",
        "geometry": {
            "type": "MultiPolygon",
            "coordinates": [[[
                [0, 0],
                [0, 5],
                [5, 5],
                [5, 0],
                [0, 0]
            ]]],
        },
        "center": {
            "type": "Point",
            "coordinates": [2.5, 2.5],
        },
        "float_attribute": 0.0,
        "int_attribute": 5,
        "str_attribute": "this is a test",
        "maybe_str_attribute": None,
        "datetime_attribute": parse_datetime("2000-01-01T00:00:00Z"),
        "array_attribute": [2, 3],
        "extra_attribute": True,
    }).inserted_id
    record_a = collection.find_one({"_id": id_a})

    id_b = collection.insert_one({
        "identifier": "B",
        "geometry": {
            "type": "MultiPolygon",
            "coordinates": [[[
                [5, 5],
                [5, 10],
                [10, 10],
                [10, 5],
                [5, 5]
            ]]],
        },
        "center": {
            "type": "Point",
            "coordinates": [7.5, 7.5],
        },
        "float_attribute": 30.0,
        "int_attribute": None,
        "str_attribute": "this is another test",
        "maybe_str_attribute": "some value",
        "array_attribute": [1, 2, 3, 4, 5],
        "datetime_attribute": parse_datetime("2000-01-01T00:00:10Z"),
    }).inserted_id
    record_b = collection.find_one({"_id": id_b})

    yield [record_a, record_b]

    collection.drop()


@pytest.fixture
def evaluate(collection, data):  # pylint: disable=W0613
    def inner(ast_, expected_ids=None):
        query = to_filter(ast_)
        print(query)
        result = list(collection.find(query))
        if expected_ids is not None:
            assert expected_ids == [r["identifier"] for r in result]
        return result
    return inner


def test_comparison(evaluate):
    evaluate(parse('int_attribute = 5'), ["A"])
    evaluate(parse('float_attribute < 6'), ["A"])
    evaluate(parse('float_attribute > 6'), ["B"])
    evaluate(parse('int_attribute <= 5'), ["A"])
    evaluate(parse('float_attribute >= 8'), ["B"])
    evaluate(parse('float_attribute <> 0.0'), ["B"])


def test_combination(evaluate):
    evaluate(parse('int_attribute = 5 AND float_attribute < 6.0'), ["A"])
    evaluate(parse('int_attribute = 6 OR float_attribute < 6.0'), ["A"])


def test_between(evaluate):
    evaluate(parse('float_attribute BETWEEN -1 AND 1'), ["A"])
    evaluate(parse('int_attribute NOT BETWEEN 4 AND 6'), ["B"])


def test_like(evaluate):
    evaluate(parse('str_attribute LIKE \'this is a test\''), ["A"])
    evaluate(parse('str_attribute LIKE \'this is % test\''), ["A", "B"])
    evaluate(parse('str_attribute NOT LIKE \'% another test\''), ["A"])
    evaluate(parse('str_attribute NOT LIKE \'this is . test\''), ["B"])
    evaluate(parse('str_attribute ILIKE \'THIS IS . TEST\''), ["A"])
    evaluate(parse('str_attribute ILIKE \'THIS IS % TEST\''), ["A", "B"])


def test_in(evaluate):
    evaluate(parse('int_attribute IN ( 1, 2, 3, 4, 5 )'), ["A"])
    evaluate(parse('int_attribute NOT IN ( 1, 2, 3, 4, 5 )'), ["B"])


def test_null(evaluate):
    evaluate(parse('maybe_str_attribute IS NULL'), ["A"])
    evaluate(parse('maybe_str_attribute IS NOT NULL'), ["B"])


def test_has_attr(evaluate):
    evaluate(parse('extra_attribute EXISTS'), ["A"])
    evaluate(parse('extra_attribute DOES-NOT-EXIST'), ["B"])


# def test_temporal(data):
#     result = filter_(
#         ast.TimeDisjoint(
#             ast.Attribute("datetime_attribute"),
#             [
#                 parse_datetime("2000-01-01T00:00:05.00Z"),
#                 parse_datetime("2000-01-01T00:00:15.00Z"),
#             ]
#         )
#     )
#     assert len(result) == 1 and result[0].identifier is data[0].identifier

#     result = filter_(
#         parse('datetime_attribute BEFORE 2000-01-01T00:00:05.00Z'),
#     )
#     assert len(result) == 1 and result[0].identifier is data[0].identifier

#     result = filter_(
#         parse('datetime_attribute AFTER 2000-01-01T00:00:05.00Z'),
#     )
#     assert len(result) == 1 and result[0].identifier is data[1].identifier


def test_spatial(evaluate):
    evaluate(
        parse('INTERSECTS(geometry, ENVELOPE (0.0 1.0 0.0 1.0))'),
        ["A"],
    )
    evaluate(
        parse(
            'WITHIN(geometry, '
            'POLYGON ((-1.0 -1.0,-1.0 6.0, 6.0 6.0,6.0 -1.0,-1.0 -1.0)))'
        ),
        ["A"],
    )
    evaluate(
        parse('BBOX(center, 2, 2, 3, 3)'),
    )


def test_spatial_distance(evaluate):
    evaluate(
        parse('DWITHIN(geometry, POINT(-0.00001 -0.000001), 5, feet)'),
        ["A"]
    )

    evaluate(
        parse('BEYOND(geometry, POINT(7.5 7.5), 10, kilometers)'),
        ["A"]
    )


def test_array(evaluate):
    evaluate(
        ast.ArrayEquals(
            ast.Attribute("array_attribute"),
            [2, 3],
        ),
        ["A"]
    )

    evaluate(
        ast.ArrayOverlaps(
            ast.Attribute("array_attribute"),
            [2, 3, 4],
        ),
        ["A", "B"]
    )

    evaluate(
        ast.ArrayContains(
            ast.Attribute("array_attribute"),
            [1, 2, 3, 4],
        ),
        ["B"]
    )


def test_swapped_lhs_rhs(evaluate):
    evaluate(parse('5 = int_attribute'), ["A"])
    evaluate(parse('6 > float_attribute'), ["A"])
    evaluate(parse('6 < float_attribute'), ["B"])
    evaluate(parse('5 >= int_attribute'), ["A"])
    evaluate(parse('8 <= float_attribute'), ["B"])
    evaluate(parse('0.0 <> float_attribute'), ["B"])

    evaluate(
        parse('INTERSECTS(ENVELOPE (0.0 1.0 0.0 1.0), geometry)'),
        ["A"],
    )
    with pytest.raises(ValueError):
        evaluate(
            parse(
                'WITHIN('
                'POLYGON ((-1.0 -1.0,-1.0 6.0, 6.0 6.0,6.0 -1.0,-1.0 -1.0)),'
                'geometry)'
            ),
            ["A"],
        )

    evaluate(
        ast.ArrayEquals(
            [2, 3],
            ast.Attribute("array_attribute"),
        ),
        ["A"]
    )

    with pytest.raises(ValueError):
        evaluate(
            ast.ArrayOverlaps(
                [2, 3, 4],
                ast.Attribute("array_attribute"),
            ),
            ["A", "B"]
        )

    with pytest.raises(ValueError):
        evaluate(
            ast.ArrayContains(
                [1, 2, 3, 4],
                ast.Attribute("array_attribute"),
            ),
            ["B"]
        )
