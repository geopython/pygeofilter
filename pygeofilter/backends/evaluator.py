from functools import wraps
from typing import Any, Callable, List, Type

from .. import ast


def get_all_subclasses(*classes: List[Type]) -> List[Type]:
    """ Utility function to get all the leaf-classes (classes that don't
        have any further sub-classes) from a given list of classes.
    """
    all_subclasses = []

    for cls in classes:
        subclasses = cls.__subclasses__()
        if subclasses:
            all_subclasses.extend(
                get_all_subclasses(*subclasses)
            )
        else:
            # directly insert classes that do not have any sub-classes
            all_subclasses.append(cls)

    return all_subclasses


def handle(*node_classes: List[Type], subclasses: bool = False) -> Callable:
    """ Function-decorator to mark a class function as a handler for a
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
    """ Metaclass for the ``Evaluator`` class to create a static map for
        all handler methods by their respective handled types.
    """
    def __init__(cls, name, bases, dct):
        cls.handler_map = {}
        for value in dct.values():
            if hasattr(value, 'handles_classes'):
                for handled_class in value.handles_classes:
                    cls.handler_map[handled_class] = value


class Evaluator(metaclass=EvaluatorMeta):
    """ Base class for AST evaluators.
    """

    def evaluate(self, node: ast.Node) -> Any:
        """ Recursive function to evaluate an abstract syntax tree.
            For every node in the walked syntax tree, its registered handler
            is called with the node as first parameter and all pre-evaluated
            child nodes as star-arguments.
            When no handler was found for a given node, the ``adopt`` function
            is called with the node and its arguments, which by default raises
            an ``NotImplementedError``.
        """
        if hasattr(node, 'get_sub_nodes'):
            sub_args = [
                self.evaluate(sub_node)
                for sub_node in node.get_sub_nodes()
            ]
        else:
            sub_args = []

        node_type = type(node)
        if node_type in self.handler_map:
            return self.handler_map[node_type](self, node, *sub_args)
        return self.adopt(node, *sub_args)

    def adopt(self, node, *sub_args):
        """ Interface function for a last resort when trying to evaluate a node
            and no handler was found.
        """
        raise NotImplementedError(
            f'Failed to evaluate node of type {type(node)}'
        )
