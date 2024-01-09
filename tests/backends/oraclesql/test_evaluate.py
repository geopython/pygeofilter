# ------------------------------------------------------------------------------
#
# Project: pygeofilter <https://github.com/geopython/pygeofilter>
# Authors: Andreas Kosubek <andreas.kosubek@ama.gv.at>
#          Bernhard Mallinger <bernhard.mallinger@eox.at>
# ------------------------------------------------------------------------------
# Copyright (C) 2023 Agrar Markt Austria
# Copyright (C) 2024 EOX IT Services GmbH
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


from pygeofilter.backends.oraclesql import (
    to_sql_where,
    to_sql_where_with_bind_variables,
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
    where, binds = to_sql_where_with_bind_variables(
        parse("int_attr NOT BETWEEN 4 AND 6"),
        FIELD_MAPPING,
        FUNCTION_MAP
    )
    assert where == "(int_attr NOT BETWEEN :int_attr_low_0 AND :int_attr_high_0)"
    assert binds == {"int_attr_low_0": 4, "int_attr_high_0": 6}


def test_like():
    where = to_sql_where(
        parse("str_attr LIKE 'foo%'"),
        FIELD_MAPPING,
        FUNCTION_MAP
    )
    assert where == "str_attr LIKE 'foo%' ESCAPE '\\'"


def test_like_with_binds():
    where, binds = to_sql_where_with_bind_variables(
        parse("str_attr LIKE 'foo%'"),
        FIELD_MAPPING,
        FUNCTION_MAP
    )
    assert where == "str_attr LIKE :str_attr_0 ESCAPE '\\'"
    assert binds == {"str_attr_0": "foo%"}


def test_combination():
    where = to_sql_where(
        parse("int_attr = 5 AND float_attr < 6.0"),
        FIELD_MAPPING,
        FUNCTION_MAP
    )
    assert where == "((int_attr = 5) AND (float_attr < 6.0))"


def test_combination_with_binds():
    where, binds = to_sql_where_with_bind_variables(
        parse("int_attr = 5 AND float_attr < 6.0"),
        FIELD_MAPPING,
        FUNCTION_MAP
    )
    assert where == "((int_attr = :int_attr_0) AND (float_attr < :float_attr_1))"
    assert binds == {"int_attr_0": 5, "float_attr_1": 6.0}


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
    where, binds = to_sql_where_with_bind_variables(
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
        "SDO_UTIL.FROM_JSON(geometry => :geo_json_0, srid => :srid_0), "
        "'mask=ANYINTERACT') = 'TRUE'"
    )
    assert binds == {"geo_json_0": geo_json, "srid_0": 4326}


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
    where, binds = to_sql_where_with_bind_variables(
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
        "SDO_UTIL.FROM_JSON(geometry => :geo_json_0, srid => :srid_0), "
        "'mask=ANYINTERACT') = 'TRUE'"
    )
    assert binds == {"geo_json_0": geo_json, "srid_0": 4326}
