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

from functools import wraps
from typing import Any, Callable, Dict, List, Type, cast

from .. import ast


def get_all_subclasses(*classes: Type) -> List[Type]:
    """Utility function to get all the leaf-classes (classes that don't
    have any further sub-classes) from a given list of classes.
    """
    all_subclasses = []

    for cls in classes:
        subclasses = cls.__subclasses__()
        if subclasses:
            all_subclasses.extend(get_all_subclasses(*subclasses))
        else:
            # directly insert classes that do not have any sub-classes
            all_subclasses.append(cls)

    return all_subclasses


def handle(*node_classes: Type, subclasses: bool = False) -> Callable:
    """Function-decorator to mark a class function as a handler for a
    given node type.
    """
    assert node_classes

    @wraps(handle)
    def inner(func):
        if subclasses:
            func.handles_classes = get_all_subclasses(*node_classes)
        else:
            func.handles_classes = node_classes
        return func

    return inner


class EvaluatorMeta(type):
    """Metaclass for the ``Evaluator`` class to create a static map for
    all handler methods by their respective handled types.
    """

    def __init__(cls, name, bases, dct):
        cls.handler_map = {}
        for base in bases:
            cls.handler_map.update(getattr(base, "handler_map"))

        for value in dct.values():
            if hasattr(value, "handles_classes"):
                for handled_class in value.handles_classes:
                    cls.handler_map[handled_class] = value


class Evaluator(metaclass=EvaluatorMeta):
    """Base class for AST evaluators."""

    handler_map: Dict[Type, Callable]

    def evaluate(self, node: ast.AstType, adopt_result: bool = True) -> Any:
        """Recursive function to evaluate an abstract syntax tree.
        For every node in the walked syntax tree, its registered handler
        is called with the node as first parameter and all pre-evaluated
        child nodes as star-arguments.
        When no handler was found for a given node, the ``adopt`` function
        is called with the node and its arguments, which by default raises
        an ``NotImplementedError``.
        """
        sub_args = []
        if hasattr(node, "get_sub_nodes"):
            subnodes = cast(ast.Node, node).get_sub_nodes()
            if subnodes:
                if isinstance(subnodes, list):
                    sub_args = [self.evaluate(sub_node, False) for sub_node in subnodes]
                else:
                    sub_args = [self.evaluate(subnodes, False)]

        handler = self.handler_map.get(type(node))
        if handler is not None:
            result = handler(self, node, *sub_args)
        else:
            result = self.adopt(node, *sub_args)

        if adopt_result:
            return self.adopt_result(result)
        else:
            return result

    def adopt(self, node, *sub_args):
        """Interface function for a last resort when trying to evaluate a node
        and no handler was found.
        """
        raise NotImplementedError(f"Failed to evaluate node of type {type(node)}")

    def adopt_result(self, result: Any) -> Any:
        """Interface function for adopting the final evaluation result
        if necessary.  Default is no-op.
        """
        return result
