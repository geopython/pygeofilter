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

"""
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Optional


class Node:
    """ The base class for all other nodes to display the AST of CQL.
    """
    inline = False

    def get_sub_nodes(self) -> List['Node']:
        """ Get a list of sub-node of this node.

            :return: a list of all sub-nodes
            :rtype: list[Node]
        """
        raise NotImplementedError

    def get_template(self) -> str:
        """ Get a template string (using the ``.format`` method)
            to represent the current node and sub-nodes. The template string
            must provide a template replacement for each sub-node reported by
            :func:`~pygeofilter.ast.Node.get_sub_nodes`.

            :return: the template to render
        """
        raise NotImplementedError

    def __eq__(self, other) -> bool:
        if type(self) != type(other):
            return False

        self_dict = {
            k: v.__geo_interface__ if hasattr(v, '__geo_interface__') else v
            for k, v in self.__dict__.items()
        }
        other_dict = {
            k: v.__geo_interface__ if hasattr(v, '__geo_interface__') else v
            for k, v in other.__dict__.items()
        }
        return self_dict == other_dict


class ConditionNode(Node):
    """ The base class for all nodes representing a condition
    """
    pass


class NotConditionNode(ConditionNode):
    """
    Node class to represent a negation condition.

    :ivar sub_node: the condition node to be negated
    :type sub_node: Node
    """

    def __init__(self, sub_node):
        self.sub_node = sub_node

    def get_sub_nodes(self) -> List[Node]:
        """ Returns the sub-node for the negated condition. """
        return [self.sub_node]

    def get_template(self):
        return "NOT {}"


class CombinationOp(Enum):
    AND = "AND"
    OR = "OR"


@dataclass
class CombinationConditionNode(ConditionNode):
    """ Node class to represent a condition to combine two other conditions
        using either AND or OR.
    """

    lhs: Node
    rhs: Node
    op: CombinationOp

    def get_sub_nodes(self):
        return [self.lhs, self.rhs]

    def get_template(self):
        return f"{{}} {self.op.name} {{}}"


class PredicateNode(Node):
    """ The base class for all nodes representing a predicate
    """
    pass


class ComparisonOp(Enum):
    EQ = '='
    NE = '<>'
    LT = '<'
    LE = '<='
    GT = '>'
    GE = '>='


@dataclass
class ComparisonPredicateNode(PredicateNode):
    """ Node class to represent a comparison predicate: to compare two
        expressions using a comparison operation.
    """

    lhs: Node
    rhs: Node
    op: ComparisonOp

    def get_sub_nodes(self):
        return [self.lhs, self.rhs]

    def get_template(self):
        return f"{{}} {self.op} {{}}"


@dataclass
class BetweenPredicateNode(PredicateNode):
    """ Node class to represent a BETWEEN predicate: to check whether an
        expression value within a range.
    """

    lhs: Node
    low: Node
    high: Node
    not_: bool

    def get_sub_nodes(self):
        return [self.lhs, self.low, self.high]

    def get_template(self):
        return f"%s {'NOT ' if self.not_ else ''}BETWEEN {{}} AND {{}}"


@dataclass
class LikePredicateNode(PredicateNode):
    """ Node class to represent a wildcard sting matching predicate.
    """

    lhs: Node
    pattern: str
    nocase: bool
    wildcard: str
    singlechar: str
    escapechar: str
    not_: bool

    def get_sub_nodes(self):
        return [self.lhs]

    def get_template(self):
        return (
            f"%{{}} {'NOT ' if self.not_ else ''}"
            f"{'I' if self.nocase else ''}LIKE '{self.pattern}'"
            # TODO wildcard, singlechar, escapechar
        )


@dataclass
class InPredicateNode(PredicateNode):
    """ Node class to represent list checking predicate.
    """
    lhs: Node
    sub_nodes: List[Node]
    not_: bool

    def get_sub_nodes(self):
        return [self.lhs] + list(self.sub_nodes)

    def get_template(self):
        return (
            f"{{}} {'NOT ' if self.not_ else ''}IN "
            f"{', '.join(['{}'] * len(self.sub_nodes))}"
        )


@dataclass
class NullPredicateNode(PredicateNode):
    """ Node class to represent null check predicate.
    """

    lhs: Node
    not_: bool

    def get_sub_nodes(self):
        return [self.lhs]

    def get_template(self):
        return f"{{}} IS {('NOT ' if self.not_ else '')}NULL"


# class ExistsPredicateNode(PredicateNode):
#     pass

# http://docs.opengeospatial.org/DRAFTS/19-079.html#enhanced-temporal-operators

# BEFORE                <======>     <----->    AFTER
# MEETS                         <---------->    METBY
# TOVERLAPS                 <-------------->    OVERLAPPEDBY
# BEGINS                <------------------>    BEGUNBY
# DURING            <---------------------->    TCONTAINS
# TENDS             <---------->                ENDEDBY
# TEQUALS               <------>                TEQUALS

# https://github.com/geotools/geotools/blob/main/modules/library/cql/ECQL.md#temporal-predicate
# BEFORE_OR_DURING  <----->
# DURING_OR_AFTER           <----->

class TemporalComparisonOp(Enum):
    AFTER = 'AFTER'
    BEFORE = 'BEFORE'
    BEGINS = 'BEGINS'
    BEGUNBY = 'BEGUNBY'
    TCONTAINS = 'TCONTAINS'
    DURING = 'DURING'
    ENDEDBY = 'ENDEDBY'
    ENDS = 'ENDS'
    TEQUALS = 'TEQUALS'
    MEETS = 'MEETS'
    METBY = 'METBY'
    TOVERLAPS = 'TOVERLAPS'
    OVERLAPPEDBY = 'OVERLAPPEDBY'

    BEFORE_OR_DURING = 'BEFORE OR DURING'
    DURING_OR_AFTER = 'DURING OR AFTER'


@dataclass
class TemporalPredicateNode(PredicateNode):
    """ Node class to represent temporal predicate.
    """

    lhs: Node
    rhs: Node
    op: TemporalComparisonOp

    def get_sub_nodes(self):
        return [self.lhs, self.rhs]

    def get_template(self):
        return f"{{}} {self.op} {{}}"


class SpatialdPredicateNode(PredicateNode):
    pass


class SpatialComparisonOp(Enum):
    INTERSECTS = 'INTERSECTS'
    DISJOINT = 'DISJOINT'
    CONTAINS = 'CONTAINS'
    WITHIN = 'WITHIN'
    TOUCHES = 'TOUCHES'
    CROSSES = 'CROSSES'
    OVERLAPS = 'OVERLAPS'
    EQUALS = 'EQUALS'


@dataclass
class SpatialOperationPredicateNode(PredicateNode):
    """ Node class to represent spatial relation predicate.
    """

    lhs: Node
    rhs: Node
    op: SpatialComparisonOp

    def get_sub_nodes(self):
        return [self.lhs, self.rhs]

    def get_template(self):
        return f"{self.op.name}({{}}, {{}})"


@dataclass
class SpatialPatternPredicateNode(PredicateNode):
    """ Node class to represent spatial relation predicate.
    """

    lhs: Node
    rhs: Node
    pattern: str

    def get_sub_nodes(self):
        return [self.lhs, self.rhs]

    def get_template(self):
        return f"RELATE({{}}, {{}}, '{self.pattern}')"


class SpatialDistanceOp(Enum):
    DWITHIN = 'DWITHIN'
    BEYOND = 'BEYOND'


@dataclass
class SpatialDistancePredicateNode(PredicateNode):
    """ Node class to represent spatial relation predicate.
    """

    lhs: Node
    rhs: Node
    op: SpatialDistanceOp
    distance: float
    units: str

    def get_sub_nodes(self):
        return [self.lhs, self.rhs]

    def get_template(self):
        return f"{self.op.name}({{}}, {{}}, {self.distance}, '{self.units}')"


@dataclass
class BBoxPredicateNode(PredicateNode):
    """ Node class to represent a bounding box predicate.
    """

    lhs: Node
    minx: float
    miny: float
    maxx: float
    maxy: float
    crs: Optional[str] = None

    def get_sub_nodes(self):
        return [self.lhs]

    def get_template(self):
        return (
            f"BBOX({{}}, {self.minx}, {self.miny}, {self.maxx}, "
            f"{self.maxy}, {repr(self.crs)})"
        )


# TODO: Array predicates


class ExpressionNode(Node):
    """ The base class for all nodes representing expressions
    """
    pass


class AttributeExpression(ExpressionNode):
    """ Node class to represent attribute lookup expressions

        :ivar name: the name of the attribute to be accessed
        :type name: str
    """
    inline = True

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"ATTRIBUTE {self.name}"


class LiteralExpression(ExpressionNode):
    """ Node class to represent literal value expressions

        :ivar value: the value of the literal
        :type value: str, float, int, datetime, timedelta
    """
    inline = True

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f"LITERAL {repr(self.value)}"


class ArithmeticOp(Enum):
    ADD = '+'
    SUB = '-'
    MUL = '*'
    DIV = '/'


@dataclass
class ArithmeticExpressionNode(ExpressionNode):
    """ Node class to represent arithmetic operation expressions with two
        sub-expressions and an operator.
    """

    lhs: Node
    rhs: Node
    op: ArithmeticOp

    def get_sub_nodes(self):
        return [self.lhs, self.rhs]

    def get_template(self):
        return f"{{}} {self.op.value} {{}}"


@dataclass
class FunctionExpressionNode(ExpressionNode):
    """ Node class to represent function invocations.
    """

    name: str
    arguments: List[Node]

    def get_sub_nodes(self):
        return self.arguments

    def get_template(self):
        return f"{self.name} ({', '.join(['{}'] * len(self.arguments))})"


def indent(text: str, amount: int, ch: str = ' ') -> str:
    padding = amount * ch
    return ''.join(padding+line for line in text.splitlines(True))


def get_repr(node: Node, indent_amount: int = 0, indent_incr: int = 4) -> str:
    """ Get a debug representation of the given AST node. ``indent_amount``
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
                        get_repr(
                            sub_node,
                            indent_amount + indent_incr,
                            indent_incr
                        ),
                        indent_amount + indent_incr
                    )
                )
            )
        else:
            args.append(repr(sub_node))

    return template.format(*args)
