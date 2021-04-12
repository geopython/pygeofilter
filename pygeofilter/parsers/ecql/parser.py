from sly import Parser

from ... import ast
from .lexer import ECQLLexer


class ECQLParser(Parser):
    tokens = ECQLLexer.tokens

    precedence = (
        ('left', EQ, NE),               # noqa: F821
        ('left', GT, GE, LT, LE),       # noqa: F821
        ('left', PLUS, MINUS),          # noqa: F821
        ('left', TIMES, DIVIDE),        # noqa: F821
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

    @_('condition AND condition',
       'condition OR condition')
    def condition(self, p):
        return ast.CombinationConditionNode(
            p[0],
            p[2],
            ast.CombinationOp(p[1])
        )

    @_('NOT condition')
    def condition(self, p):
        return ast.NotConditionNode(p.condition)

    @_('LPAREN condition RPAREN',
       'LBRACKET condition RBRACKET')
    def condition(self, p):
        return p.condition

    @_('expression EQ expression',
       'expression NE expression',
       'expression LT expression',
       'expression LE expression',
       'expression GT expression',
       'expression GE expression')
    def predicate(self, p):
        return ast.ComparisonPredicateNode(p[0], p[2], ast.ComparisonOp(p[1]))

    @_('expression NOT BETWEEN expression AND expression',
       'expression BETWEEN expression AND expression')
    def predicate(self, p):
        return ast.BetweenPredicateNode(
            p[0], p[-3], p[-1], p[1] == 'NOT'
        )

    @_('expression NOT LIKE QUOTED',
       'expression LIKE QUOTED')
    def predicate(self, p):
        return ast.LikePredicateNode(
            p.expression,
            ast.LiteralExpression(p[-1]),
            nocase=False,
            wildcard='%',
            singlechar='.',
            escapechar=None,
            not_=p[1] == 'NOT',
        )

    @_('expression NOT ILIKE QUOTED',
       'expression ILIKE QUOTED')
    def predicate(self, p):
        return ast.LikePredicateNode(
            p.expression,
            ast.LiteralExpression(p[-1]),
            nocase=True,
            wildcard='%',
            singlechar='.',
            escapechar=None,
            not_=p[1] == 'NOT',
        )

    @_('expression NOT IN LPAREN expression_list RPAREN',
       'expression IN LPAREN expression_list RPAREN')
    def predicate(self, p):
        return ast.InPredicateNode(p[0], p[-2], p[1] == 'NOT')

    @_('expression IS NOT NULL',
       'expression IS NULL')
    def predicate(self, p):
        return ast.NullPredicateNode(p[0], p[2] == 'NOT')

    @_('temporal_predicate',
       'spatial_predicate')
    def predicate(self, p):
        return p[0]

    @_('expression BEFORE DATETIME',
       'expression BEFORE OR DURING time_period',
       'expression DURING time_period',
       'expression DURING OR AFTER time_period',
       'expression AFTER DATETIME')
    def temporal_predicate(self, p):
        if len(p) == 3:
            op = ast.TemporalComparisonOp(p[1])
        else:
            op = ast.TemporalComparisonOp(f'{p[1]} {p[2]} {p[3]}')
        return ast.TemporalPredicateNode(p.expression, p[-1], op)

    @_('DATETIME DIVIDE DATETIME',
       'DATETIME DIVIDE DURATION',
       'DURATION DIVIDE DATETIME')
    def time_period(self, p):
        return (p[0], p[2])

    @_('INTERSECTS LPAREN expression COMMA expression RPAREN',
       'DISJOINT LPAREN expression COMMA expression RPAREN',
       'CONTAINS LPAREN expression COMMA expression RPAREN',
       'WITHIN LPAREN expression COMMA expression RPAREN',
       'TOUCHES LPAREN expression COMMA expression RPAREN',
       'CROSSES LPAREN expression COMMA expression RPAREN',
       'OVERLAPS LPAREN expression COMMA expression RPAREN',
       'EQUALS LPAREN expression COMMA expression RPAREN')
    def spatial_predicate(self, p):
        return ast.SpatialOperationPredicateNode(
            p[2],
            p[4],
            ast.SpatialComparisonOp(p[0])
        )

    @_('RELATE LPAREN expression COMMA expression COMMA QUOTED RPAREN')
    def spatial_predicate(self, p):
        return ast.SpatialPatternPredicateNode(p[2], p[4], pattern=p[6])

    @_('DWITHIN LPAREN expression COMMA expression COMMA number COMMA UNITS RPAREN',
       'BEYOND LPAREN expression COMMA expression COMMA number COMMA UNITS RPAREN')
    def spatial_predicate(self, p):
        return ast.SpatialDistancePredicateNode(
            p[2],
            p[4],
            ast.SpatialDistanceOp(p[0]),
            distance=p[6].value,
            units=p[8],
        )

    @_('BBOX LPAREN expression COMMA number COMMA number COMMA number COMMA number RPAREN')
    def spatial_predicate(self, p):
        return ast.BBoxPredicateNode(p[2], p[4], p[6], p[8], p[10])

    @_('BBOX LPAREN expression COMMA number COMMA number COMMA number COMMA number COMMA QUOTED RPAREN')
    def spatial_predicate(self, p):
        return ast.BBoxPredicateNode(p[2], p[4], p[6], p[8], p[10], p[12])

    @_('expression_list COMMA expression')
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
        return ast.ArithmeticExpressionNode(
            p[0],
            p[2],
            ast.ArithmeticOp(p[1]),
        )

    @_('LPAREN expression RPAREN',
       'LBRACKET expression RBRACKET')
    def expression(self, p):
        return p[1]

    @_('IDENTIFIER LPAREN RPAREN')
    def expression(self, p):
        return ast.FunctionExpressionNode(p[0], [])

    @_('IDENTIFIER LPAREN expression_list RPAREN')
    def expression(self, p):
        return ast.FunctionExpressionNode(p[0], p.expression_list)

    @_('GEOMETRY',
       'ENVELOPE',
       'attribute',
       'QUOTED',
       'INTEGER',
       'FLOAT')
    def expression(self, p):
        if isinstance(p[0], ast.Node):
            return p[0]
        return ast.LiteralExpression(p[0])

    @_('INTEGER',
       'FLOAT')
    def number(self, p):
        return ast.LiteralExpression(p[0])

    @_('IDENTIFIER')
    def attribute(self, p):
        return ast.AttributeExpression(p[0])

    def error(self, tok):
        raise Exception(f"{repr(tok)}")


def parse(cql):
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
