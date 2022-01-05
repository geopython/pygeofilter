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

from pygeofilter.backends.sql import to_sql_where
from pygeofilter.parsers.ecql import parse

from osgeo import ogr
import pytest


ogr.UseExceptions()


@pytest.fixture
def data():
    driver = ogr.GetDriverByName('MEMORY')
    source = driver.CreateDataSource('data')

    layer = source.CreateLayer("layer")
    id_attr = ogr.FieldDefn("id", ogr.OFTInteger)
    layer.CreateField(id_attr)
    str_attr = ogr.FieldDefn("str_attr", ogr.OFTString)
    layer.CreateField(str_attr)
    maybe_str_attr = ogr.FieldDefn("maybe_str_attr", ogr.OFTString)
    layer.CreateField(maybe_str_attr)
    int_attr = ogr.FieldDefn("int_attr", ogr.OFTInteger)
    layer.CreateField(int_attr)
    float_attr = ogr.FieldDefn("float_attr", ogr.OFTReal)
    layer.CreateField(float_attr)
    date_attr = ogr.FieldDefn("date_attr", ogr.OFTDate)
    layer.CreateField(date_attr)
    datetime_attr = ogr.FieldDefn("datetime_attr", ogr.OFTDateTime)
    layer.CreateField(datetime_attr)

    feature_def = layer.GetLayerDefn()
    feature = ogr.Feature(feature_def)
    feature.SetGeometry(ogr.CreateGeometryFromWkt("POINT (1 1)"))
    feature.SetField("id", 0)
    feature.SetField("str_attr", "this is a test")
    feature.SetField("maybe_str_attr", None)
    feature.SetField("int_attr", 5)
    feature.SetField("float_attr", 5.5)
    feature.SetField("date_attr", "2010-01-01")
    feature.SetField("datetime_attr", "2010-01-01T00:00:00Z")
    layer.CreateFeature(feature)
    feature = None

    feature_def = layer.GetLayerDefn()
    feature = ogr.Feature(feature_def)
    feature.SetGeometry(ogr.CreateGeometryFromWkt("POINT (2 2)"))
    feature.SetField("id", 1)
    feature.SetField("str_attr", "this is another test")
    feature.SetField("maybe_str_attr", 'not null')
    feature.SetField("int_attr", 8)
    feature.SetField("float_attr", 8.5)
    feature.SetField("date_attr", "2010-01-10")
    feature.SetField("datetime_attr", "2010-10-01T00:00:00Z")
    layer.CreateFeature(feature)
    feature = None

    return source


FIELD_MAPPING = {
    'str_attr': 'str_attr',
    'maybe_str_attr': 'maybe_str_attr',
    'int_attr': 'int_attr',
    'float_attr': 'float_attr',
    'date_attr': 'date_attr',
    'datetime_attr': 'datetime_attr',
    'point_attr': 'GEOMETRY',
}

FUNCTION_MAP = {
    'sin': 'sin'
}


def filter_(ast, data):
    where = to_sql_where(ast, FIELD_MAPPING, FUNCTION_MAP)
    return data.ExecuteSQL(f"""
        SELECT id, str_attr, maybe_str_attr, int_attr, float_attr,
               date_attr, datetime_attr, GEOMETRY
        FROM layer
        WHERE {where}
    """, None, "SQLite")


def test_comparison(data):
    result = filter_(parse('int_attr = 5'), data)
    assert result.GetFeatureCount() == 1 and \
        result.GetFeature(0).GetField(0) == 0

    result = filter_(parse('int_attr < 6'), data)
    assert result.GetFeatureCount() == 1 and \
        result.GetFeature(0).GetField(0) == 0

    result = filter_(parse('int_attr > 6'), data)
    assert result.GetFeatureCount() == 1 and \
        result.GetFeature(0).GetField(0) == 1

    result = filter_(parse('int_attr <= 5'), data)
    assert result.GetFeatureCount() == 1 and \
        result.GetFeature(0).GetField(0) == 0

    result = filter_(parse('int_attr >= 8'), data)
    assert result.GetFeatureCount() == 1 and \
        result.GetFeature(0).GetField(0) == 1

    result = filter_(parse('int_attr <> 5'), data)
    assert result.GetFeatureCount() == 1 and \
        result.GetFeature(0).GetField(0) == 1


def test_combination(data):
    result = filter_(parse('int_attr = 5 AND float_attr < 6.0'), data)
    assert result.GetFeatureCount() == 1 and \
        result.GetFeature(0).GetField(0) == 0

    result = filter_(parse('int_attr = 5 AND float_attr < 6.0'), data)
    assert result.GetFeatureCount() == 1 and \
        result.GetFeature(0).GetField(0) == 0


def test_between(data):
    result = filter_(parse('float_attr BETWEEN 4 AND 6'), data)
    assert result.GetFeatureCount() == 1 and \
        result.GetFeature(0).GetField(0) == 0

    result = filter_(parse('int_attr NOT BETWEEN 4 AND 6'), data)
    assert result.GetFeatureCount() == 1 and \
        result.GetFeature(0).GetField(0) == 1


def test_like(data):
    result = filter_(parse('str_attr LIKE \'this is . test\''), data)
    assert result.GetFeatureCount() == 1 and \
        result.GetFeature(0).GetField(0) == 0

    result = filter_(parse('str_attr LIKE \'this is % test\''), data)
    assert result.GetFeatureCount() == 2

    result = filter_(parse('str_attr NOT LIKE \'% another test\''), data)
    assert result.GetFeatureCount() == 1 and \
        result.GetFeature(0).GetField(0) == 0

    result = filter_(parse('str_attr NOT LIKE \'this is . test\''), data)
    assert result.GetFeatureCount() == 1 and \
        result.GetFeature(0).GetField(0) == 1

    result = filter_(parse('str_attr ILIKE \'THIS IS . TEST\''), data)
    assert result.GetFeatureCount() == 1 and \
        result.GetFeature(0).GetField(0) == 0

    result = filter_(parse('str_attr ILIKE \'THIS IS % TEST\''), data)
    assert result.GetFeatureCount() == 2


def test_in(data):
    result = filter_(parse('int_attr IN ( 1, 2, 3, 4, 5 )'), data)
    assert result.GetFeatureCount() == 1 and \
        result.GetFeature(0).GetField(0) == 0

    result = filter_(parse('int_attr NOT IN ( 1, 2, 3, 4, 5 )'), data)
    assert result.GetFeatureCount() == 1 and \
        result.GetFeature(0).GetField(0) == 1


def test_null(data):
    result = filter_(parse('maybe_str_attr IS NULL'), data)
    assert result.GetFeatureCount() == 1 and \
        result.GetFeature(0).GetField(0) == 0

    result = filter_(parse('maybe_str_attr IS NOT NULL'), data)
    assert result.GetFeatureCount() == 1 and \
        result.GetFeature(0).GetField(0) == 1

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
        parse('INTERSECTS(point_attr, ENVELOPE (0 1 0 1))'),
        data,
    )
    assert result.GetFeatureCount() == 1 and \
        result.GetFeature(0).GetField(0) == 0

    result = filter_(
        parse('EQUALS(point_attr, POINT(2 2))'),
        data,
    )
    assert result.GetFeatureCount() == 1 and \
        result.GetFeature(0).GetField(0) == 1


def test_arithmetic(data):
    result = filter_(
        parse('int_attr = float_attr - 0.5'),
        data,
    )
    assert result.GetFeatureCount() == 2

    result = filter_(
        parse('int_attr = 5 + 20 / 2 - 10'),
        data,
    )
    assert result.GetFeatureCount() == 1 and \
        result.GetFeature(0).GetField(0) == 0


def test_function(data):
    result = filter_(
        parse('sin(float_attr) BETWEEN -0.75 AND -0.70'),
        data,
    )
    assert result.GetFeatureCount() == 1 and \
        result.GetFeature(0).GetField(0) == 0
