import base64
import datetime

from pygml.georss import NAMESPACE as NAMESPACE_GEORSS
from pygml.georss import parse_georss
from pygml.pre_v32 import NAMESPACE as NAMESPACE_PRE_32
from pygml.pre_v32 import NSMAP as NSMAP_PRE_32
from pygml.pre_v32 import parse_pre_v32
from pygml.v32 import NAMESPACE as NAMESPACE_32
from pygml.v32 import NSMAP as NSMAP_32
from pygml.v32 import parse_v32
from pygml.v33 import NAMESPACE as NAMESPACE_33_CE
from pygml.v33 import parse_v33_ce

from ... import ast, values
from ...util import parse_datetime, parse_duration
from .gml import is_temporal, parse_temporal
from .util import Element, XMLParser, handle, handle_namespace


class FESBaseParser(XMLParser):
    @handle("Filter")
    def filter_(self, node: Element, predicate):
        return predicate

    @handle("And")
    def and_(self, node: Element, lhs, rhs):
        return ast.And(lhs, rhs)

    @handle("Or")
    def or_(self, node: Element, lhs, rhs):
        return ast.Or(lhs, rhs)

    @handle("Not")
    def not_(self, node: Element, lhs):
        return ast.Not(lhs)

    @handle("PropertyIsEqualTo")
    def property_is_equal_to(self, node: Element, lhs, rhs):
        return ast.Equal(lhs, rhs)

    @handle("PropertyIsNotEqualTo")
    def property_is_not_equal_to(self, node: Element, lhs, rhs):
        return ast.NotEqual(lhs, rhs)

    @handle("PropertyIsLessThan")
    def property_is_less_than(self, node: Element, lhs, rhs):
        return ast.LessThan(lhs, rhs)

    @handle("PropertyIsGreaterThan")
    def property_is_greater_than(self, node: Element, lhs, rhs):
        return ast.GreaterThan(lhs, rhs)

    @handle("PropertyIsLessThanOrEqualTo")
    def property_is_less_than_or_equal_to(self, node: Element, lhs, rhs):
        return ast.LessEqual(lhs, rhs)

    @handle("PropertyIsGreaterThanOrEqualTo")
    def property_is_greater_than_or_equal_to(self, node: Element, lhs, rhs):
        return ast.GreaterEqual(lhs, rhs)

    @handle("PropertyIsLike")
    def property_is_like(self, node: Element, lhs, rhs):
        return ast.Like(
            lhs,
            rhs,
            wildcard=node.attrib["wildCard"],
            singlechar=node.attrib["singleChar"],
            escapechar=node.attrib.get("escape", node.attrib["escapeChar"]),
            nocase=node.attrib.get("matchCase", "true") == "false",
            not_=False,
        )

    @handle("PropertyIsNull")
    def property_is_null(self, node: Element, lhs):
        return ast.IsNull(lhs, not_=False)

    @handle("PropertyIsBetween")
    def property_is_between(self, node: Element, lhs, low, high):
        return ast.Between(lhs, low, high, False)

    @handle("LowerBoundary", "UpperBoundary")
    def boundary(self, node: Element, expression):
        return expression

    @handle("BBOX")
    def geometry_bbox(self, node: Element, *args):
        if len(args) == 2:
            # PropertyName, Envelope
            lhs, rhs = args
        else:
            # No PropertyName
            lhs = None
            rhs = args[0]
        return ast.Not(ast.GeometryDisjoint(lhs, rhs))

    @handle("Equals")
    def geometry_equals(self, node: Element, lhs, rhs):
        return ast.GeometryEquals(lhs, rhs)

    @handle("Disjoint")
    def geometry_disjoint(self, node: Element, lhs, rhs):
        return ast.GeometryDisjoint(lhs, rhs)

    @handle("Touches")
    def geometry_touches(self, node: Element, lhs, rhs):
        return ast.GeometryTouches(lhs, rhs)

    @handle("Within")
    def geometry_within(self, node: Element, lhs, rhs):
        return ast.GeometryWithin(lhs, rhs)

    @handle("Overlaps")
    def geometry_overlaps(self, node: Element, lhs, rhs):
        return ast.GeometryOverlaps(lhs, rhs)

    @handle("Crosses")
    def geometry_crosses(self, node: Element, lhs, rhs):
        return ast.GeometryCrosses(lhs, rhs)

    @handle("Intersects")
    def geometry_intersects(self, node: Element, lhs, rhs):
        return ast.GeometryIntersects(lhs, rhs)

    @handle("Contains")
    def geometry_contains(self, node: Element, lhs, rhs):
        return ast.GeometryContains(lhs, rhs)

    @handle("DWithin")
    def distance_within(self, node: Element, lhs, rhs, distance_and_units):
        distance, units = distance_and_units
        return ast.DistanceWithin(lhs, rhs, distance, units)

    @handle("Beyond")
    def distance_beyond(self, node: Element, lhs, rhs, distance_and_units):
        distance, units = distance_and_units
        return ast.DistanceBeyond(lhs, rhs, distance, units)

    @handle("Distance")
    def distance(self, node: Element):
        return (float(node.text), node.attrib["uom"])

    @handle("PropertyName")
    def property_name(self, node):
        return ast.Attribute(node.text)

    @handle("ValueReference")
    def value_reference(self, node):
        return ast.Attribute(node.text)

    @handle("Literal")
    def literal(self, node):
        type_ = node.get("type", "").rpartition(":")[2]
        value = node.text
        if type_ == "boolean":
            return value.lower() == "true"
        elif type_ in (
            "byte",
            "int",
            "integer",
            "long",
            "negativeInteger",
            "nonNegativeInteger",
            "nonPositiveInteger",
            "positiveInteger",
            "short",
            "unsignedByte",
            "unsignedInt",
            "unsignedLong",
            "unsignedShort",
        ):
            return int(value)
        elif type_ in ("decimal", "double", "float"):
            return float(value)
        elif type_ == "base64Binary":
            return base64.b64decode(value)
        elif type_ == "hexBinary":
            return bytes.fromhex(value)
        elif type_ == "date":
            return datetime.date.fromisoformat(value)
        elif type_ == "dateTime":
            return parse_datetime(value)
        elif type_ == "duration":
            return parse_duration(value)

        # return to string
        return value

    @handle_namespace(NAMESPACE_PRE_32, False)
    def gml_pre_32(self, node: Element):
        if is_temporal(node):
            return parse_temporal(node, NSMAP_PRE_32)

        return values.Geometry(parse_pre_v32(node))

    @handle_namespace(NAMESPACE_32, False)
    def gml_32(self, node: Element):
        if is_temporal(node):
            return parse_temporal(node, NSMAP_32)

        return values.Geometry(parse_v32(node))

    @handle_namespace(NAMESPACE_33_CE, False)
    def gml_33_ce(self, node: Element):
        return values.Geometry(parse_v33_ce(node))

    @handle_namespace(NAMESPACE_GEORSS, False)
    def georss(self, node: Element):
        return values.Geometry(parse_georss(node))
