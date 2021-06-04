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


# pylint: disable=undefined-variable,function-redefined
# flake8: noqa

from sly import Parser

from ... import ast
from .lexer import ECQLLexer


class ECQLParser(Parser):
    tokens = ECQLLexer.tokens

    precedence = (
        ('left', EQ, NE),
        ('left', GT, GE, LT, LE),
        ('left', PLUS, MINUS),
        ('left', TIMES, DIVIDE),
        ('right', UMINUS),
    )

    start = 'condition_or_empty'

    @_('')
    def empty(self, p):
        return None

    @_('condition',
       'empty')
    def condition_or_empty(self, p):
        return p[0]

    @_('predicate')
    def condition(self, p):
        return p.predicate

    @_('predicate AND predicate',
       'predicate OR predicate')
    def condition(self, p):
        if p[1] == 'AND':
            return ast.And(p[0], p[2])
        else:
            return ast.Or(p[0], p[2])

    @_('NOT condition')
    def condition(self, p):
        return ast.Not(p.condition)

    @_('"(" condition ")"',
       '"[" condition "]"')
    def condition(self, p):
        return p.condition

    @_('expression EQ expression',
       'expression NE expression',
       'expression LT expression',
       'expression LE expression',
       'expression GT expression',
       'expression GE expression')
    def predicate(self, p):
        op = p[1]
        if op == '=':
            return ast.Equal(p[0], p[2])
        elif op == '<>':
            return ast.NotEqual(p[0], p[2])
        elif op == '<':
            return ast.LessThan(p[0], p[2])
        elif op == '<=':
            return ast.LessEqual(p[0], p[2])
        elif op == '>':
            return ast.GreaterThan(p[0], p[2])
        elif op == '>=':
            return ast.GreaterEqual(p[0], p[2])

    @_('expression NOT BETWEEN expression AND expression',
       'expression BETWEEN expression AND expression')
    def predicate(self, p):
        return ast.Between(
            p[0], p[-3], p[-1], p[1] == 'NOT'
        )

    @_('expression NOT LIKE QUOTED',
       'expression LIKE QUOTED')
    def predicate(self, p):
        return ast.Like(
            p.expression,
            p[-1],
            nocase=False,
            wildcard='%',
            singlechar='.',
            escapechar='\\',
            not_=p[1] == 'NOT',
        )

    @_('expression NOT ILIKE QUOTED',
       'expression ILIKE QUOTED')
    def predicate(self, p):
        return ast.Like(
            p.expression,
            p[-1],
            nocase=True,
            wildcard='%',
            singlechar='.',
            escapechar='\\',
            not_=p[1] == 'NOT',
        )

    @_('expression NOT IN "(" expression_list ")"',
       'expression IN "(" expression_list ")"')
    def predicate(self, p):
        return ast.In(p[0], p[-2], p[1] == 'NOT')

    @_('expression IS NOT NULL',
       'expression IS NULL')
    def predicate(self, p):
        return ast.IsNull(p[0], p[2] == 'NOT')

    @_('attribute EXISTS',
       'attribute DOES_NOT_EXIST')
    def predicate(self, p):
        return ast.Exists(p[0], p[1] != 'EXISTS')

    @_('INCLUDE',
       'EXCLUDE')
    def predicate(self, p):
        return ast.Include(p[0] != 'INCLUDE')

    @_('temporal_predicate',
       'spatial_predicate')
    def predicate(self, p):
        return p[0]

    @_('expression BEFORE datetime',
       'expression BEFORE OR DURING time_period',
       'expression DURING time_period',
       'expression DURING OR AFTER time_period',
       'expression AFTER datetime')
    def temporal_predicate(self, p):
        if len(p) == 3:
            op = p[1]
            if op == 'BEFORE':
                return ast.TimeBefore(p.expression, p[-1])
            elif op == 'DURING':
                return ast.TimeDuring(p.expression, p[-1])
            elif op == 'AFTER':
                return ast.TimeAfter(p.expression, p[-1])
        else:
            op = f'{p[1]} {p[2]} {p[3]}'
            if op == 'BEFORE OR DURING':
                return ast.TimeBeforeOrDuring(p.expression, p[-1])
            elif op == 'DURING OR AFTER':
                return ast.TimeDuringOrAfter(p.expression, p[-1])

    @_('datetime DIVIDE datetime',
       'datetime DIVIDE duration',
       'duration DIVIDE datetime')
    def time_period(self, p):
        return [p[0], p[2]]

    @_('INTERSECTS "(" expression "," expression ")"',
       'DISJOINT "(" expression "," expression ")"',
       'CONTAINS "(" expression "," expression ")"',
       'WITHIN "(" expression "," expression ")"',
       'TOUCHES "(" expression "," expression ")"',
       'CROSSES "(" expression "," expression ")"',
       'OVERLAPS "(" expression "," expression ")"',
       'EQUALS "(" expression "," expression ")"')
    def spatial_predicate(self, p):
        op = p[0]
        if op == 'INTERSECTS':
            return ast.GeometryIntersects(p[2], p[4])
        elif op == 'DISJOINT':
            return ast.GeometryDisjoint(p[2], p[4])
        elif op == 'CONTAINS':
            return ast.GeometryContains(p[2], p[4])
        elif op == 'WITHIN':
            return ast.GeometryWithin(p[2], p[4])
        elif op == 'TOUCHES':
            return ast.GeometryTouches(p[2], p[4])
        elif op == 'CROSSES':
            return ast.GeometryCrosses(p[2], p[4])
        elif op == 'OVERLAPS':
            return ast.GeometryOverlaps(p[2], p[4])
        elif op == 'EQUALS':
            return ast.GeometryEquals(p[2], p[4])

    @_('RELATE "(" expression "," expression "," QUOTED ")"')
    def spatial_predicate(self, p):
        return ast.Relate(p[2], p[4], pattern=p[6])

    @_('DWITHIN "(" expression "," expression "," number "," UNITS ")"',
       'BEYOND "(" expression "," expression "," number "," UNITS ")"')
    def spatial_predicate(self, p):
        op = p[0]
        if op == 'DWITHIN':
            return ast.DistanceWithin(p[2], p[4], p[6], p[8])
        elif op == 'BEYOND':
            return ast.DistanceBeyond(p[2], p[4], p[6], p[8])

    @_('BBOX "(" expression "," number "," number "," number "," number ")"')
    def spatial_predicate(self, p):
        return ast.BBox(p[2], p[4], p[6], p[8], p[10])

    @_('BBOX "(" expression "," number "," number "," number "," number "," QUOTED ")"')
    def spatial_predicate(self, p):
        return ast.BBox(p[2], p[4], p[6], p[8], p[10], p[12])

    @_('expression_list "," expression')
    def expression_list(self, p):
        p.expression_list.append(p.expression)
        return p.expression_list

    @_('expression')
    def expression_list(self, p):
        return [p.expression]

    @_('expression PLUS expression',
       'expression MINUS expression',
       'expression TIMES expression',
       'expression DIVIDE expression')
    def expression(self, p):
        op = p[1]
        if op == '+':
            return ast.Add(p[0], p[2])
        elif op == '-':
            return ast.Sub(p[0], p[2])
        elif op == '*':
            return ast.Mul(p[0], p[2])
        elif op == '/':
            return ast.Div(p[0], p[2])

    @_('"(" expression ")"',
       '"[" expression "]"')
    def expression(self, p):
        return p[1]

    @_('IDENTIFIER "(" ")"')
    def expression(self, p):
        return ast.Function(p[0], [])

    @_('IDENTIFIER "(" expression_list ")"')
    def expression(self, p):
        return ast.Function(p[0], p.expression_list)

    @_('GEOMETRY',
       'ENVELOPE',
       'attribute',
       'QUOTED',
       'number')
    def expression(self, p):
        if isinstance(p[0], ast.Node):
            return p[0]
        return p[0]

    @_('MINUS number %prec UMINUS')
    def number(self, p):
        return -p.number

    @_('INTEGER',
       'FLOAT')
    def number(self, p):
        return p[0]

    @_('DATETIME')
    def datetime(self, p):
        return p[0]

    @_('DURATION')
    def duration(self, p):
        return p[0]

    @_('IDENTIFIER',
       'DOUBLE_QUOTED')
    def attribute(self, p):
        return ast.Attribute(p[0])

    def error(self, tok):
        raise Exception(f"{repr(tok)}")


def parse(cql: str) -> ast.Node:
    lexer = ECQLLexer()
    parser = ECQLParser()

    try:
        result = parser.parse(lexer.tokenize(cql))
        if not result:
            raise Exception
        return result
    except:
        print(cql)
        for tok in lexer.tokenize(cql):
            print('\ttype=%r, value=%r' % (tok.type, tok.value))
        raise
