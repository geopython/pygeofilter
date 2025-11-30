# ------------------------------------------------------------------------------
#
# Project: pygeofilter <https://github.com/geopython/pygeofilter>
# Authors: Magnar Martinsen <magnarem@met.no>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2025 Norwegian Meteorological Institute
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

# pylint: disable=W0621,C0114,C0115,C0116

import json

import pytest
import requests

from pygeofilter import ast
from pygeofilter.backends.solr import to_filter
from pygeofilter.backends.solr.evaluate import SOLRDSLEvaluator, SolrDSLQuery
from pygeofilter.parsers.ecql import parse
from pygeofilter.util import parse_datetime

SOLR_BASE_URL = "http://localhost:8983/solr/test"  # replace with your Solr URL
HEADERS = {
    "Content-type": "application/json",
}

# input documents for testing
INPUT_DOCS = [
    {
        "id": "A",
        "geometry_jts": "MULTIPOLYGON(((0 0, 0 5, 5 5,5 0,0 0)))",
        "center": "POINT(2.5 2.5)",
        "float_attribute": 0.0,
        "int_attribute": 5,
        "str_attribute": "this is a test",
        "datetime_attribute": "2000-01-01T00:00:00Z",
        "daterange_attribute": "[2000-01-01T00:00:00Z TO 2000-01-02T00:00:00Z]",
    },
    {
        "id": "B",
        "geospatial_jts": "MULTIPOLYGON(((5 5, 5 10, 10 10,10 5,5 5)))",
        "center": "POINT(7.5 7.5)",
        "float_attribute": 30.0,
        "str_attribute": "this is another test",
        "maybe_str_attribute": "some value",
        "datetime_attribute": "2000-01-01T00:00:10Z",
        "daterange_attribute": "[2000-01-04T00:00:00Z TO 2000-01-05T00:00:00Z]",
    },
]


@pytest.fixture(autouse=True, scope="session")
def prepare():
    """Prepare the Solr instance. Add the fields needed for testing"""
    # print('Preparing core')
    # Create a new core
    # res = requests.get('http://localhost:8983/solr/admin/cores?action=CREATE&name=test&configSet= /opt/solr/server/solr/configsets/_default/conf')
    # print(res)
    # Add the field types
    field_types = [
        {
            "name": "spatial_jts",
            "class": "solr.SpatialRecursivePrefixTreeFieldType",
            "autoIndex": "true",
            "spatialContextFactory": "JTS",
            "validationRule": "repairBuffer0",
            "distErrPct": "0.025",
            "maxDistErr": "0.001",
            "distanceUnits": "kilometers",
        },
        {"name": "date_range", "class": "solr.DateRangeField"},
    ]

    for field_type in field_types:
        data = json.dumps({"add-field-type": field_type})
        requests.post(
            "http://localhost:8983/api/cores/test/schema", headers={"Content-type": "application/json"}, data=data
        )

    # Define the fields to be added
    fields = [
        {"name": "extra_attr", "type": "string"},
        {"name": "float_attribute", "type": "pdouble"},
        {"name": "int_attribute", "type": "pint"},
        {"name": "datetime_attribute", "type": "pdate"},
        {"name": "str_attribute", "type": "text_general"},
        {"name": "center", "type": "location"},
        {"name": "geometry_jts", "type": "spatial_jts", "multiValued": "false"},
        {"name": "daterange_attribute", "type": "date_range"},
    ]

    # Add the fields to the schema
    for field in fields:
        data = json.dumps({"add-field": field})
        requests.post(
            "http://localhost:8983/api/cores/test/schema", headers={"Content-type": "application/json"}, data=data
        )
    index = "ok"
    yield index
    print("cleaning up")
    requests.get(SOLR_BASE_URL + "/admin/cores?action=UNLOAD&core=test&deleteIndex=true")


@pytest.fixture(autouse=True, scope="session")
def index(prepare):
    # Add test documents
    response = requests.post(SOLR_BASE_URL + "/update", data=json.dumps(INPUT_DOCS), headers=HEADERS)
    print(response.json())
    # Commit index
    res = requests.get(SOLR_BASE_URL + "/update?commit=true")
    print(res.json())


@pytest.fixture(autouse=True, scope="session")
def data(index):
    """Fixture to add initial data to the search index."""
    data = {
        "query": "id:A",  # Query
    }
    response = requests.get(SOLR_BASE_URL + "/query", data=json.dumps(data), headers=HEADERS)
    response_json = response.json()
    if response_json["responseHeader"]["status"] == 0:
        # Print the response
        record_a = response_json["response"]["docs"][0]

    data = {
        "query": "id:B",  # Query
    }
    response = requests.post(SOLR_BASE_URL + "/query", json=data)
    response_json = response.json()
    if response_json["responseHeader"]["status"] == 0:
        # Print the response
        record_b = response_json["response"]["docs"][0]

    yield [record_a, record_b]


def filter_(ast_):
    print("Ast Query: ", ast.get_repr(ast_))
    query = to_filter(ast_, version="9.8.1")
    print("Solr Query: ", query)
    response = requests.post(SOLR_BASE_URL + "/select", json=query)
    response_json = response.json()
    print("Solr response: ", response_json)
    print("\n")
    return response_json["response"]["docs"]


def test_comparison(data):
    result = filter_(parse("int_attribute = 5"))
    assert len(result) == 1 and result[0]["id"] == data[0]["id"]

    result = filter_(parse("float_attribute < 6.0"))
    assert len(result) == 1 and result[0]["id"] == data[0]["id"]

    result = filter_(parse("float_attribute > 6.0"))
    assert len(result) == 1 and result[0]["id"] == data[1]["id"]

    result = filter_(parse("int_attribute <= 5"))
    assert len(result) == 1 and result[0]["id"] == data[0]["id"]

    result = filter_(parse("float_attribute >= 8.0"))
    assert len(result) == 1 and result[0]["id"] == data[1]["id"]

    result = filter_(parse("float_attribute <> 0.0"))
    assert len(result) == 1 and result[0]["id"] == data[1]["id"]


def test_combination(data):
    result = filter_(parse("int_attribute = 5 AND float_attribute < 6.0"))
    assert len(result) == 1 and result[0]["id"] is data[0]["id"]

    result = filter_(parse("int_attribute = 6 OR float_attribute < 6.0"))
    assert len(result) == 1 and result[0]["id"] is data[0]["id"]


def test_between(data):
    result = filter_(parse("float_attribute BETWEEN -1 AND 1"))
    assert len(result) == 1 and result[0]["id"] is data[0]["id"]

    result = filter_(parse("int_attribute NOT BETWEEN 4 AND 6"))
    assert len(result) == 1 and result[0]["id"] is data[1]["id"]

    result = filter_(parse("int_attribute = 6 OR float_attribute < 6.0"))
    assert len(result) == 1 and result[0]["id"] is data[0]["id"]


def test_like(data):
    result = filter_(parse("str_attribute LIKE 'this is a test'"))
    assert len(result) == 1 and result[0]["id"] is data[0]["id"]

    result = filter_(parse("str_attribute LIKE 'this is % test'"))
    assert len(result) == 2

    result = filter_(parse("str_attribute NOT LIKE '% another test'"))
    assert len(result) == 1 and result[0]["id"] is data[0]["id"]

    result = filter_(parse("str_attribute NOT LIKE 'this is . test'"))
    assert len(result) == 1 and result[0]["id"] is data[1]["id"]

    result = filter_(parse("str_attribute ILIKE 'THIS IS . TEST'"))
    assert len(result) == 1 and result[0]["id"] is data[0]["id"]

    result = filter_(parse("str_attribute ILIKE 'THIS IS % TEST'"))
    assert len(result) == 2


def test_combination_like_not(data):
    result = filter_(parse("NOT str_attribute LIKE 'another'"))
    assert len(result) == 1 and result[0]["id"] is data[0]["id"]

    result = filter_(parse("str_attribute LIKE 'test' AND NOT str_attribute LIKE 'another'"))
    assert len(result) == 1 and result[0]["id"] is data[0]["id"]

    result = filter_(parse("NOT str_attribute LIKE 'another' AND str_attribute LIKE 'test'"))
    assert len(result) == 1 and result[0]["id"] is data[0]["id"]

    result = filter_(parse("NOT str_attribute LIKE 'test' AND str_attribute LIKE 'another'"))
    assert len(result) == 0

    result = filter_(parse("str_attribute LIKE 'test' OR NOT str_attribute LIKE 'another'"))
    assert len(result) == 1 and result[0]["id"] is data[0]["id"]

    result = filter_(parse("str_attribute LIKE 'test' OR NOT str_attribute LIKE 'another'"))
    assert len(result) == 1 and result[0]["id"] is data[0]["id"]

    result = filter_(parse("NOT str_attribute LIKE 'another' OR str_attribute LIKE 'test'"))
    assert len(result) == 1 and result[0]["id"] is data[0]["id"]


def test_in(data):
    result = filter_(parse("int_attribute IN ( 1, 2, 3, 4, 5 )"))
    assert len(result) == 1 and result[0]["id"] is data[0]["id"]

    result = filter_(parse("int_attribute NOT IN ( 1, 2, 3, 4, 5 )"))
    assert len(result) == 1 and result[0]["id"] is data[1]["id"]


def test_null(data):
    result = filter_(parse("maybe_str_attribute IS NULL"))
    assert len(result) == 1 and result[0]["id"] is data[0]["id"]

    result = filter_(parse("maybe_str_attribute IS NOT NULL"))
    assert len(result) == 1 and result[0]["id"] is data[1]["id"]


def test_has_attr():
    result = filter_(parse("extra_attr EXISTS"))
    assert len(result) == 0

    result = filter_(parse("extra_attr DOES-NOT-EXIST"))
    assert len(result) == 2


def test_temporal(data):
    result = filter_(
        ast.TimeDisjoint(
            ast.Attribute("datetime_attribute"),
            [
                parse_datetime("2000-01-01T00:00:05.00Z"),
                parse_datetime("2000-01-01T00:00:15.00Z"),
            ],
        )
    )
    assert len(result) == 1 and result[0]["id"] is data[0]["id"]

    result = filter_(
        parse("datetime_attribute BEFORE 2000-01-01T00:00:05.00Z"),
    )
    assert len(result) == 1 and result[0]["id"] is data[0]["id"]

    result = filter_(
        parse("datetime_attribute AFTER 2000-01-01T00:00:05.00Z"),
    )
    assert len(result) == 1 and result[0]["id"] is data[1]["id"]


def test_dsl_query_obj():
    """test the solr DSL query object"""
    q = SolrDSLQuery()
    assert q == {"query": "*:*"}

    q.add_filter("status:active")
    assert q == {"query": "*:*", "filter": ["status:active"]}

    q = SolrDSLQuery("text:ice")
    assert q == {"query": "text:ice"}

    q.add_filter("status:active")
    assert q == {"query": "text:ice", "filter": ["status:active"]}

    q = SolrDSLQuery(filters="collection:ice")
    assert q == {"query": "*:*", "filter": ["collection:ice"]}

    q.add_filter("status:active")
    assert q == {"query": "*:*", "filter": ["collection:ice", "status:active"]}

    q = SolrDSLQuery("text:ice", filters="collection:ice")
    assert q == {"query": "text:ice", "filter": ["collection:ice"]}

    q = SolrDSLQuery("text:ice", filters="collection:ice")
    assert q == {"query": "text:ice", "filter": ["collection:ice"]}

    q.add_filter("status:active")
    assert q == {"query": "text:ice", "filter": ["collection:ice", "status:active"]}

    q = SolrDSLQuery(filters=["collection:ice", "int_field:[3 TO 10]"])
    assert q == {"query": "*:*", "filter": ["collection:ice", "int_field:[3 TO 10]"]}

    q.add_filter("status:active")
    assert q == {"query": "*:*", "filter": ["collection:ice", "int_field:[3 TO 10]", "status:active"]}


def test_attribute_mapping_fallback():
    # attribute_map does not contain 'dc:subject'
    evaluator = SOLRDSLEvaluator(attribute_map={"foo": "bar"})
    node = ast.Attribute("dc:subject")
    result = evaluator.attribute(node)
    assert result == "dc:subject"

    # attribute_map contains the key
    evaluator2 = SOLRDSLEvaluator(attribute_map={"dc:subject": "subject_s"})
    node2 = ast.Attribute("dc:subject")
    result2 = evaluator2.attribute(node2)
    assert result2 == "subject_s"


# def test_array():
#     result = filter_(
#         ast.ArrayEquals(
#             ast.Attribute('array_attr'),
#             [2, 3],
#         ),
#         data
#     )
#     assert len(result) == 1 and result[0] is data[0]

#     result = filter_(
#         ast.ArrayContains(
#             ast.Attribute('array_attr'),
#             [1, 2, 3, 4],
#         ),
#         data
#     )
#     assert len(result) == 1 and result[0] is data[1]

#     result = filter_(
#         ast.ArrayContainedBy(
#             ast.Attribute('array_attr'),
#             [1, 2, 3, 4],
#         ),
#         data
#     )
#     assert len(result) == 1 and result[0] is data[0]

#     result = filter_(
#         ast.ArrayOverlaps(
#             ast.Attribute('array_attr'),
#             [5, 6, 7],
#         ),
#         data
#     )
#     assert len(result) == 1 and result[0] is data[1]


def test_spatial_and_text(data):
    ast = parse("INTERSECTS(geometry_jts, ENVELOPE (0.0 1.0 0.0 1.0)) AND str_attribute LIKE 'this is a test'")
    result = filter_(ast)
    assert len(result) == 1


def test_spatial(data):
    result = filter_(parse("INTERSECTS(geometry_jts, ENVELOPE (0.0 1.0 0.0 1.0))"))
    assert len(result) == 1 and result[0]["id"] is data[0]["id"]

    result = filter_(parse("INTERSECTS(geometry_jts, POLYGON((0.0 0.0, 1.0 0.0, 1.0 1.0, 0.0 1.0, 0.0 0.0)))"))
    assert len(result) == 1 and result[0]["id"] is data[0]["id"]

    result = filter_(
        parse("BBOX(center, 2, 2, 3, 3)"),
    )
    assert len(result) == 1 and result[0]["id"] is data[0]["id"]

    result = filter_(parse("DISJOINT(geometry_jts, POLYGON((0.0 0.0, 1.0 0.0, 1.0 1.0, 0.0 1.0, 0.0 0.0)))"))
    assert len(result) == 1 and result[0]["id"] is data[1]["id"]

    result = filter_(parse("NOT DISJOINT(geometry_jts, POLYGON((0.0 0.0, 1.0 0.0, 1.0 1.0, 0.0 1.0, 0.0 0.0)))"))
    assert len(result) == 1 and result[0]["id"] is data[0]["id"]


# def test_arithmetic():
#     result = filter_(
#         parse('int_attr = float_attr - 0.5'),
#         data,
#     )
#     assert len(result) == 2

#     result = filter_(
#         parse('int_attr = 5 + 20 / 2 - 10'),
#         data,
#     )
#     assert len(result) == 1 and result[0] is data[0]


# def test_function():
#     result = filter_(
#         parse('sin(float_attr) BETWEEN -0.75 AND -0.70'),
#         data,
#     )
#     assert len(result) == 1 and result[0] is data[0]


# def test_nested():
#     result = filter_(
#         parse('"nested_attr.str_attr" = \'this is a test\''),
#         data,
#     )
#     assert len(result) == 1 and result[0] is data[0]
