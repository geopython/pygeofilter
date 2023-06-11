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

from django.test import TransactionTestCase

from pygeofilter.backends.django.evaluate import to_filter
from pygeofilter.frontends.ecql import parse

from . import models


class CQLTestCase(TransactionTestCase):
    fixtures = ["test.json"]

    def evaluate(self, cql_expr, expected_ids, model_type=None):
        model_type = model_type or models.Record
        mapping = models.FIELD_MAPPING
        mapping_choices = models.MAPPING_CHOICES

        ast = parse(cql_expr)
        filters = to_filter(ast, mapping, mapping_choices)

        qs = model_type.objects.filter(filters)

        self.assertEqual(
            expected_ids, type(expected_ids)(qs.values_list("identifier", flat=True))
        )

    # common comparisons

    def test_id_eq(self):
        self.evaluate("identifier = 'A'", ("A",))

    def test_id_ne(self):
        self.evaluate("identifier <> 'B'", ("A",))

    def test_float_lt(self):
        self.evaluate("floatAttribute < 30", ("A",))

    def test_float_le(self):
        self.evaluate("floatAttribute <= 20", ("A",))

    def test_float_gt(self):
        self.evaluate("floatAttribute > 20", ("B",))

    def test_float_ge(self):
        self.evaluate("floatAttribute >= 30", ("B",))

    def test_float_between(self):
        self.evaluate("floatAttribute BETWEEN -1 AND 1", ("A",))

    # test different field types

    def test_common_value_eq(self):
        self.evaluate("strAttribute = 'AAA'", ("A",))

    def test_common_value_in(self):
        self.evaluate("strAttribute IN ('AAA', 'XXX')", ("A",))

    def test_common_value_like(self):
        self.evaluate("strAttribute LIKE 'AA%'", ("A",))

    def test_common_value_like_middle(self):
        self.evaluate("strAttribute LIKE 'A%A'", ("A",))

    # TODO: resolve from choice?
    # def test_enum_value_eq(self):
    #     self.evaluate(
    #         'choiceAttribute = "A"',
    #         ('A',)
    #     )

    # def test_enum_value_in(self):
    #     self.evaluate(
    #         'choiceAttribute IN ("ASCENDING")',
    #         ('A',)
    #     )

    # def test_enum_value_like(self):
    #     self.evaluate(
    #         'choiceAttribute LIKE "ASCEN%"',
    #         ('A',)
    #     )

    # def test_enum_value_ilike(self):
    #     self.evaluate(
    #         'choiceAttribute ILIKE "ascen%"',
    #         ('A',)
    #     )

    # def test_enum_value_ilike_start_middle_end(self):
    #     self.evaluate(
    #         r'choiceAttribute ILIKE "a%en%ing"',
    #         ('A',)
    #     )

    # (NOT) LIKE | ILIKE

    def test_like_beginswith(self):
        self.evaluate("strMetaAttribute LIKE 'A%'", ("A",))

    def test_ilike_beginswith(self):
        self.evaluate("strMetaAttribute ILIKE 'a%'", ("A",))

    def test_like_endswith(self):
        self.evaluate("strMetaAttribute LIKE '%A'", ("A",))

    def test_ilike_endswith(self):
        self.evaluate("strMetaAttribute ILIKE '%a'", ("A",))

    def test_like_middle(self):
        self.evaluate("strMetaAttribute LIKE '%parent%'", ("A", "B"))

    def test_like_startswith_middle(self):
        self.evaluate("strMetaAttribute LIKE 'A%rent%'", ("A",))

    def test_like_middle_endswith(self):
        self.evaluate("strMetaAttribute LIKE '%ren%A'", ("A",))

    def test_like_startswith_middle_endswith(self):
        self.evaluate("strMetaAttribute LIKE 'A%ren%A'", ("A",))

    def test_ilike_middle(self):
        self.evaluate("strMetaAttribute ILIKE '%PaReNT%'", ("A", "B"))

    def test_not_like_beginswith(self):
        self.evaluate("strMetaAttribute NOT LIKE 'B%'", ("A",))

    def test_not_ilike_beginswith(self):
        self.evaluate("strMetaAttribute NOT ILIKE 'b%'", ("A",))

    def test_not_like_endswith(self):
        self.evaluate("strMetaAttribute NOT LIKE '%B'", ("A",))

    def test_not_ilike_endswith(self):
        self.evaluate("strMetaAttribute NOT ILIKE '%b'", ("A",))

    # (NOT) IN

    def test_string_in(self):
        self.evaluate("identifier IN ('A', 'B')", ("A", "B"))

    def test_string_not_in(self):
        self.evaluate("identifier NOT IN ('B', 'C')", ("A",))

    # (NOT) NULL

    def test_string_null(self):
        self.evaluate("intAttribute IS NULL", ("B",))

    def test_string_not_null(self):
        self.evaluate("intAttribute IS NOT NULL", ("A",))

    # temporal predicates

    def test_before(self):
        self.evaluate("datetimeAttribute BEFORE 2000-01-01T00:00:01Z", ("A",))

    def test_before_or_during_dt_dt(self):
        self.evaluate(
            "datetimeAttribute BEFORE OR DURING "
            "2000-01-01T00:00:00Z / 2000-01-01T00:00:01Z",
            ("A",),
        )

    def test_before_or_during_dt_td(self):
        self.evaluate(
            "datetimeAttribute BEFORE OR DURING " "2000-01-01T00:00:00Z / PT4S", ("A",)
        )

    def test_before_or_during_td_dt(self):
        self.evaluate(
            "datetimeAttribute BEFORE OR DURING " "PT4S / 2000-01-01T00:00:03Z", ("A",)
        )

    def test_during_td_dt(self):
        self.evaluate(
            "datetimeAttribute BEFORE OR DURING " "PT4S / 2000-01-01T00:00:03Z", ("A",)
        )

    # TODO: test DURING OR AFTER / AFTER

    # spatial predicates

    def test_intersects_point(self):
        self.evaluate("INTERSECTS(geometry, POINT(1 1.0))", ("A",))

    def test_intersects_mulitipoint_1(self):
        self.evaluate("INTERSECTS(geometry, MULTIPOINT(0 0, 1 1))", ("A",))

    def test_intersects_mulitipoint_2(self):
        self.evaluate("INTERSECTS(geometry, MULTIPOINT((0 0), (1 1)))", ("A",))

    def test_intersects_linestring(self):
        self.evaluate("INTERSECTS(geometry, LINESTRING(0 0, 1 1))", ("A",))

    def test_intersects_multilinestring(self):
        self.evaluate(
            "INTERSECTS(geometry, MULTILINESTRING((0 0, 1 1), (2 1, 1 2)))", ("A",)
        )

    def test_intersects_polygon(self):
        self.evaluate(
            "INTERSECTS(geometry, "
            "POLYGON((0 0, 3 0, 3 3, 0 3, 0 0), (1 1, 2 1, 2 2, 1 2, 1 1)))",
            ("A",),
        )

    def test_intersects_multipolygon(self):
        self.evaluate(
            "INTERSECTS(geometry, "
            "MULTIPOLYGON(((0 0, 3 0, 3 3, 0 3, 0 0), "
            "(1 1, 2 1, 2 2, 1 2, 1 1))))",
            ("A",),
        )

    def test_intersects_envelope(self):
        self.evaluate("INTERSECTS(geometry, ENVELOPE(0 1.0 0 1.0))", ("A",))

    def test_dwithin(self):
        self.evaluate("DWITHIN(geometry, POINT(0 0), 10, meters)", ("A",))

    def test_beyond(self):
        self.evaluate("BEYOND(geometry, POINT(0 0), 10, meters)", ("B",))

    def test_bbox(self):
        self.evaluate("BBOX(geometry, 0, 0, 1, 1, 'EPSG:4326')", ("A",))

    # TODO: other relation methods

    # arithmethic expressions

    def test_arith_simple_plus(self):
        self.evaluate("intMetaAttribute = 10 + 10", ("A",))

    def test_arith_field_plus_1(self):
        self.evaluate("intMetaAttribute = floatMetaAttribute + 10", ("A", "B"))

    def test_arith_field_plus_2(self):
        self.evaluate("intMetaAttribute = 10 + floatMetaAttribute", ("A", "B"))

    def test_arith_field_plus_field(self):
        self.evaluate("intMetaAttribute = " "floatMetaAttribute + intAttribute", ("A",))

    def test_arith_field_plus_mul_1(self):
        self.evaluate("intMetaAttribute = intAttribute * 1.5 + 5", ("A",))

    def test_arith_field_plus_mul_2(self):
        self.evaluate("intMetaAttribute = 5 + intAttribute * 1.5", ("A",))
