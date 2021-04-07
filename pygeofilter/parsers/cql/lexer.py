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

int_pattern = r'-?[0-9]+'
float_pattern = r'[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?'

datetime_pattern = r"\d{4}-\d{2}-\d{2}T[0-2][0-9]:[0-5][0-9]:[0-5][0-9]Z"
duration_pattern = (
    # "P(?=[YMDHMS])"  # positive lookahead here... TODO: does not work
    # "((\d+Y)?(\d+M)?(\d+D)?)?(T(\d+H)?(\d+M)?(\d+S)?)?"
    r"P((\d+Y)?(\d+M)?(\d+D)?)?(T(\d+H)?(\d+M)?(\d+S)?)?"
)
quoted_string_pattern = r'(\"[^"]*\")|(\'[^\']*\')'


class CQLLexer(Lexer):
    tokens = {
        NOT, AND, OR, BETWEEN, LIKE, ILIKE, IN, IS, NULL,
        BEFORE, AFTER, DURING, INTERSECTS, DISJOINT, CONTAINS,
        WITHIN, TOUCHES, CROSSES, OVERLAPS, EQUALS, RELATE,
        DWITHIN, BEYOND, BBOX,
        PLUS, MINUS, TIMES, DIVIDE, OR, AND, LT, GT, LE, GE, EQ, NE,
        LPAREN, RPAREN, LBRACKET, RBRACKET, COMMA,
        GEOMETRY, ENVELOPE, UNITS,
        QUOTED, DATETIME, DURATION, FLOAT, INTEGER,
        ATTRIBUTE,
    }
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

    LPAREN = r'\('
    RPAREN = r'\)'
    LBRACKET = r'\['
    RBRACKET = r'\]'
    COMMA = r','


    # for geometry parsing
    @_(geometry_pattern)
    def GEOMETRY(self, t):
        t.value = from_wkt(t.value)
        return t

    @_(envelope_pattern)
    def ENVELOPE(self, t):
        t.value = Envelope([
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

    ATTRIBUTE = identifier_pattern

    # remap some tokens to be confused with attributes
    ATTRIBUTE['NOT'] = NOT
    ATTRIBUTE['AND'] = AND
    ATTRIBUTE['OR'] = OR
    ATTRIBUTE['BETWEEN'] = BETWEEN
    ATTRIBUTE['LIKE'] = LIKE
    ATTRIBUTE['ILIKE'] = ILIKE
    ATTRIBUTE['IN'] = IN
    ATTRIBUTE['IS'] = IS
    ATTRIBUTE['NULL'] = NULL
    ATTRIBUTE['BEFORE'] = BEFORE
    ATTRIBUTE['AFTER'] = AFTER
    ATTRIBUTE['DURING'] = DURING
    ATTRIBUTE['INTERSECTS'] = INTERSECTS
    ATTRIBUTE['DISJOINT'] = DISJOINT
    ATTRIBUTE['CONTAINS'] = CONTAINS
    ATTRIBUTE['WITHIN'] = WITHIN
    ATTRIBUTE['TOUCHES'] = TOUCHES
    ATTRIBUTE['CROSSES'] = CROSSES
    ATTRIBUTE['OVERLAPS'] = OVERLAPS
    ATTRIBUTE['EQUALS'] = EQUALS
    ATTRIBUTE['RELATE'] = RELATE
    ATTRIBUTE['DWITHIN'] = DWITHIN
    ATTRIBUTE['BEYOND'] = BEYOND
    ATTRIBUTE['BBOX'] = BBOX

    # @_(identifier_pattern)
    # def ATTRIBUTE(self, t):
    #     # TODO
    #     # t.type = self.keyword_map.get(t.value, "ATTRIBUTE")
    #     return t

    ignore = ' \t'

    # Ignored pattern
    ignore_newline = r'\n+'

    # Extra action for newlines
    def ignore_newline(self, t):
        self.lineno += t.value.count('\n')

    def error(self, t):
        print("Illegal character '%s'" % t.value[0])
        self.index += 1
