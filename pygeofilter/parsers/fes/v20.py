from ... import ast
from .util import XMLParser, handle, ParseInput
from .gml import GML32ParserMixIn


class FES20Parser(GML32ParserMixIn, XMLParser):
    namespace = 'http://www.opengis.net/fes/2.0'

    @handle('Filter')
    def filter_(self, node, predicate):
        return predicate

    @handle('PropertyIsEqualTo')
    def property_is_equal_to(self, node, lhs, rhs):
        return ast.Equal(lhs, rhs)

    @handle('PropertyIsNotEqualTo')
    def property_is_not_equal_to(self, node, lhs, rhs):
        return ast.NotEqual

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
        return ast.IsNull(lhs)

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

    # TODO: temporal predicates

    @handle('ValueReference')
    def value_reference(self, node):
        return ast.Attribute(node.text)


def parse(input_: ParseInput) -> ast.Node:
    return FES20Parser().parse(input_)
