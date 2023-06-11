import base64
import datetime

from ... import ast
from ...util import parse_datetime, parse_duration
from .base import FESBaseParser
from .util import Element, ParseInput, handle


class FES20Parser(FESBaseParser):
    namespace = "http://www.opengis.net/fes/2.0"

    # @handle('PropertyIsNil')
    # def property_is_nil(self, node: Element, lhs, rhs):
    #     return ast...

    @handle("After")
    def time_after(self, node: Element, lhs, rhs):
        return ast.TimeAfter(lhs, rhs)

    @handle("Before")
    def time_before(self, node: Element, lhs, rhs):
        return ast.TimeBefore(lhs, rhs)

    @handle("Begins")
    def time_begins(self, node: Element, lhs, rhs):
        return ast.TimeBegins(lhs, rhs)

    @handle("BegunBy")
    def time_begun_by(self, node: Element, lhs, rhs):
        return ast.TimeBegunBy(lhs, rhs)

    @handle("TContains")
    def time_contains(self, node: Element, lhs, rhs):
        return ast.TimeContains(lhs, rhs)

    @handle("During")
    def time_during(self, node: Element, lhs, rhs):
        return ast.TimeDuring(lhs, rhs)

    @handle("TEquals")
    def time_equals(self, node: Element, lhs, rhs):
        return ast.TimeEquals(lhs, rhs)

    @handle("TOverlaps")
    def time_overlaps(self, node: Element, lhs, rhs):
        return ast.TimeOverlaps(lhs, rhs)

    @handle("Meets")
    def time_meets(self, node: Element, lhs, rhs):
        return ast.TimeMeets(lhs, rhs)

    @handle("OverlappedBy")
    def time_overlapped_by(self, node: Element, lhs, rhs):
        return ast.TimeOverlappedBy(lhs, rhs)

    @handle("MetBy")
    def time_met_by(self, node: Element, lhs, rhs):
        return ast.TimeMetBy(lhs, rhs)

    @handle("Ends")
    def time_ends(self, node: Element, lhs, rhs):
        return ast.TimeEnds(lhs, rhs)

    @handle("EndedBy")
    def time_ended_by(self, node: Element, lhs, rhs):
        return ast.TimeEndedBy(lhs, rhs)

    @handle("ValueReference")
    def value_reference(self, node: Element):
        return ast.Attribute(node.text)

    @handle("Literal")
    def literal(self, node: Element):
        type_ = node.get("type").rpartition(":")[2]
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


def parse(input_: ParseInput) -> ast.Node:
    return FES20Parser().parse(input_)
