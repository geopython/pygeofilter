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


# pylint: disable=undefined-variable,function-redefined,used-before-assignment
# pylint: disable=unsupported-assignment-operation
# flake8: noqa

from sly import Lexer
from pygeoif import from_wkt
from dateparser import parse as parse_datetime

from ...util import parse_duration
from ... import values


# a simple pattern that allows the simple float and integer notations (but
# not the scientific ones). Maybe TODO
number_pattern = r'-?[0-9]*\.?[0-9]+'

coordinate_2d_pattern = r'%s\s+%s\s*' % (number_pattern, number_pattern)
coordinate_3d_pattern = r'%s\s+%s\s*' % (
    coordinate_2d_pattern, number_pattern
)
coordinate_4d_pattern = r'%s\s+%s\s*' % (
    coordinate_3d_pattern, number_pattern
)
coordinate_pattern = r'((%s)|(%s)|(%s))' % (
    coordinate_2d_pattern, coordinate_3d_pattern, coordinate_4d_pattern
)

coordinates_pattern = r'%s(\s*,\s*%s)*' % (
    coordinate_pattern, coordinate_pattern
)

coordinate_group_pattern = r'\(\s*%s\s*\)' % coordinates_pattern
coordinate_groups_pattern = r'%s(\s*,\s*%s)*' % (
    coordinate_group_pattern, coordinate_group_pattern
)

nested_coordinate_group_pattern = r'\(\s*%s\s*\)' % coordinate_groups_pattern
nested_coordinate_groups_pattern = r'%s(\s*,\s*%s)*' % (
    nested_coordinate_group_pattern, nested_coordinate_group_pattern
)

geometry_pattern = (
    r'(POINT\s*\(%s\))|' % coordinate_pattern +
    r'((MULTIPOINT|LINESTRING)\s*\(%s\))|' % coordinates_pattern +
    r'((MULTIPOINT|MULTILINESTRING|POLYGON)\s*\(%s\))|' % (
        coordinate_groups_pattern
    ) +
    r'(MULTIPOLYGON\s*\(%s\))' % nested_coordinate_groups_pattern
)
envelope_pattern = r'ENVELOPE\s*\((\s*%s\s*){4}\)' % number_pattern

identifier_pattern = r'[a-zA-Z_$][0-9a-zA-Z_$]*'

int_pattern = r'[0-9]+'
float_pattern = r'[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?'

datetime_pattern = r"\d{4}-\d{2}-\d{2}T[0-2][0-9]:[0-5][0-9]:[0-5][0-9](\.[0-9]+)?(Z|[+-][0-9]{2}:[0-9]{2})"
duration_pattern = (
    # "P(?=[YMDHMS])"  # positive lookahead here... TODO: does not work
    # "((\d+Y)?(\d+M)?(\d+D)?)?(T(\d+H)?(\d+M)?(\d+S)?)?"
    r"P((\d+Y)?(\d+M)?(\d+D)?)?(T(\d+H)?(\d+M)?(\d+S)?)?"
)
double_quoted_string_pattern = r'(\"[^"]*\")'
quoted_string_pattern = r'(\'[^\']*\')'


class ECQLLexer(Lexer):
    tokens = {
        EXISTS, DOES_NOT_EXIST, INCLUDE, EXCLUDE,
        NOT, AND, OR, BETWEEN, LIKE, ILIKE, IN, IS, NULL,
        BEFORE, AFTER, DURING, INTERSECTS, DISJOINT, CONTAINS,
        WITHIN, TOUCHES, CROSSES, OVERLAPS, EQUALS, RELATE,
        DWITHIN, BEYOND, BBOX,
        PLUS, MINUS, TIMES, DIVIDE, OR, AND, LT, GT, LE, GE, EQ, NE,
        GEOMETRY, ENVELOPE, UNITS,
        QUOTED, DOUBLE_QUOTED, DATETIME, DURATION, FLOAT, INTEGER,
        IDENTIFIER,
    }

    literals = {'(', ')', '[', ']', ','}

    DOES_NOT_EXIST = r'DOES-NOT-EXIST'
    PLUS = r'\+'
    MINUS = r'-'
    TIMES = r'\*'
    DIVIDE = r'/'
    OR = r'OR'
    AND = r'AND'
    NE = r'<>'
    LE = r'<='
    GE = r'>='
    LT = r'<'
    GT = r'>'
    EQ = r'='

    # for geometry parsing
    @_(geometry_pattern)
    def GEOMETRY(self, t):
        t.value = from_wkt(t.value).__geo_interface__
        return t

    @_(envelope_pattern)
    def ENVELOPE(self, t):
        t.value = values.Envelope(*[
            float(number) for number in
            t.value.partition('(')[2].partition(')')[0].split()
        ])
        return t

    @_(r'(feet)|(meters)|(statute miles)|(nautical miles)|(kilometers)')
    def UNITS(self, t):
        return t

    @_(datetime_pattern)
    def DATETIME(self, t):
        t.value = parse_datetime(t.value)
        return t

    @_(duration_pattern)
    def DURATION(self, t):
        t.value = parse_duration(t.value)
        return t

    @_(float_pattern)
    def FLOAT(self, t):
        t.value = float(t.value)
        return t

    @_(int_pattern)
    def INTEGER(self, t):
        t.value = int(t.value)
        return t

    @_(quoted_string_pattern)
    def QUOTED(self, t):
        t.value = t.value[1:-1]
        return t

    @_(double_quoted_string_pattern)
    def DOUBLE_QUOTED(self, t):
        t.value = t.value[1:-1]
        return t

    IDENTIFIER = identifier_pattern

    # remap some tokens to be confused with identifiers
    IDENTIFIER['EXISTS'] = EXISTS
    IDENTIFIER['INCLUDE'] = INCLUDE
    IDENTIFIER['EXCLUDE'] = EXCLUDE
    IDENTIFIER['NOT'] = NOT
    IDENTIFIER['AND'] = AND
    IDENTIFIER['OR'] = OR
    IDENTIFIER['BETWEEN'] = BETWEEN
    IDENTIFIER['LIKE'] = LIKE
    IDENTIFIER['ILIKE'] = ILIKE
    IDENTIFIER['IN'] = IN
    IDENTIFIER['IS'] = IS
    IDENTIFIER['NULL'] = NULL
    IDENTIFIER['BEFORE'] = BEFORE
    IDENTIFIER['AFTER'] = AFTER
    IDENTIFIER['DURING'] = DURING
    IDENTIFIER['INTERSECTS'] = INTERSECTS
    IDENTIFIER['DISJOINT'] = DISJOINT
    IDENTIFIER['CONTAINS'] = CONTAINS
    IDENTIFIER['WITHIN'] = WITHIN
    IDENTIFIER['TOUCHES'] = TOUCHES
    IDENTIFIER['CROSSES'] = CROSSES
    IDENTIFIER['OVERLAPS'] = OVERLAPS
    IDENTIFIER['EQUALS'] = EQUALS
    IDENTIFIER['RELATE'] = RELATE
    IDENTIFIER['DWITHIN'] = DWITHIN
    IDENTIFIER['BEYOND'] = BEYOND
    IDENTIFIER['BBOX'] = BBOX

    ignore = ' \t'

    # Ignored pattern
    ignore_newline = r'\n+'

    # Extra action for newlines
    def ignore_newline(self, t):
        self.lineno += t.value.count('\n')

    def error(self, t):
        print("Illegal character '%s'" % t.value[0])
        self.index += 1
