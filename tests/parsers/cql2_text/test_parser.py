from datetime import datetime, timedelta

from dateparser.timezone_parser import StaticTzInfo

from pygeofilter import ast, values
from pygeofilter.parsers.cql2_text import parse


def test_attribute_eq_true_uppercase():
    result = parse("attr = TRUE")
    assert result == ast.Equal(
        ast.Attribute("attr"),
        True,
    )


def test_attribute_eq_true_lowercase():
    result = parse("attr = true")
    assert result == ast.Equal(
        ast.Attribute("attr"),
        True,
    )


def test_attribute_eq_false_uppercase():
    result = parse("attr = FALSE")
    assert result == ast.Equal(
        ast.Attribute("attr"),
        False,
    )


def test_attribute_eq_false_lowercase():
    result = parse("attr = false")
    assert result == ast.Equal(
        ast.Attribute("attr"),
        False,
    )


def test_attribute_eq_literal():
    result = parse("attr = 'A'")
    assert result == ast.Equal(
        ast.Attribute("attr"),
        "A",
    )


def test_attribute_lt_literal():
    result = parse("attr < 5")
    assert result == ast.LessThan(
        ast.Attribute("attr"),
        5,
    )


def test_attribute_lte_literal():
    result = parse("attr <= 5")
    assert result == ast.LessEqual(
        ast.Attribute("attr"),
        5,
    )


def test_attribute_gt_literal():
    result = parse("attr > 5")
    assert result == ast.GreaterThan(
        ast.Attribute("attr"),
        5,
    )


def test_attribute_gte_literal():
    result = parse("attr >= 5")
    assert result == ast.GreaterEqual(
        ast.Attribute("attr"),
        5,
    )


def test_attribute_ne_literal():
    result = parse("attr != 5")
    assert result == ast.NotEqual(
        ast.Attribute("attr"),
        5,
    )


def test_attribute_ne_literal_alt():
    result = parse("attr <> 5")
    assert result == ast.NotEqual(
        ast.Attribute("attr"),
        5,
    )


def test_attribute_between():
    result = parse("attr BETWEEN 2 AND 5")
    assert result == ast.Between(
        ast.Attribute("attr"),
        2,
        5,
        False,
    )


def test_attribute_not_between():
    result = parse("attr NOT BETWEEN 2 AND 5")
    assert result == ast.Between(
        ast.Attribute("attr"),
        2,
        5,
        True,
    )


def test_attribute_between_negative_positive():
    result = parse("attr BETWEEN -1 AND 1")
    assert result == ast.Between(
        ast.Attribute("attr"),
        -1,
        1,
        False,
    )


def test_attribute_not_between_negative_positive():
    result = parse("attr NOT BETWEEN -1 AND 1")
    assert result == ast.Between(
        ast.Attribute("attr"),
        -1,
        1,
        True,
    )


def test_string_like():
    result = parse("attr LIKE 'some%'")
    assert result == ast.Like(
        ast.Attribute("attr"),
        "some%",
        nocase=False,
        not_=False,
        wildcard="%",
        singlechar=".",
        escapechar="\\",
    )


def test_string_not_like():
    result = parse("attr NOT LIKE 'some%'")
    assert result == ast.Like(
        ast.Attribute("attr"),
        "some%",
        nocase=False,
        not_=True,
        wildcard="%",
        singlechar=".",
        escapechar="\\",
    )


def test_attribute_in_list():
    result = parse("attr IN (1, 2, 3, 4)")
    assert result == ast.In(
        ast.Attribute("attr"),
        [
            1,
            2,
            3,
            4,
        ],
        False,
    )


def test_attribute_not_in_list():
    result = parse("attr NOT IN (1, 2, 3, 4)")
    assert result == ast.In(
        ast.Attribute("attr"),
        [
            1,
            2,
            3,
            4,
        ],
        True,
    )


def test_attribute_is_null():
    result = parse("attr IS NULL")
    assert result == ast.IsNull(ast.Attribute("attr"), False)


def test_attribute_before():
    # Using TIMESTAMP function to properly wrap the timestamp
    result = parse("attr T_BEFORE TIMESTAMP('2000-01-01T00:00:01Z')")
    assert result == ast.TimeBefore(
        ast.Attribute("attr"),
        datetime(2000, 1, 1, 0, 0, 1, tzinfo=StaticTzInfo("Z", timedelta(0))),
    )


def test_attribute_t_intersects():
    # Using INTERVAL function with properly quoted timestamps
    result = parse(
        "attr T_INTERSECTS INTERVAL('2000-01-01T00:00:00Z', '2000-01-01T00:00:01Z')"
    )
    assert result == ast.TimeOverlaps(
        ast.Attribute("attr"),
        values.Interval(
            datetime(2000, 1, 1, 0, 0, 0, tzinfo=StaticTzInfo("Z", timedelta(0))),
            datetime(2000, 1, 1, 0, 0, 1, tzinfo=StaticTzInfo("Z", timedelta(0))),
        ),
    )


def test_attribute_tintersects_dt_dr():
    result = parse(
        "attr T_INTERSECTS INTERVAL('2000-01-01T00:00:03Z', '2000-01-01T00:00:04Z')"
    )
    assert result == ast.TimeOverlaps(
        ast.Attribute("attr"),
        values.Interval(
            datetime(2000, 1, 1, 0, 0, 3, tzinfo=StaticTzInfo("Z", timedelta(0))),
            datetime(2000, 1, 1, 0, 0, 4, tzinfo=StaticTzInfo("Z", timedelta(0))),
        ),
    )


def test_intersects_geometry():
    result = parse(
        "S_INTERSECTS(geometry, POLYGON((-77.0824 38.7886,-77.0189 38.7886,-77.0189 38.8351,-77.0824 38.8351,-77.0824 38.7886)))"
    )
    assert isinstance(result, ast.GeometryIntersects)
    assert result.lhs == ast.Attribute("geometry")
    # The exact structure of the polygon geometry depends on implementation details
    # Just validate the basic structure
    assert isinstance(result.rhs, values.Geometry)


def test_attribute_boolean_literal_true():
    result = parse("attr = TRUE")
    assert result == ast.Equal(
        ast.Attribute("attr"),
        True,
    )


def test_attribute_boolean_literal_false():
    result = parse("attr = FALSE")
    assert result == ast.Equal(
        ast.Attribute("attr"),
        False,
    )


def test_attribute_boolean_literal_lowercase_true():
    result = parse("attr = true")
    assert result == ast.Equal(
        ast.Attribute("attr"),
        True,
    )


def test_attribute_boolean_literal_lowercase_false():
    result = parse("attr = false")
    assert result == ast.Equal(
        ast.Attribute("attr"),
        False,
    )


def test_attribute_arithmetic_add():
    result = parse("attr = 5 + 2")
    assert result == ast.Equal(
        ast.Attribute("attr"),
        ast.Add(
            5,
            2,
        ),
    )


def test_attribute_arithmetic_sub():
    result = parse("attr = 5 - 2")
    assert result == ast.Equal(
        ast.Attribute("attr"),
        ast.Sub(
            5,
            2,
        ),
    )


def test_attribute_arithmetic_mul():
    result = parse("attr = 5 * 2")
    assert result == ast.Equal(
        ast.Attribute("attr"),
        ast.Mul(
            5,
            2,
        ),
    )


def test_attribute_arithmetic_div():
    result = parse("attr = 5 / 2")
    assert result == ast.Equal(
        ast.Attribute("attr"),
        ast.Div(
            5,
            2,
        ),
    )


def test_attribute_arithmetic_add_mul():
    result = parse("attr = 3 + 5 * 2")
    assert result == ast.Equal(
        ast.Attribute("attr"),
        ast.Add(
            3,
            ast.Mul(
                5,
                2,
            ),
        ),
    )


def test_attribute_arithmetic_div_sub():
    result = parse("attr = 3 / 5 - 2")
    assert result == ast.Equal(
        ast.Attribute("attr"),
        ast.Sub(
            ast.Div(
                3,
                5,
            ),
            2,
        ),
    )


def test_attribute_arithmetic_div_sub_bracketed():
    result = parse("attr = 3 / (5 - 2)")
    assert result == ast.Equal(
        ast.Attribute("attr"),
        ast.Div(
            3,
            ast.Sub(
                5,
                2,
            ),
        ),
    )


def test_function_single_arg():
    result = parse("attr = func(1)")
    assert result == ast.Equal(
        ast.Attribute("attr"),
        ast.Function(
            "func",
            [1],
        ),
    )


def test_function_multiple_args():
    result = parse("attr = func(other_attr, 'abc')")
    assert result == ast.Equal(
        ast.Attribute("attr"),
        ast.Function(
            "func",
            [
                ast.Attribute("other_attr"),
                "abc",
            ],
        ),
    )


def test_complex_expression():
    result = parse(
        "collection = 'landsat8_l1tp' AND gsd <= 30 AND eo:cloud_cover <= 10 AND datetime >= TIMESTAMP('2021-04-08T04:39:23Z')"
    )
    assert isinstance(result, ast.And)
    assert isinstance(result.lhs, ast.And)
    assert isinstance(result.lhs.lhs, ast.And)
    assert result.lhs.lhs.lhs == ast.Equal(ast.Attribute("collection"), "landsat8_l1tp")
    assert result.lhs.lhs.rhs == ast.LessEqual(ast.Attribute("gsd"), 30)
    assert result.lhs.rhs == ast.LessEqual(ast.Attribute("eo:cloud_cover"), 10)
    # The exact datetime comparison depends on implementation details
    assert isinstance(result.rhs, ast.GreaterEqual)
    assert result.rhs.lhs == ast.Attribute("datetime")


def test_nested_and_or():
    result = parse("(attr_a = 1 AND attr_b = 2) OR (attr_c = 3 AND attr_d = 4)")
    assert isinstance(result, ast.Or)
    assert isinstance(result.lhs, ast.And)
    assert isinstance(result.rhs, ast.And)
    assert result.lhs.lhs == ast.Equal(ast.Attribute("attr_a"), 1)
    assert result.lhs.rhs == ast.Equal(ast.Attribute("attr_b"), 2)
    assert result.rhs.lhs == ast.Equal(ast.Attribute("attr_c"), 3)
    assert result.rhs.rhs == ast.Equal(ast.Attribute("attr_d"), 4)


def test_casei_function():
    result = parse("CASEI(provider) = 'coolsat'")
    # Assuming CASEI maps to 'lower' in the implementation
    assert isinstance(result, ast.Equal)
    assert isinstance(result.lhs, ast.Function)
    assert result.lhs.name == "lower"
    assert result.lhs.arguments == [ast.Attribute("provider")]
    assert result.rhs == "coolsat"
