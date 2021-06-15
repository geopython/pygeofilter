from functools import wraps
from typing import Callable, List, Union, Optional

from lxml import etree

from ... import ast


class NodeParsingError(ValueError):
    pass


class Missing:
    pass


def handle(*tags: List[str], namespace: Optional[str] = Missing,
           subiter: bool = True) -> Callable:
    """ Function-decorator to mark a class function as a handler for a
        given node type.
    """
    assert tags

    @wraps(handle)
    def inner(func):
        print(func)
        func.handles_tags = tags
        func.namespace = namespace
        func.subiter = subiter
        return func

    return inner


class XMLParserMeta(type):
    def __init__(cls, name, bases, dct):
        cls_values = [(cls, dct.values())]
        for base in bases:
            print(base.__dict__)
            cls_values.append((base, base.__dict__.values()))

        tag_map = {}
        for cls_, values in cls_values:
            for value in values:
                if hasattr(value, 'handles_tags'):
                    for handled_tag in value.handles_tags:
                        namespace = value.namespace
                        if namespace is Missing:
                            namespace = cls_.namespace
                        if namespace:
                            if isinstance(namespace, (list, tuple)):
                                namespaces = namespace
                            else:
                                namespaces = [namespace]

                            for namespace in namespaces:
                                full_tag = f'{{{namespace}}}{handled_tag}'
                                tag_map[full_tag] = value
                        else:
                            tag_map[handled_tag] = value

        cls.tag_map = tag_map


ParseInput = Union[etree._Element, etree._ElementTree, str]


class XMLParser(metaclass=XMLParserMeta):
    namespace = None

    def parse(self, input_: ParseInput) -> ast.Node:
        if isinstance(input_, etree._Element):
            root = input_
        elif isinstance(input_, etree._ElementTree):
            root = input_.getroot()
        else:
            root = etree.fromstring(input_)

        return self._evaluate_node(root)

    def _evaluate_node(self, node: etree._Element) -> ast.Node:
        try:
            parse_func = self.tag_map[node.tag]
        except KeyError:
            raise NodeParsingError(f"Cannot parse XML tag {node.tag}")

        if parse_func.subiter:
            sub_nodes = [
                self._evaluate_node(child)
                for child in node.iterchildren()
            ]
            return parse_func(self, node, *sub_nodes)
        else:
            return parse_func(self, node)
