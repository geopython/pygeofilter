import pytest

from pygeofilter.backends.oraclesql import (
    to_sql_where,
    to_sql_where_with_binds,
)
from pygeofilter.parsers.ecql import parse

FIELD_MAPPING = {
    "str_attr": "str_attr",
    "maybe_str_attr": "maybe_str_attr",
    "int_attr": "int_attr",
    "float_attr": "float_attr",
    "date_attr": "date_attr",
    "datetime_attr": "datetime_attr",
    "point_attr": "geometry_attr",
}

FUNCTION_MAP = {}


def test_between():
    where = to_sql_where(
        parse("int_attr NOT BETWEEN 4 AND 6"), FIELD_MAPPING, FUNCTION_MAP
    )
    assert where == "(int_attr NOT BETWEEN 4 AND 6)"


def test_between_with_binds():
    where, binds = to_sql_where_with_binds(
        parse("int_attr NOT BETWEEN 4 AND 6"), FIELD_MAPPING, FUNCTION_MAP
    )
    assert where == "(int_attr NOT BETWEEN :int_attr_low AND :int_attr_high)"
    assert binds == {"int_attr_low": 4, "int_attr_high": 6}


def test_like():
    where = to_sql_where(
        parse("str_attr LIKE 'foo%'"), FIELD_MAPPING, FUNCTION_MAP
    )
    assert where == "str_attr LIKE 'foo%' ESCAPE '\\'"


def test_like_with_binds():
    where, binds = to_sql_where_with_binds(
        parse("str_attr LIKE 'foo%'"), FIELD_MAPPING, FUNCTION_MAP
    )
    assert where == "str_attr LIKE :str_attr ESCAPE '\\'"
    assert binds == {"str_attr": "foo%"}


def test_combination():
    where = to_sql_where(
        parse("int_attr = 5 AND float_attr < 6.0"), FIELD_MAPPING, FUNCTION_MAP
    )
    assert where == "((int_attr = 5) AND (float_attr < 6.0))"


def test_combination_with_binds():
    where, binds = to_sql_where_with_binds(
        parse("int_attr = 5 AND float_attr < 6.0"), FIELD_MAPPING, FUNCTION_MAP
    )
    assert where == "((int_attr = :int_attr) AND (float_attr < :float_attr))"
    assert binds == {"int_attr": 5, "float_attr": 6.0}


def test_spatial():
    where = to_sql_where(
        parse("INTERSECTS(point_attr, ENVELOPE (0 1 0 1))"),
        FIELD_MAPPING,
        FUNCTION_MAP,
    )
    wkb = "01030000000100000005000000000000000000F03F0000000000000000000000000000"
    wkb += "F03F000000000000F03F0000000000000000000000000000F03F000000000000000000"
    wkb += "00000000000000000000000000F03F0000000000000000"
    assert (
        where
        == f"SDO_RELATE(geometry_attr, SDO_UTIL.FROM_WKBGEOMETRY('{wkb}'), 'mask=ANYINTERACT') = 'TRUE'"
    )


def test_spatial_with_binds():
    where, binds = to_sql_where_with_binds(
        parse("INTERSECTS(point_attr, ENVELOPE (0 1 0 1))"),
        FIELD_MAPPING,
        FUNCTION_MAP,
    )
    wkb = "01030000000100000005000000000000000000F03F0000000000000000000000000000"
    wkb += "F03F000000000000F03F0000000000000000000000000000F03F000000000000000000"
    wkb += "00000000000000000000000000F03F0000000000000000"
    assert (
        where
        == "SDO_RELATE(geometry_attr, SDO_UTIL.FROM_WKBGEOMETRY(:wkb), 'mask=ANYINTERACT') = 'TRUE'"
    )
    assert binds == {"wkb": wkb}
