import base64
import datetime

from pygml.v32 import parse_v32, NAMESPACE as NAMESPACE_32
from pygml.pre_v32 import parse_pre_v32, NAMESPACE as NAMESPACE_PRE_32
from pygml.v33 import parse_v33_ce, NAMESPACE as NAMESPACE_33_CE
from pygml.georss import NAMESPACE as NAMESPACE_GEORSS, parse_georss
from dateparser import parse as parse_datetime

from ... import ast
from ... import values
from ... import util
from .util import XMLParser, handle, handle_namespace, ParseInput


class FES20Parser(XMLParser):
    namespace = 'http://www.opengis.net/fes/2.0'

    @handle('Filter')
    def filter_(self, node, predicate):
        return predicate

    @handle('And')
    def and_(self, node, lhs, rhs):
        return ast.And(lhs, rhs)

    @handle('Or')
    def or_(self, node, lhs, rhs):
        return ast.Or(lhs, rhs)

    @handle('Not')
    def not_(self, node, lhs):
        return ast.Not(lhs)

    @handle('PropertyIsEqualTo')
    def property_is_equal_to(self, node, lhs, rhs):
        return ast.Equal(lhs, rhs)

    @handle('PropertyIsNotEqualTo')
    def property_is_not_equal_to(self, node, lhs, rhs):
        return ast.NotEqual(lhs, rhs)

    @handle('PropertyIsLessThan')
    def property_is_less_than(self, node, lhs, rhs):
        return ast.LessThan(lhs, rhs)

    @handle('PropertyIsGreaterThan')
    def property_is_greater_than(self, node, lhs, rhs):
        return ast.GreaterThan(lhs, rhs)

    @handle('PropertyIsLessThanOrEqualTo')
    def property_is_less_than_or_equal_to(self, node, lhs, rhs):
        return ast.LessEqual(lhs, rhs)

    @handle('PropertyIsGreaterThanOrEqualTo')
    def property_is_greater_than_or_equal_to(self, node, lhs, rhs):
        return ast.GreaterEqual(lhs, rhs)

    @handle('PropertyIsLike')
    def property_is_like(self, node, lhs, rhs):
        return ast.Like(
            lhs,
            rhs,
            wildcard=node.attrib['wildCard'],
            singlechar=node.attrib['singleChar'],
            escapechar=node.attrib['escapeChar'],
            nocase=node.attrib.get('matchCase', 'true') == 'false',
            not_=False,
        )

    @handle('PropertyIsNull')
    def property_is_null(self, node, lhs):
        return ast.IsNull(lhs, not_=False)

    # @handle('PropertyIsNil')
    # def property_is_nil(self, node, lhs, rhs):
    #     return ast...

    @handle('PropertyIsBetween')
    def property_is_between(self, node, lhs, low, high):
        return ast.Between(lhs, low, high, False)

    @handle('LowerBoundary', 'UpperBoundary')
    def boundary(self, node, expression):
        return expression

    @handle('Equals')
    def geometry_equals(self, node, lhs, rhs):
        return ast.GeometryEquals(lhs, rhs)

    @handle('Disjoint')
    def geometry_disjoint(self, node, lhs, rhs):
        return ast.GeometryDisjoint(lhs, rhs)

    @handle('Touches')
    def geometry_touches(self, node, lhs, rhs):
        return ast.GeometryTouches(lhs, rhs)

    @handle('Within')
    def geometry_within(self, node, lhs, rhs):
        return ast.GeometryWithin(lhs, rhs)

    @handle('Overlaps')
    def geometry_overlaps(self, node, lhs, rhs):
        return ast.GeometryOverlaps(lhs, rhs)

    @handle('Crosses')
    def geometry_crosses(self, node, lhs, rhs):
        return ast.GeometryCrosses(lhs, rhs)

    @handle('Intersects')
    def geometry_intersects(self, node, lhs, rhs):
        return ast.GeometryIntersects(lhs, rhs)

    @handle('Contains')
    def geometry_contains(self, node, lhs, rhs):
        return ast.GeometryContains(lhs, rhs)

    @handle('DWithin')
    def distance_within(self, node, lhs, rhs, distance_and_units):
        distance, units = distance_and_units
        return ast.DistanceWithin(lhs, rhs, distance, units)

    @handle('Beyond')
    def distance_beyond(self, node, lhs, rhs, distance_and_units):
        distance, units = distance_and_units
        return ast.DistanceBeyond(lhs, rhs, distance, units)

    @handle('Distance')
    def distance(self, node):
        return (float(node.text), node.attrib['uom'])

    @handle('BBOX')
    def geometry_bbox(self, node, lhs, rhs):
        pass

    @handle('After')
    def time_after(self, node, lhs, rhs):
        return ast.TimeAfter(lhs, rhs)

    @handle('Before')
    def time_before(self, node, lhs, rhs):
        return ast.TimeBefore(lhs, rhs)

    @handle('Begins')
    def time_begins(self, node, lhs, rhs):
        return ast.TimeBegins(lhs, rhs)

    @handle('BegunBy')
    def time_begun_by(self, node, lhs, rhs):
        return ast.TimeBegunBy(lhs, rhs)

    @handle('TContains')
    def time_contains(self, node, lhs, rhs):
        return ast.TimeContains(lhs, rhs)

    @handle('During')
    def time_during(self, node, lhs, rhs):
        return ast.TimeDuring(lhs, rhs)

    @handle('TEquals')
    def time_equals(self, node, lhs, rhs):
        return ast.TimeEquals(lhs, rhs)

    @handle('TOverlaps')
    def time_overlaps(self, node, lhs, rhs):
        return ast.TimeOverlaps(lhs, rhs)

    @handle('Meets')
    def time_meets(self, node, lhs, rhs):
        return ast.TimeMeets(lhs, rhs)

    @handle('OverlappedBy')
    def time_overlapped_by(self, node, lhs, rhs):
        return ast.TimeOverlappedBy(lhs, rhs)

    @handle('MetBy')
    def time_met_by(self, node, lhs, rhs):
        return ast.TimeMetBy(lhs, rhs)

    @handle('Ends')
    def time_ends(self, node, lhs, rhs):
        return ast.TimeEnds(lhs, rhs)

    @handle('EndedBy')
    def time_ended_by(self, node, lhs, rhs):
        return ast.TimeEndedBy(lhs, rhs)

    @handle('ValueReference')
    def value_reference(self, node):
        return ast.Attribute(node.text)

    @handle('Literal')
    def literal(self, node):
        type_ = node.get('type').rpartition(':')[2]
        value = node.text
        if type_ == 'boolean':
            return value.lower() == 'true'
        elif type_ in ('byte', 'int', 'integer', 'long', 'negativeInteger',
                       'nonNegativeInteger', 'nonPositiveInteger',
                       'positiveInteger', 'short', 'unsignedByte',
                       'unsignedInt', 'unsignedLong', 'unsignedShort'):
            return int(value)
        elif type_ in ('decimal', 'double', 'float'):
            return float(value)
        elif type_ == 'base64Binary':
            return base64.b64decode(value)
        elif type_ == 'hexBinary':
            return bytes.fromhex(value)
        elif type_ == 'date':
            return datetime.date.fromisoformat(value)
        elif type_ == 'dateTime':
            return parse_datetime(value)
        elif type_ == 'duration':
            return util.parse_duration(value)

        # return to string
        return value

    @handle_namespace(NAMESPACE_PRE_32, False)
    def gml_pre_32(self, node):
        return values.Geometry(parse_pre_v32(node))

    @handle_namespace(NAMESPACE_32, False)
    def gml_32(self, node):
        return values.Geometry(parse_v32(node))

    @handle_namespace(NAMESPACE_33_CE, False)
    def gml_33_ce(self, node):
        return values.Geometry(parse_v33_ce(node))

    @handle_namespace(NAMESPACE_GEORSS, False)
    def georss(self, node):
        return values.Geometry(parse_georss(node))


def parse(input_: ParseInput) -> ast.Node:
    return FES20Parser().parse(input_)
