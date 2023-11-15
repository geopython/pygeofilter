# ------------------------------------------------------------------------------
#
# Project: pygeofilter <https://github.com/geopython/pygeofilter>
# Authors: Jonas Kiefer <jonas.kiefer@live.com>
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

import pytest
from testapp import models

from pygeofilter.backends.django.evaluate import to_filter
from pygeofilter.parsers.fes.parser import parse


def evaluate(fes_expr, expected_ids, model_type=None):
    model_type = model_type or models.Record
    mapping = models.FIELD_MAPPING
    mapping_choices = models.MAPPING_CHOICES

    ast = parse(fes_expr)
    filters = to_filter(ast, mapping, mapping_choices)

    qs = model_type.objects.filter(filters)

    assert expected_ids == type(expected_ids)(qs.values_list("identifier", flat=True))


FILTER_FRAME = """
<ogc:Filter xmlns:ogc="http://www.opengis.net/ogc">
  {0}
</ogc:Filter>
"""


# common comparisons

@pytest.mark.django_db
def test_common_value_like():
    CONSTRAINT = '''
    <ogc:PropertyIsLike wildCard="*" singleChar="_" escapeChar="/">
    <ogc:PropertyName>strAttribute</ogc:PropertyName>
    <ogc:Literal>AA*</ogc:Literal>
    </ogc:PropertyIsLike>
    '''

    evaluate(FILTER_FRAME.format(CONSTRAINT), ("A",))


@pytest.mark.django_db
def test_common_value_like_middle():
    CONSTRAINT = '''
    <ogc:PropertyIsLike wildCard="*" singleChar="_" escapeChar="/">
    <ogc:PropertyName>strAttribute</ogc:PropertyName>
    <ogc:Literal>A*A</ogc:Literal>
    </ogc:PropertyIsLike>
    '''

    evaluate(FILTER_FRAME.format(CONSTRAINT), ("A",))


@pytest.mark.django_db
def test_like_beginswith():
    CONSTRAINT = '''
    <ogc:PropertyIsLike wildCard="*" singleChar="_" escapeChar="/">
    <ogc:PropertyName>strAttribute</ogc:PropertyName>
    <ogc:Literal>A*</ogc:Literal>
    </ogc:PropertyIsLike>
    '''

    evaluate(FILTER_FRAME.format(CONSTRAINT), ("A",))


@pytest.mark.django_db
def test_like_endswith():
    CONSTRAINT = '''
    <ogc:PropertyIsLike wildCard="*" singleChar="_" escapeChar="/">
    <ogc:PropertyName>strAttribute</ogc:PropertyName>
    <ogc:Literal>*a</ogc:Literal>
    </ogc:PropertyIsLike>
    '''

    evaluate(FILTER_FRAME.format(CONSTRAINT), ("A",))


@pytest.mark.django_db
def test_like_middle():
    CONSTRAINT = '''
    <ogc:PropertyIsLike wildCard="*" singleChar="_" escapeChar="/">
    <ogc:PropertyName>strMetaAttribute</ogc:PropertyName>
    <ogc:Literal>*parent*</ogc:Literal>
    </ogc:PropertyIsLike>
    '''

    evaluate(FILTER_FRAME.format(CONSTRAINT), ("A", "B"))


@pytest.mark.django_db
def test_like_startswith_middle():
    CONSTRAINT = '''
    <ogc:PropertyIsLike wildCard="*" singleChar="_" escapeChar="/">
    <ogc:PropertyName>strMetaAttribute</ogc:PropertyName>
    <ogc:Literal>A*rent*</ogc:Literal>
    </ogc:PropertyIsLike>
    '''

    evaluate(FILTER_FRAME.format(CONSTRAINT), ("A",))


@pytest.mark.django_db
def test_like_startswith_middle_endswith():
    CONSTRAINT = '''
    <ogc:PropertyIsLike wildCard="*" singleChar="_" escapeChar="/">
    <ogc:PropertyName>strMetaAttribute</ogc:PropertyName>
    <ogc:Literal>A%ren%A</ogc:Literal>
    </ogc:PropertyIsLike>
    '''

    evaluate(FILTER_FRAME.format(CONSTRAINT), ("A",))


@pytest.mark.django_db
def test_not_like_beginswith():
    CONSTRAINT = '''
    <ogc:Not>
    <ogc:PropertyIsLike wildCard="*" singleChar="_" escapeChar="/">
    <ogc:PropertyName>strMetaAttribute</ogc:PropertyName>
    <ogc:Literal>B%</ogc:Literal>
    </ogc:PropertyIsLike>
    </ogc:Not>
    '''

    evaluate(FILTER_FRAME.format(CONSTRAINT), ("A",))


@pytest.mark.django_db
def test_not_like_endswith():
    CONSTRAINT = '''
    <ogc:Not>
    <ogc:PropertyIsLike wildCard="*" singleChar="_" escapeChar="/">
    <ogc:PropertyName>strMetaAttribute</ogc:PropertyName>
    <ogc:Literal>%B</ogc:Literal>
    </ogc:PropertyIsLike>
    </ogc:Not>
    '''

    evaluate(FILTER_FRAME.format(CONSTRAINT), ("A",))


# spatial predicates

@pytest.mark.django_db
def test_intersects_point():
    CONSTRAINT = '''
    <ogc:Intersects>
        <ogc:PropertyName>geometry</ogc:PropertyName>
        <gml:Point gml:id="ID"
                srsName="http://www.opengis.net/def/crs/epsg/0/4326"
                xmlns:gml="http://www.opengis.net/gml">
            <gml:pos>1.0 1.0</gml:pos>
        </gml:Point>

    </ogc:Intersects>
    '''

    evaluate(FILTER_FRAME.format(CONSTRAINT), ("A",))


@pytest.mark.django_db
def test_intersects_mulitipoint_1():
    CONSTRAINT = '''
    <ogc:Intersects>
        <ogc:PropertyName>geometry</ogc:PropertyName>
        <gml:MultiPoint gml:id="ID">
           <gml:pointMember>
                <gml:Point gml:id="ID"
                        srsName="http://www.opengis.net/def/crs/epsg/0/4326"
                        xmlns:gml="http://www.opengis.net/gml">
                    <gml:pos>1.0 1.0</gml:pos>
                </gml:Point>
            </gml:pointMember>
        </gml:MultiPoint>
    </ogc:Intersects>
    '''

    evaluate(FILTER_FRAME.format(CONSTRAINT), ("A",))
