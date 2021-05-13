import re

from pygeofilter.util import like_pattern_to_re


SEARCH_STRING = "This is a test"


def test_basic_single():
    pattern = r'This is . test'
    regex = like_pattern_to_re(
        pattern,
        nocase=False,
        wildcard='%',
        single_char='.',
        escape_char='\\',
    )
    assert regex.match(SEARCH_STRING) is not None


def test_basic():
    pattern = r'% a test'
    regex = like_pattern_to_re(
        pattern,
        nocase=False,
        wildcard='%',
        single_char='.',
        escape_char='\\',
    )
    assert regex.match(SEARCH_STRING) is not None


def test_basic_nocase():
    pattern = r'% A TEST'
    regex = like_pattern_to_re(
        pattern,
        nocase=True,
        wildcard='%',
        single_char='.',
        escape_char='\\',
    )
    assert regex.match(SEARCH_STRING) is not None


def test_basic_regex_escape_re_func():
    pattern = r'.* a test'
    regex = like_pattern_to_re(
        pattern,
        nocase=True,
        wildcard='%',
        single_char='.',
        escape_char='\\',
    )
    assert regex.match(SEARCH_STRING) is None


def test_basic_regex_escape_char():
    search_string = r'This is a % sign'
    pattern = r'This is a /% sign'
    regex = like_pattern_to_re(
        pattern,
        nocase=True,
        wildcard='%',
        single_char='.',
        escape_char='/',
    )
    assert regex.match(search_string) is not None


def test_basic_regex_escape_char_2():
    search_string = r'This is a . sign'
    pattern = r'This is a /. sign'
    regex = like_pattern_to_re(
        pattern,
        nocase=True,
        wildcard='%',
        single_char='.',
        escape_char='/',
    )
    assert regex.match(search_string) is not None
