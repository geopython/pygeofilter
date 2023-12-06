from pygeofilter.backends.oraclesql import (
    to_sql_where,
    to_sql_where_with_binds,
)
from pygeofilter.parsers.ecql import parse

FIELD_MAPPING = {
    "str_attr": "str_attr",
    "int_attr": "int_attr",
    "float_attr": "float_attr",
    "point_attr": "geometry_attr",
}

FUNCTION_MAP = {}


def test_between():
    where = to_sql_where(
        parse("int_attr NOT BETWEEN 4 AND 6"),
        FIELD_MAPPING,
        FUNCTION_MAP
    )
    assert where == "(int_attr NOT BETWEEN 4 AND 6)"


def test_between_with_binds():
    where, binds = to_sql_where_with_binds(
        parse("int_attr NOT BETWEEN 4 AND 6"),
        FIELD_MAPPING,
        FUNCTION_MAP
    )
    assert where == "(int_attr NOT BETWEEN :int_attr_low AND :int_attr_high)"
    assert binds == {"int_attr_low": 4, "int_attr_high": 6}


def test_like():
    where = to_sql_where(
        parse("str_attr LIKE 'foo%'"),
        FIELD_MAPPING,
        FUNCTION_MAP
    )
    assert where == "str_attr LIKE 'foo%' ESCAPE '\\'"


def test_like_with_binds():
    where, binds = to_sql_where_with_binds(
        parse("str_attr LIKE 'foo%'"),
        FIELD_MAPPING,
        FUNCTION_MAP
    )
    assert where == "str_attr LIKE :str_attr ESCAPE '\\'"
    assert binds == {"str_attr": "foo%"}


def test_combination():
    where = to_sql_where(
        parse("int_attr = 5 AND float_attr < 6.0"),
        FIELD_MAPPING,
        FUNCTION_MAP
    )
    assert where == "((int_attr = 5) AND (float_attr < 6.0))"


def test_combination_with_binds():
    where, binds = to_sql_where_with_binds(
        parse("int_attr = 5 AND float_attr < 6.0"),
        FIELD_MAPPING,
        FUNCTION_MAP
    )
    assert where == "((int_attr = :int_attr) AND (float_attr < :float_attr))"
    assert binds == {"int_attr": 5, "float_attr": 6.0}


def test_spatial():
    where = to_sql_where(
        parse("INTERSECTS(point_attr, ENVELOPE (0 1 0 1))"),
        FIELD_MAPPING,
        FUNCTION_MAP,
    )
    geo_json = (
        "{\"type\": \"Polygon\", "
        "\"coordinates\": [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]}"
    )
    assert where == (
        "SDO_RELATE(geometry_attr, "
        f"SDO_UTIL.FROM_JSON(geometry => '{geo_json}', srid => 4326), "
        "'mask=ANYINTERACT') = 'TRUE'"
    )


def test_spatial_with_binds():
    where, binds = to_sql_where_with_binds(
        parse("INTERSECTS(point_attr, ENVELOPE (0 1 0 1))"),
        FIELD_MAPPING,
        FUNCTION_MAP,
    )
    geo_json = (
        "{\"type\": \"Polygon\", "
        "\"coordinates\": [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]}"
    )
    assert where == (
        "SDO_RELATE(geometry_attr, "
        "SDO_UTIL.FROM_JSON(geometry => :geo_json, srid => :srid), "
        "'mask=ANYINTERACT') = 'TRUE'"
    )
    assert binds == {"geo_json": geo_json, "srid": 4326}


def test_bbox():
    where = to_sql_where(
        parse("BBOX(point_attr,-140.99778,41.6751050889,-52.6480987209,83.23324)"),
        FIELD_MAPPING,
        FUNCTION_MAP,
    )
    geo_json = (
        "{\"type\": \"Polygon\", \"coordinates\": [["
        "[-140.99778, 41.6751050889], "
        "[-140.99778, 83.23324], "
        "[-52.6480987209, 83.23324], "
        "[-52.6480987209, 41.6751050889], "
        "[-140.99778, 41.6751050889]]]}"
    )
    assert where == (
        "SDO_RELATE(geometry_attr, "
        f"SDO_UTIL.FROM_JSON(geometry => '{geo_json}', srid => 4326), "
        "'mask=ANYINTERACT') = 'TRUE'"
    )


def test_bbox_with_binds():
    where, binds = to_sql_where_with_binds(
        parse("BBOX(point_attr,-140.99778,41.6751050889,-52.6480987209,83.23324)"),
        FIELD_MAPPING,
        FUNCTION_MAP,
    )
    geo_json = (
        "{\"type\": \"Polygon\", \"coordinates\": [["
        "[-140.99778, 41.6751050889], "
        "[-140.99778, 83.23324], "
        "[-52.6480987209, 83.23324], "
        "[-52.6480987209, 41.6751050889], "
        "[-140.99778, 41.6751050889]]]}"
    )
    assert where == (
        "SDO_RELATE(geometry_attr, "
        "SDO_UTIL.FROM_JSON(geometry => :geo_json, srid => :srid), "
        "'mask=ANYINTERACT') = 'TRUE'"
    )
    assert binds == {"geo_json": geo_json, "srid": 4326}
