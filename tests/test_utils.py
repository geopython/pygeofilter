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

from pygeofilter.util import like_pattern_to_re

SEARCH_STRING = "This is a test"


def test_basic_single():
    pattern = r"This is . test"
    regex = like_pattern_to_re(
        pattern,
        nocase=False,
        wildcard="%",
        single_char=".",
        escape_char="\\",
    )
    assert regex.match(SEARCH_STRING) is not None


def test_basic():
    pattern = r"% a test"
    regex = like_pattern_to_re(
        pattern,
        nocase=False,
        wildcard="%",
        single_char=".",
        escape_char="\\",
    )
    assert regex.match(SEARCH_STRING) is not None


def test_basic_nocase():
    pattern = r"% A TEST"
    regex = like_pattern_to_re(
        pattern,
        nocase=True,
        wildcard="%",
        single_char=".",
        escape_char="\\",
    )
    assert regex.match(SEARCH_STRING) is not None


def test_basic_regex_escape_re_func():
    pattern = r".* a test"
    regex = like_pattern_to_re(
        pattern,
        nocase=True,
        wildcard="%",
        single_char=".",
        escape_char="\\",
    )
    assert regex.match(SEARCH_STRING) is None


def test_basic_regex_escape_char():
    search_string = r"This is a % sign"
    pattern = r"This is a /% sign"
    regex = like_pattern_to_re(
        pattern,
        nocase=True,
        wildcard="%",
        single_char=".",
        escape_char="/",
    )
    assert regex.match(search_string) is not None


def test_basic_regex_escape_char_2():
    search_string = r"This is a . sign"
    pattern = r"This is a /. sign"
    regex = like_pattern_to_re(
        pattern,
        nocase=True,
        wildcard="%",
        single_char=".",
        escape_char="/",
    )
    assert regex.match(search_string) is not None
