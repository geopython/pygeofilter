from datetime import datetime
from pygeofilter import ast
from pygeofilter.parsers.ecql import parse
from pygeofilter.backends.optimize import optimize


def test_not():
    result = optimize(parse("NOT 1 > 2"))
    assert result == ast.Include(False)

    result = optimize(parse("NOT 1 < 2"))
    assert result == ast.Include(True)


def test_combination():
    # reduce right hand side
    result = optimize(parse("attr = 1 AND 1 < 2"))
    assert result == ast.Equal(
        ast.Attribute('attr'),
        1
    )

    # reduce left hand side
    result = optimize(parse("1 < 2 AND attr = 1"))
    assert result == ast.Equal(
        ast.Attribute('attr'),
        1
    )

    # reduce left hand side
    result = optimize(parse("1 < 2 AND attr = 1"))
    assert result == ast.Equal(
        ast.Attribute('attr'),
        1
    )

    # can' reduce
    result = optimize(parse("attr = 1 AND other = 2"))
    assert result == ast.And(
        ast.Equal(
            ast.Attribute('attr'),
            1
        ),
        ast.Equal(
            ast.Attribute('other'),
            2
        )
    )

    # reduce AND to an INCLUDE if both sides evaluate to true
    result = optimize(parse("1 = 1 AND 2 = 2"))
    assert result == ast.Include(False)

    # reduce AND to an EXCLUDE if either side evaluates to false
    result = optimize(parse("attr = 1 AND 2 = 3"))
    assert result == ast.Include(True)
    result = optimize(parse("2 = 3 AND attr = 1"))
    assert result == ast.Include(True)
    result = optimize(parse("0 = 1 AND 2 = 3"))
    assert result == ast.Include(True)

    # reduce OR to INCLUDE if either side evaluates to true
    result = optimize(parse("attr = 1 OR 2 = 2"))
    assert result == ast.Include(False)
    result = optimize(parse("2 = 2 OR attr = 1"))
    assert result == ast.Include(False)

    # reduce OR to an EXCLUDE if both sides evaluate to false
    result = optimize(parse("1 = 2 AND 2 = 1"))
    assert result == ast.Include(True)


def test_comparison():
    # reduce less than
    result = optimize(parse("1 < 2 AND attr = 1"))
    assert result == ast.Equal(
        ast.Attribute('attr'),
        1
    )

    # reduce greater than
    result = optimize(parse("2 > 1 AND attr = 1"))
    assert result == ast.Equal(
        ast.Attribute('attr'),
        1
    )

    # reduce less or equal
    result = optimize(parse("1 <= 2 AND attr = 1"))
    assert result == ast.Equal(
        ast.Attribute('attr'),
        1
    )

    # reduce greater or equal
    result = optimize(parse("2 >= 1 AND attr = 1"))
    assert result == ast.Equal(
        ast.Attribute('attr'),
        1
    )

    # reduce not equal
    result = optimize(parse("2 <> 1 AND attr = 1"))
    assert result == ast.Equal(
        ast.Attribute('attr'),
        1
    )


def test_between():
    # allow reduction
    result = optimize(parse("5 BETWEEN 1 AND 6 AND attr = 1"))
    assert result == ast.Equal(
        ast.Attribute('attr'),
        1
    )
    result = optimize(parse("10 NOT BETWEEN 1 AND 6 AND attr = 1"))
    assert result == ast.Equal(
        ast.Attribute('attr'),
        1
    )

    # don't reduce if either lhs, low or high are uncertain
    result = optimize(parse("attr BETWEEN 1 AND 6"))
    assert result == ast.Between(
        ast.Attribute("attr"), 1, 6, False
    )
    result = optimize(parse("5 BETWEEN attr AND 6"))
    assert result == ast.Between(
        5, ast.Attribute("attr"), 6, False
    )
    result = optimize(parse("5 BETWEEN 1 AND attr"))
    assert result == ast.Between(
        5, 1, ast.Attribute("attr"), False
    )


def test_like():
    # allow reduction
    result = optimize(parse("'This is a test' LIKE 'This is %' AND attr = 1"))
    assert result == ast.Equal(
        ast.Attribute('attr'),
        1
    )
    result = optimize(
        parse("'This is a test' LIKE 'This is . test' AND attr = 1")
    )
    assert result == ast.Equal(
        ast.Attribute('attr'),
        1
    )

    # don't reduction when an attribute is referenced
    result = optimize(parse("attr LIKE 'This is %'"))
    assert result == ast.Like(
        ast.Attribute('attr'),
        'This is %',
        False,
        '%',
        '.',
        '\\',
        False
    )


def test_arithmetic():
    # test possible optimizations
    result = optimize(parse("attr = 10 + 10"))
    assert result == ast.Equal(
        ast.Attribute('attr'),
        20
    )

    result = optimize(parse("attr = 30 - 10"))
    assert result == ast.Equal(
        ast.Attribute('attr'),
        20
    )

    result = optimize(parse("attr = 10 * 2"))
    assert result == ast.Equal(
        ast.Attribute('attr'),
        20
    )

    result = optimize(parse("attr = 40 / 2"))
    assert result == ast.Equal(
        ast.Attribute('attr'),
        20
    )

    # test imppossible optimizations
    result = optimize(parse("attr = other + 10"))
    assert result == ast.Equal(
        ast.Attribute('attr'),
        ast.Add(
            ast.Attribute('other'), 10
        ),
    )

    result = optimize(parse("attr = other - 10"))
    assert result == ast.Equal(
        ast.Attribute('attr'),
        ast.Sub(
            ast.Attribute('other'), 10
        ),
    )

    result = optimize(parse("attr = other * 2"))
    assert result == ast.Equal(
        ast.Attribute('attr'),
        ast.Mul(
            ast.Attribute('other'), 2
        ),
    )

    result = optimize(parse("attr = other / 2"))
    assert result == ast.Equal(
        ast.Attribute('attr'),
        ast.Div(
            ast.Attribute('other'), 2
        ),
    )


def test_function():
    def myadder(a, b):
        return a + b

    result = optimize(parse("attr = myadder(1, 2)"), {"myadder": myadder})
    assert result == ast.Equal(
        ast.Attribute('attr'),
        3,
    )

    # can't optimize a function referencing an attribute
    result = optimize(parse("attr = myadder(other, 2)"), {"myadder": myadder})
    assert result == ast.Equal(
        ast.Attribute('attr'),
        ast.Function(
            "myadder", [
                ast.Attribute("other"),
                2
            ]
        )
    )
    # can't optimize a function with a nested reference to an attribute
    result = optimize(
        parse("attr = myadder(other + 2, 2)"), {"myadder": myadder}
    )
    assert result == ast.Equal(
        ast.Attribute('attr'),
        ast.Function(
            "myadder", [
                ast.Add(ast.Attribute("other"), 2),
                2
            ]
        )
    )

    # can't optimize an unknown functions
    result = optimize(parse("attr = unkown(1, 2)"), {"myadder": myadder})
    assert result == ast.Equal(
        ast.Attribute('attr'),
        ast.Function(
            "unkown", [
                1,
                2,
            ]
        )
    )
