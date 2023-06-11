# ------------------------------------------------------------------------------
#
# Project: pygeofilter <https://github.com/geopython/pygeofilter>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
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
from pygeofilter.frontends.ecql import parse


def evaluate(cql_expr, expected_ids, model_type=None):
    model_type = model_type or models.Record
    mapping = models.FIELD_MAPPING
    mapping_choices = models.MAPPING_CHOICES

    ast = parse(cql_expr)
    filters = to_filter(ast, mapping, mapping_choices)

    qs = model_type.objects.filter(filters)

    assert expected_ids == type(expected_ids)(qs.values_list("identifier", flat=True))


# common comparisons


@pytest.mark.django_db
def test_id_eq():
    evaluate("identifier = 'A'", ("A",))


@pytest.mark.django_db
def test_id_eq_2():
    evaluate("'A' = identifier", ("A",))


@pytest.mark.django_db
def test_id_ne():
    evaluate("identifier <> 'B'", ("A",))


@pytest.mark.django_db
def test_float_lt():
    evaluate("floatAttribute < 30", ("A",))


@pytest.mark.django_db
def test_float_le():
    evaluate("floatAttribute <= 20", ("A",))


@pytest.mark.django_db
def test_float_le_inv():
    evaluate("20 >= floatAttribute", ("A",))


@pytest.mark.django_db
def test_float_gt():
    evaluate("floatAttribute > 20", ("B",))


@pytest.mark.django_db
def test_float_gt_2():
    evaluate("20 < floatAttribute", ("B",))


@pytest.mark.django_db
def test_float_ge():
    evaluate("floatAttribute >= 30", ("B",))


@pytest.mark.django_db
def test_float_ge_inv():
    evaluate("30 <= floatAttribute", ("B",))


@pytest.mark.django_db
def test_float_between():
    evaluate("floatAttribute BETWEEN -1 AND 1", ("A",))


# test different field types


@pytest.mark.django_db
def test_common_value_eq():
    evaluate("strAttribute = 'AAA'", ("A",))


@pytest.mark.django_db
def test_common_value_eq_inv():
    evaluate("'AAA' = strAttribute", ("A",))


@pytest.mark.django_db
def test_common_value_in():
    evaluate("strAttribute IN ('AAA', 'XXX')", ("A",))


@pytest.mark.django_db
def test_common_value_like():
    evaluate("strAttribute LIKE 'AA%'", ("A",))


@pytest.mark.django_db
def test_common_value_like_middle():
    evaluate("strAttribute LIKE 'A%A'", ("A",))


# TODO: resolve from choice?
# def test_enum_value_eq():
#     evaluate(
#         'choiceAttribute = "A"',
#         ('A',)
#     )

# def test_enum_value_in():
#     evaluate(
#         'choiceAttribute IN ("ASCENDING")',
#         ('A',)
#     )

# def test_enum_value_like():
#     evaluate(
#         'choiceAttribute LIKE "ASCEN%"',
#         ('A',)
#     )

# def test_enum_value_ilike():
#     evaluate(
#         'choiceAttribute ILIKE "ascen%"',
#         ('A',)
#     )

# def test_enum_value_ilike_start_middle_end():
#     evaluate(
#         r'choiceAttribute ILIKE "a%en%ing"',
#         ('A',)
#     )

# (NOT) LIKE | ILIKE


@pytest.mark.django_db
def test_like_beginswith():
    evaluate("strMetaAttribute LIKE 'A%'", ("A",))


@pytest.mark.django_db
def test_ilike_beginswith():
    evaluate("strMetaAttribute ILIKE 'a%'", ("A",))


@pytest.mark.django_db
def test_like_endswith():
    evaluate("strMetaAttribute LIKE '%A'", ("A",))


@pytest.mark.django_db
def test_ilike_endswith():
    evaluate("strMetaAttribute ILIKE '%a'", ("A",))


@pytest.mark.django_db
def test_like_middle():
    evaluate("strMetaAttribute LIKE '%parent%'", ("A", "B"))


@pytest.mark.django_db
def test_like_startswith_middle():
    evaluate("strMetaAttribute LIKE 'A%rent%'", ("A",))


@pytest.mark.django_db
def test_like_middle_endswith():
    evaluate("strMetaAttribute LIKE '%ren%A'", ("A",))


@pytest.mark.django_db
def test_like_startswith_middle_endswith():
    evaluate("strMetaAttribute LIKE 'A%ren%A'", ("A",))


@pytest.mark.django_db
def test_ilike_middle():
    evaluate("strMetaAttribute ILIKE '%PaReNT%'", ("A", "B"))


@pytest.mark.django_db
def test_not_like_beginswith():
    evaluate("strMetaAttribute NOT LIKE 'B%'", ("A",))


@pytest.mark.django_db
def test_not_ilike_beginswith():
    evaluate("strMetaAttribute NOT ILIKE 'b%'", ("A",))


@pytest.mark.django_db
def test_not_like_endswith():
    evaluate("strMetaAttribute NOT LIKE '%B'", ("A",))


@pytest.mark.django_db
def test_not_ilike_endswith():
    evaluate("strMetaAttribute NOT ILIKE '%b'", ("A",))


# (NOT) IN


@pytest.mark.django_db
def test_string_in():
    evaluate("identifier IN ('A', 'B')", ("A", "B"))


@pytest.mark.django_db
def test_string_not_in():
    evaluate("identifier NOT IN ('B', 'C')", ("A",))


# (NOT) NULL


@pytest.mark.django_db
def test_string_null():
    evaluate("intAttribute IS NULL", ("B",))


@pytest.mark.django_db
def test_string_not_null():
    evaluate("intAttribute IS NOT NULL", ("A",))


# temporal predicates


@pytest.mark.django_db
def test_before():
    evaluate("datetimeAttribute BEFORE 2000-01-01T00:00:01Z", ("A",))


@pytest.mark.django_db
def test_before_or_during_dt_dt():
    evaluate(
        "datetimeAttribute BEFORE OR DURING "
        "2000-01-01T00:00:00Z / 2000-01-01T00:00:01Z",
        ("A",),
    )


@pytest.mark.django_db
def test_before_or_during_dt_td():
    evaluate(
        "datetimeAttribute BEFORE OR DURING " "2000-01-01T00:00:00Z / PT4S", ("A",)
    )


@pytest.mark.django_db
def test_before_or_during_td_dt():
    evaluate(
        "datetimeAttribute BEFORE OR DURING " "PT4S / 2000-01-01T00:00:03Z", ("A",)
    )


@pytest.mark.django_db
def test_during_td_dt():
    evaluate(
        "datetimeAttribute BEFORE OR DURING " "PT4S / 2000-01-01T00:00:03Z", ("A",)
    )


# TODO: test DURING OR AFTER / AFTER

# spatial predicates


@pytest.mark.django_db
def test_intersects_point():
    evaluate("INTERSECTS(geometry, POINT(1 1.0))", ("A",))


@pytest.mark.django_db
def test_intersects_point_inv():
    evaluate("INTERSECTS(POINT(1 1.0), geometry)", ("A",))


@pytest.mark.django_db
def test_intersects_mulitipoint_1():
    evaluate("INTERSECTS(geometry, MULTIPOINT(0 0, 1 1))", ("A",))


@pytest.mark.django_db
def test_intersects_mulitipoint_1_inv():
    evaluate("INTERSECTS(MULTIPOINT(0 0, 1 1), geometry)", ("A",))


@pytest.mark.django_db
def test_intersects_mulitipoint_2():
    evaluate("INTERSECTS(geometry, MULTIPOINT((0 0), (1 1)))", ("A",))


@pytest.mark.django_db
def test_intersects_mulitipoint_2_inv():
    evaluate("INTERSECTS(MULTIPOINT((0 0), (1 1)), geometry)", ("A",))


@pytest.mark.django_db
def test_intersects_linestring():
    evaluate("INTERSECTS(geometry, LINESTRING(0 0, 1 1))", ("A",))


@pytest.mark.django_db
def test_intersects_linestring__inv():
    evaluate("INTERSECTS(LINESTRING(0 0, 1 1), geometry)", ("A",))


@pytest.mark.django_db
def test_intersects_multilinestring():
    evaluate("INTERSECTS(geometry, MULTILINESTRING((0 0, 1 1), (2 1, 1 2)))", ("A",))


@pytest.mark.django_db
def test_intersects_multilinestring_inv():
    evaluate("INTERSECTS(MULTILINESTRING((0 0, 1 1), (2 1, 1 2)), geometry)", ("A",))


@pytest.mark.django_db
def test_intersects_polygon():
    evaluate(
        "INTERSECTS(geometry, "
        "POLYGON((0 0, 3 0, 3 3, 0 3, 0 0), (1 1, 2 1, 2 2, 1 2, 1 1)))",
        ("A",),
    )


@pytest.mark.django_db
def test_intersects_polygon_inv():
    evaluate(
        "INTERSECTS("
        "POLYGON((0 0, 3 0, 3 3, 0 3, 0 0), (1 1, 2 1, 2 2, 1 2, 1 1)), "
        "geometry)",
        ("A",),
    )


@pytest.mark.django_db
def test_intersects_multipolygon():
    evaluate(
        "INTERSECTS(geometry, "
        "MULTIPOLYGON(((0 0, 3 0, 3 3, 0 3, 0 0), "
        "(1 1, 2 1, 2 2, 1 2, 1 1))))",
        ("A",),
    )


@pytest.mark.django_db
def test_intersects_multipolygon_inv():
    evaluate(
        "INTERSECTS("
        "MULTIPOLYGON(((0 0, 3 0, 3 3, 0 3, 0 0), "
        "(1 1, 2 1, 2 2, 1 2, 1 1))), "
        "geometry)",
        ("A",),
    )


@pytest.mark.django_db
def test_intersects_envelope():
    evaluate("INTERSECTS(geometry, ENVELOPE(0 1.0 0 1.0))", ("A",))


@pytest.mark.django_db
def test_intersects_envelope_inv():
    evaluate("INTERSECTS(ENVELOPE(0 1.0 0 1.0), geometry)", ("A",))


@pytest.mark.django_db
def test_dwithin():
    evaluate("DWITHIN(geometry, POINT(0 0), 10, meters)", ("A",))


@pytest.mark.django_db
def test_dwithin_inv():
    evaluate("DWITHIN(POINT(0 0), geometry, 10, meters)", ("A",))


@pytest.mark.django_db
def test_beyond():
    evaluate("BEYOND(geometry, POINT(0 0), 10, meters)", ("B",))


@pytest.mark.django_db
def test_beyond_inv():
    evaluate("BEYOND(POINT(0 0), geometry, 10, meters)", ("B",))


@pytest.mark.django_db
def test_bbox():
    evaluate("BBOX(geometry, 0, 0, 1, 1, 'EPSG:4326')", ("A",))


# TODO: other relation methods

# arithmethic expressions


@pytest.mark.django_db
def test_arith_simple_plus():
    evaluate("intMetaAttribute = 10 + 10", ("A",))


@pytest.mark.django_db
def test_arith_simple_plus_inv():
    evaluate("10 + 10 = intMetaAttribute", ("A",))


@pytest.mark.django_db
def test_arith_field_plus_1():
    evaluate("intMetaAttribute = floatMetaAttribute + 10", ("A", "B"))


@pytest.mark.django_db
def test_arith_field_plus_1_inv():
    evaluate("floatMetaAttribute + 10 = intMetaAttribute", ("A", "B"))


@pytest.mark.django_db
def test_arith_field_plus_2():
    evaluate("intMetaAttribute = 10 + floatMetaAttribute", ("A", "B"))


@pytest.mark.django_db
def test_arith_field_plus_2_inv():
    evaluate("10 + floatMetaAttribute = intMetaAttribute", ("A", "B"))


@pytest.mark.django_db
def test_arith_field_plus_field():
    evaluate("intMetaAttribute = " "floatMetaAttribute + intAttribute", ("A",))


@pytest.mark.django_db
def test_arith_field_plus_field_inv():
    evaluate("floatMetaAttribute + intAttribute" "= intMetaAttribute", ("A",))


@pytest.mark.django_db
def test_arith_field_plus_mul_1():
    evaluate("intMetaAttribute = intAttribute * 1.5 + 5", ("A",))


@pytest.mark.django_db
def test_arith_field_plus_mul_2():
    evaluate("intMetaAttribute = 5 + intAttribute * 1.5", ("A",))
