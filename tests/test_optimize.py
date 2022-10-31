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

from pygeofilter import ast
from pygeofilter.backends.optimize import optimize
from pygeofilter.parsers.ecql import parse


def test_not():
    result = optimize(parse("NOT 1 > 2"))
    assert result == ast.Include(False)

    result = optimize(parse("NOT 1 < 2"))
    assert result == ast.Include(True)


def test_combination():
    # reduce right hand side
    result = optimize(parse("attr = 1 AND 1 < 2"))
    assert result == ast.Equal(ast.Attribute("attr"), 1)

    # reduce left hand side
    result = optimize(parse("1 < 2 AND attr = 1"))
    assert result == ast.Equal(ast.Attribute("attr"), 1)

    # reduce left hand side
    result = optimize(parse("1 < 2 AND attr = 1"))
    assert result == ast.Equal(ast.Attribute("attr"), 1)

    # can' reduce
    result = optimize(parse("attr = 1 AND other = 2"))
    assert result == ast.And(
        ast.Equal(ast.Attribute("attr"), 1), ast.Equal(ast.Attribute("other"), 2)
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
    assert result == ast.Equal(ast.Attribute("attr"), 1)

    # reduce greater than
    result = optimize(parse("2 > 1 AND attr = 1"))
    assert result == ast.Equal(ast.Attribute("attr"), 1)

    # reduce less or equal
    result = optimize(parse("1 <= 2 AND attr = 1"))
    assert result == ast.Equal(ast.Attribute("attr"), 1)

    # reduce greater or equal
    result = optimize(parse("2 >= 1 AND attr = 1"))
    assert result == ast.Equal(ast.Attribute("attr"), 1)

    # reduce not equal
    result = optimize(parse("2 <> 1 AND attr = 1"))
    assert result == ast.Equal(ast.Attribute("attr"), 1)


def test_between():
    # allow reduction
    result = optimize(parse("5 BETWEEN 1 AND 6 AND attr = 1"))
    assert result == ast.Equal(ast.Attribute("attr"), 1)
    result = optimize(parse("10 NOT BETWEEN 1 AND 6 AND attr = 1"))
    assert result == ast.Equal(ast.Attribute("attr"), 1)

    # don't reduce if either lhs, low or high are uncertain
    result = optimize(parse("attr BETWEEN 1 AND 6"))
    assert result == ast.Between(ast.Attribute("attr"), 1, 6, False)
    result = optimize(parse("5 BETWEEN attr AND 6"))
    assert result == ast.Between(5, ast.Attribute("attr"), 6, False)
    result = optimize(parse("5 BETWEEN 1 AND attr"))
    assert result == ast.Between(5, 1, ast.Attribute("attr"), False)


def test_like():
    # allow reduction
    result = optimize(parse("'This is a test' LIKE 'This is %' AND attr = 1"))
    assert result == ast.Equal(ast.Attribute("attr"), 1)
    result = optimize(parse("'This is a test' LIKE 'This is . test' AND attr = 1"))
    assert result == ast.Equal(ast.Attribute("attr"), 1)

    # don't reduction when an attribute is referenced
    result = optimize(parse("attr LIKE 'This is %'"))
    assert result == ast.Like(
        ast.Attribute("attr"), "This is %", False, "%", ".", "\\", False
    )


def test_in():
    # allow reduction when the left hand side and all options
    # are certain
    result = optimize(parse("1 IN (1, 2, 3) AND attr = 1"))
    assert result == ast.Equal(ast.Attribute("attr"), 1)
    result = optimize(parse("5 NOT IN (1, 2, 3) AND attr = 1"))
    assert result == ast.Equal(ast.Attribute("attr"), 1)
    # don't allow reduction if either left hand side or either option
    # is uncertain
    result = optimize(parse("attr IN (1, 2, 3)"))
    assert result == ast.In(ast.Attribute("attr"), [1, 2, 3], False)
    result = optimize(parse("1 IN (attr, 2, 3)"))
    assert result == ast.In(1, [ast.Attribute("attr"), 2, 3], False)


def test_temporal():
    # TODO
    pass


def test_array():
    # TODO
    pass


def test_spatial():
    # TODO
    pass


def test_arithmetic():
    # test possible optimizations
    result = optimize(parse("attr = 10 + 10"))
    assert result == ast.Equal(ast.Attribute("attr"), 20)

    result = optimize(parse("attr = 30 - 10"))
    assert result == ast.Equal(ast.Attribute("attr"), 20)

    result = optimize(parse("attr = 10 * 2"))
    assert result == ast.Equal(ast.Attribute("attr"), 20)

    result = optimize(parse("attr = 40 / 2"))
    assert result == ast.Equal(ast.Attribute("attr"), 20)

    # test imppossible optimizations
    result = optimize(parse("attr = other + 10"))
    assert result == ast.Equal(
        ast.Attribute("attr"),
        ast.Add(ast.Attribute("other"), 10),
    )

    result = optimize(parse("attr = other - 10"))
    assert result == ast.Equal(
        ast.Attribute("attr"),
        ast.Sub(ast.Attribute("other"), 10),
    )

    result = optimize(parse("attr = other * 2"))
    assert result == ast.Equal(
        ast.Attribute("attr"),
        ast.Mul(ast.Attribute("other"), 2),
    )

    result = optimize(parse("attr = other / 2"))
    assert result == ast.Equal(
        ast.Attribute("attr"),
        ast.Div(ast.Attribute("other"), 2),
    )


def test_function():
    def myadder(a, b):
        return a + b

    result = optimize(parse("attr = myadder(1, 2)"), {"myadder": myadder})
    assert result == ast.Equal(
        ast.Attribute("attr"),
        3,
    )

    # can't optimize a function referencing an attribute
    result = optimize(parse("attr = myadder(other, 2)"), {"myadder": myadder})
    assert result == ast.Equal(
        ast.Attribute("attr"), ast.Function("myadder", [ast.Attribute("other"), 2])
    )
    # can't optimize a function with a nested reference to an attribute
    result = optimize(parse("attr = myadder(other + 2, 2)"), {"myadder": myadder})
    assert result == ast.Equal(
        ast.Attribute("attr"),
        ast.Function("myadder", [ast.Add(ast.Attribute("other"), 2), 2]),
    )

    # can't optimize an unknown functions
    result = optimize(parse("attr = unkown(1, 2)"), {"myadder": myadder})
    assert result == ast.Equal(
        ast.Attribute("attr"),
        ast.Function(
            "unkown",
            [
                1,
                2,
            ],
        ),
    )
