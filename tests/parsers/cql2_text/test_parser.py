from pygeofilter import ast
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
