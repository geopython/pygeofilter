# ------------------------------------------------------------------------------
#
# Project: pygeofilter <https://github.com/geopython/pygeofilter>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2019 EOX IT Services GmbH
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

from dataclasses import dataclass
from enum import Enum
from typing import ClassVar, List, Optional, Union

from . import values

AstType = Union["Node", values.ValueType, list]
ScalarAstType = Union["Node", int, float]
SpatialAstType = Union["Node", values.SpatialValueType]
TemporalAstType = Union["Node", values.TemporalValueType]
ArrayAstType = Union["Node", List[AstType]]


class Node:
    """The base class for all other nodes to display the AST of CQL."""

    inline: bool = False

    def get_sub_nodes(self) -> List[AstType]:
        """Get a list of sub-node of this node.

        :return: a list of all sub-nodes
        :rtype: list[Node]
        """
        return []

    def get_template(self) -> str:
        """Get a template string (using the ``.format`` method)
        to represent the current node and sub-nodes. The template string
        must provide a template replacement for each sub-node reported by
        :func:`~pygeofilter.ast.Node.get_sub_nodes`.

        :return: the template to render
        """
        raise NotImplementedError

    def __eq__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            return False

        self_dict = {
            k: v.__geo_interface__ if hasattr(v, "__geo_interface__") else v
            for k, v in self.__dict__.items()
        }
        other_dict = {
            k: v.__geo_interface__ if hasattr(v, "__geo_interface__") else v
            for k, v in other.__dict__.items()
        }
        return self_dict == other_dict


class Condition(Node):
    """The base class for all nodes representing a condition"""

    pass


class Not(Condition):
    """
    Node class to represent a negation condition.

    :ivar sub_node: the condition node to be negated
    :type sub_node: Node
    """

    def __init__(self, sub_node: Node):
        self.sub_node = sub_node

    def get_sub_nodes(self) -> List[AstType]:
        """Returns the sub-node for the negated condition."""
        return [self.sub_node]

    def get_template(self) -> str:
        return "NOT {}"


class CombinationOp(Enum):
    AND = "AND"
    OR = "OR"


@dataclass
class Combination(Condition):
    """Node class to represent a condition to combine two other conditions
    using either AND or OR.
    """

    lhs: Node
    rhs: Node
    op: ClassVar[CombinationOp]

    def get_sub_nodes(self) -> List[AstType]:
        return [self.lhs, self.rhs]

    def get_template(self) -> str:
        return f"{{}} {self.op.name} {{}}"

    @classmethod
    def from_items(cls, first, *rest) -> Node:
        result = first
        for item in rest:
            result = cls(result, item)
        return result


@dataclass
class And(Combination):
    op: ClassVar[CombinationOp] = CombinationOp.AND


@dataclass
class Or(Combination):
    op: ClassVar[CombinationOp] = CombinationOp.OR


class Predicate(Node):
    """The base class for all nodes representing a predicate"""

    pass


class ComparisonOp(Enum):
    EQ = "="
    NE = "<>"
    LT = "<"
    LE = "<="
    GT = ">"
    GE = ">="


@dataclass
class Comparison(Predicate):
    """Node class to represent a comparison predicate: to compare two
    expressions using a comparison operation.
    """

    lhs: ScalarAstType
    rhs: ScalarAstType
    op: ClassVar[ComparisonOp]

    def get_sub_nodes(self) -> List[AstType]:
        return [self.lhs, self.rhs]

    def get_template(self) -> str:
        return f"{{}} {self.op.value} {{}}"


@dataclass
class Equal(Comparison):
    op: ClassVar[ComparisonOp] = ComparisonOp.EQ


@dataclass
class NotEqual(Comparison):
    op: ClassVar[ComparisonOp] = ComparisonOp.NE


@dataclass
class LessThan(Comparison):
    op: ClassVar[ComparisonOp] = ComparisonOp.LT


@dataclass
class LessEqual(Comparison):
    op: ClassVar[ComparisonOp] = ComparisonOp.LE


@dataclass
class GreaterThan(Comparison):
    op: ClassVar[ComparisonOp] = ComparisonOp.GT


@dataclass
class GreaterEqual(Comparison):
    op: ClassVar[ComparisonOp] = ComparisonOp.GE


@dataclass
class Between(Predicate):
    """Node class to represent a BETWEEN predicate: to check whether an
    expression value within a range.
    """

    lhs: Node
    low: ScalarAstType
    high: ScalarAstType
    not_: bool

    def get_sub_nodes(self) -> List[AstType]:
        return [self.lhs, self.low, self.high]

    def get_template(self) -> str:
        return f"{{}} {'NOT ' if self.not_ else ''}BETWEEN {{}} AND {{}}"


@dataclass
class Like(Predicate):
    """Node class to represent a wildcard sting matching predicate."""

    lhs: Node
    pattern: str
    nocase: bool
    wildcard: str
    singlechar: str
    escapechar: str
    not_: bool

    def get_sub_nodes(self) -> List[AstType]:
        return [self.lhs]

    def get_template(self) -> str:
        return (
            f"{{}} {'NOT ' if self.not_ else ''}"
            f"{'I' if self.nocase else ''}LIKE '{self.pattern}'"
            # TODO wildcard, singlechar, escapechar
        )


@dataclass
class In(Predicate):
    """Node class to represent list checking predicate."""

    lhs: AstType
    sub_nodes: List[AstType]
    not_: bool

    def get_sub_nodes(self) -> List[AstType]:
        return [self.lhs] + list(self.sub_nodes)

    def get_template(self) -> str:
        return (
            f"{{}} {'NOT ' if self.not_ else ''}IN "
            f"{', '.join(['{}'] * len(self.sub_nodes))}"
        )


@dataclass
class IsNull(Predicate):
    """Node class to represent null check predicate."""

    lhs: AstType
    not_: bool

    def get_sub_nodes(self) -> List[AstType]:
        return [self.lhs]

    def get_template(self) -> str:
        return f"{{}} IS {('NOT ' if self.not_ else '')}NULL"


@dataclass
class Exists(Predicate):
    lhs: AstType
    not_: bool

    def get_sub_nodes(self) -> List[AstType]:
        return [self.lhs]

    def get_template(self) -> str:
        return f"{{}} {('DOES-NOT-EXIST' if self.not_ else 'EXISTS')}"


@dataclass
class Include(Predicate):
    not_: bool

    def get_template(self) -> str:
        return "EXCLUDE" if self.not_ else "INCLUDE"


# https://portal.ogc.org/files/96288#enhanced-temporal-operators

# BEFORE                <======>     <----->    AFTER
# MEETS                         <---------->    METBY
# TOVERLAPS                 <-------------->    OVERLAPPEDBY
# BEGINS                <------------------>    BEGUNBY
# DURING            <---------------------->    TCONTAINS
# TENDS             <---------->                ENDEDBY
# TEQUALS               <------>                TEQUALS
# DISJOINT: If a proper interval T1 is intervalDisjoint another proper
#   interval T2,then the beginning of T1 is after the end of T2, or the end of
#   T1 is before the beginning of T2, i.e. the intervals do not overlap in any
#   way, but their ordering relationship is not known.

# https://github.com/geotools/geotools/blob/main/modules/library/cql/ECQL.md#temporal-predicate
# BEFORE_OR_DURING  <----->
# DURING_OR_AFTER           <----->


class TemporalComparisonOp(Enum):
    DISJOINT = "DISJOINT"
    AFTER = "AFTER"
    BEFORE = "BEFORE"
    BEGINS = "BEGINS"
    BEGUNBY = "BEGUNBY"
    TCONTAINS = "TCONTAINS"
    DURING = "DURING"
    ENDEDBY = "ENDEDBY"
    ENDS = "ENDS"
    TEQUALS = "TEQUALS"
    MEETS = "MEETS"
    METBY = "METBY"
    TOVERLAPS = "TOVERLAPS"
    OVERLAPPEDBY = "OVERLAPPEDBY"

    BEFORE_OR_DURING = "BEFORE OR DURING"
    DURING_OR_AFTER = "DURING OR AFTER"


@dataclass
class TemporalPredicate(Predicate):
    """Node class to represent temporal predicate."""

    lhs: TemporalAstType
    rhs: TemporalAstType
    op: ClassVar[TemporalComparisonOp]

    def get_sub_nodes(self) -> List[AstType]:
        return [self.lhs, self.rhs]

    def get_template(self) -> str:
        return f"{{}} {self.op} {{}}"


@dataclass
class TimeDisjoint(TemporalPredicate):
    op: ClassVar[TemporalComparisonOp] = TemporalComparisonOp.DISJOINT


@dataclass
class TimeAfter(TemporalPredicate):
    op: ClassVar[TemporalComparisonOp] = TemporalComparisonOp.AFTER


@dataclass
class TimeBefore(TemporalPredicate):
    op: ClassVar[TemporalComparisonOp] = TemporalComparisonOp.BEFORE


@dataclass
class TimeBegins(TemporalPredicate):
    op: ClassVar[TemporalComparisonOp] = TemporalComparisonOp.BEGINS


@dataclass
class TimeBegunBy(TemporalPredicate):
    op: ClassVar[TemporalComparisonOp] = TemporalComparisonOp.BEGUNBY


@dataclass
class TimeContains(TemporalPredicate):
    op: ClassVar[TemporalComparisonOp] = TemporalComparisonOp.TCONTAINS


@dataclass
class TimeDuring(TemporalPredicate):
    op: ClassVar[TemporalComparisonOp] = TemporalComparisonOp.DURING


@dataclass
class TimeEndedBy(TemporalPredicate):
    op: ClassVar[TemporalComparisonOp] = TemporalComparisonOp.ENDEDBY


@dataclass
class TimeEnds(TemporalPredicate):
    op: ClassVar[TemporalComparisonOp] = TemporalComparisonOp.ENDS


@dataclass
class TimeEquals(TemporalPredicate):
    op: ClassVar[TemporalComparisonOp] = TemporalComparisonOp.TEQUALS


@dataclass
class TimeMeets(TemporalPredicate):
    op: ClassVar[TemporalComparisonOp] = TemporalComparisonOp.MEETS


@dataclass
class TimeMetBy(TemporalPredicate):
    op: ClassVar[TemporalComparisonOp] = TemporalComparisonOp.METBY


@dataclass
class TimeOverlaps(TemporalPredicate):
    op: ClassVar[TemporalComparisonOp] = TemporalComparisonOp.TOVERLAPS


@dataclass
class TimeOverlappedBy(TemporalPredicate):
    op: ClassVar[TemporalComparisonOp] = TemporalComparisonOp.OVERLAPPEDBY


@dataclass
class TimeBeforeOrDuring(TemporalPredicate):
    op: ClassVar[TemporalComparisonOp] = TemporalComparisonOp.BEFORE_OR_DURING


@dataclass
class TimeDuringOrAfter(TemporalPredicate):
    op: ClassVar[TemporalComparisonOp] = TemporalComparisonOp.DURING_OR_AFTER


class ArrayComparisonOp(Enum):
    AEQUALS = "AEQUALS"
    ACONTAINS = "ACONTAINS"
    ACONTAINEDBY = "ACONTAINEDBY"
    AOVERLAPS = "AOVERLAPS"


@dataclass
class ArrayPredicate(Predicate):
    """Node class to represent array predicates."""

    lhs: ArrayAstType
    rhs: ArrayAstType
    op: ClassVar[ArrayComparisonOp]

    def get_sub_nodes(self) -> List[AstType]:
        return [self.lhs, self.rhs]

    def get_template(self) -> str:
        return f"{{}} {self.op} {{}}"


@dataclass
class ArrayEquals(ArrayPredicate):
    op: ClassVar[ArrayComparisonOp] = ArrayComparisonOp.AEQUALS


@dataclass
class ArrayContains(ArrayPredicate):
    op: ClassVar[ArrayComparisonOp] = ArrayComparisonOp.ACONTAINS


@dataclass
class ArrayContainedBy(ArrayPredicate):
    op: ClassVar[ArrayComparisonOp] = ArrayComparisonOp.ACONTAINEDBY


@dataclass
class ArrayOverlaps(ArrayPredicate):
    op: ClassVar[ArrayComparisonOp] = ArrayComparisonOp.AOVERLAPS


class SpatialComparisonOp(Enum):
    INTERSECTS = "INTERSECTS"
    DISJOINT = "DISJOINT"
    CONTAINS = "CONTAINS"
    WITHIN = "WITHIN"
    TOUCHES = "TOUCHES"
    CROSSES = "CROSSES"
    OVERLAPS = "OVERLAPS"
    EQUALS = "EQUALS"


@dataclass
class SpatialComparisonPredicate(Predicate):
    """Node class to represent spatial relation predicate."""

    lhs: SpatialAstType
    rhs: SpatialAstType
    op: ClassVar[SpatialComparisonOp]

    def get_sub_nodes(self) -> List[AstType]:
        return [self.lhs, self.rhs]

    def get_template(self) -> str:
        return f"{self.op.name}({{}}, {{}})"


@dataclass
class GeometryIntersects(SpatialComparisonPredicate):
    op: ClassVar[SpatialComparisonOp] = SpatialComparisonOp.INTERSECTS


@dataclass
class GeometryDisjoint(SpatialComparisonPredicate):
    op: ClassVar[SpatialComparisonOp] = SpatialComparisonOp.DISJOINT


@dataclass
class GeometryContains(SpatialComparisonPredicate):
    op: ClassVar[SpatialComparisonOp] = SpatialComparisonOp.CONTAINS


@dataclass
class GeometryWithin(SpatialComparisonPredicate):
    op: ClassVar[SpatialComparisonOp] = SpatialComparisonOp.WITHIN


@dataclass
class GeometryTouches(SpatialComparisonPredicate):
    op: ClassVar[SpatialComparisonOp] = SpatialComparisonOp.TOUCHES


@dataclass
class GeometryCrosses(SpatialComparisonPredicate):
    op: ClassVar[SpatialComparisonOp] = SpatialComparisonOp.CROSSES


@dataclass
class GeometryOverlaps(SpatialComparisonPredicate):
    op: ClassVar[SpatialComparisonOp] = SpatialComparisonOp.OVERLAPS


@dataclass
class GeometryEquals(SpatialComparisonPredicate):
    op: ClassVar[SpatialComparisonOp] = SpatialComparisonOp.EQUALS


@dataclass
class Relate(Predicate):
    """Node class to represent spatial relation predicate."""

    lhs: SpatialAstType
    rhs: SpatialAstType
    pattern: str

    def get_sub_nodes(self) -> List[AstType]:
        return [self.lhs, self.rhs]

    def get_template(self) -> str:
        return f"RELATE({{}}, {{}}, '{self.pattern}')"


class SpatialDistanceOp(Enum):
    DWITHIN = "DWITHIN"
    BEYOND = "BEYOND"


@dataclass
class SpatialDistancePredicate(Predicate):
    """Node class to represent spatial relation predicate."""

    lhs: SpatialAstType
    rhs: SpatialAstType
    distance: float
    units: str
    op: ClassVar[SpatialDistanceOp]

    def get_sub_nodes(self) -> List[AstType]:
        return [self.lhs, self.rhs]

    def get_template(self) -> str:
        return f"{self.op.name}({{}}, {{}}, {self.distance}, '{self.units}')"


@dataclass
class DistanceWithin(SpatialDistancePredicate):
    op: ClassVar[SpatialDistanceOp] = SpatialDistanceOp.DWITHIN


@dataclass
class DistanceBeyond(SpatialDistancePredicate):
    op: ClassVar[SpatialDistanceOp] = SpatialDistanceOp.BEYOND


@dataclass
class BBox(Predicate):
    """Node class to represent a bounding box predicate."""

    lhs: SpatialAstType
    minx: float
    miny: float
    maxx: float
    maxy: float
    crs: Optional[str] = None

    def get_sub_nodes(self) -> List[AstType]:
        return [self.lhs]

    def get_template(self) -> str:
        return (
            f"BBOX({{}}, {self.minx}, {self.miny}, {self.maxx}, "
            f"{self.maxy}, {repr(self.crs)})"
        )


class Expression(Node):
    """The base class for all nodes representing expressions"""

    pass


class Attribute(Expression):
    """Node class to represent attribute lookup expressions

    :ivar name: the name of the attribute to be accessed
    :type name: str
    """

    inline = True

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"ATTRIBUTE {self.name}"


class ArithmeticOp(Enum):
    ADD = "+"
    SUB = "-"
    MUL = "*"
    DIV = "/"


@dataclass
class Arithmetic(Expression):
    """Node class to represent arithmetic operation expressions with two
    sub-expressions and an operator.
    """

    lhs: ScalarAstType
    rhs: ScalarAstType
    op: ClassVar[ArithmeticOp]

    def get_sub_nodes(self) -> List[AstType]:
        return [self.lhs, self.rhs]

    def get_template(self) -> str:
        return f"{{}} {self.op.value} {{}}"


@dataclass
class Add(Arithmetic):
    op: ClassVar[ArithmeticOp] = ArithmeticOp.ADD


@dataclass
class Sub(Arithmetic):
    op: ClassVar[ArithmeticOp] = ArithmeticOp.SUB


@dataclass
class Mul(Arithmetic):
    op: ClassVar[ArithmeticOp] = ArithmeticOp.MUL


@dataclass
class Div(Arithmetic):
    op: ClassVar[ArithmeticOp] = ArithmeticOp.DIV


@dataclass
class Function(Expression):
    """Node class to represent function invocations."""

    name: str
    arguments: List[AstType]

    def get_sub_nodes(self) -> List[AstType]:
        return self.arguments

    def get_template(self) -> str:
        return f"{self.name} ({', '.join(['{}'] * len(self.arguments))})"


def indent(text: str, amount: int, ch: str = " ") -> str:
    padding = amount * ch
    return "".join(padding + line for line in text.splitlines(True))


def get_repr(node: Node, indent_amount: int = 0, indent_incr: int = 4) -> str:
    """Get a debug representation of the given AST node. ``indent_amount``
    and ``indent_incr`` are for the recursive call and don't need to be
    passed.
    """
    sub_nodes = node.get_sub_nodes()
    template = node.get_template()

    args = []
    for sub_node in sub_nodes:
        if isinstance(sub_node, Node) and not sub_node.inline:
            args.append(
                "(\n{}\n)".format(
                    indent(
                        get_repr(sub_node, indent_amount + indent_incr, indent_incr),
                        indent_amount + indent_incr,
                    )
                )
            )
        else:
            args.append(repr(sub_node))

    return template.format(*args)
