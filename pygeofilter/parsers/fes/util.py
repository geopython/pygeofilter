from functools import wraps
from typing import Callable, Optional, Type, Union

from lxml import etree

from ... import ast

Element = etree._Element
ElementTree = etree._ElementTree
ParseInput = Union[etree._Element, etree._ElementTree, str]


class NodeParsingError(ValueError):
    pass


class Missing:
    pass


def handle(
    *tags: str, namespace: Union[str, Type[Missing]] = Missing, subiter: bool = True
) -> Callable:
    """Function-decorator to mark a class function as a handler for a
    given node type.
    """
    assert tags

    @wraps(handle)
    def inner(func):
        func.handles_tags = tags
        func.namespace = namespace
        func.subiter = subiter
        return func

    return inner


def handle_namespace(namespace: str, subiter: bool = True) -> Callable:
    """Function-decorator to mark a class function as a handler for a
    given namespace.
    """

    @wraps(handle)
    def inner(func):
        func.handles_namespace = namespace
        func.subiter = subiter
        return func

    return inner


class XMLParserMeta(type):
    def __init__(cls, name, bases, dct):
        cls_values = [(cls, dct.values())]
        cls_namespace = getattr(cls, "namespace", None)

        for base in bases:
            cls_namespace = cls_namespace or getattr(base, "namespace", None)
            cls_values.append((base, base.__dict__.values()))

        tag_map = {}
        namespace_map = {}
        for cls_, values in cls_values:
            for value in values:
                if hasattr(value, "handles_tags"):
                    for handled_tag in value.handles_tags:
                        namespace = value.namespace
                        if namespace is Missing:
                            namespace = (
                                getattr(cls_, "namespace", None) or cls_namespace
                            )
                        if namespace:
                            if isinstance(namespace, (list, tuple)):
                                namespaces = namespace
                            else:
                                namespaces = [namespace]

                            for namespace in namespaces:
                                full_tag = f"{{{namespace}}}{handled_tag}"
                                tag_map[full_tag] = value
                        else:
                            tag_map[handled_tag] = value

                if hasattr(value, "handles_namespace"):
                    namespace_map[value.handles_namespace] = value

        cls.tag_map = tag_map
        cls.namespace_map = namespace_map


class XMLParser(metaclass=XMLParserMeta):
    namespace: Optional[str] = None
    tag_map: dict
    namespace_map: dict

    def parse(self, input_: ParseInput) -> ast.Node:
        if isinstance(input_, Element):
            root = input_
        elif isinstance(input_, ElementTree):
            root = input_.getroot()
        else:
            root = etree.fromstring(input_)

        return self._evaluate_node(root)

    def _evaluate_node(self, node: etree._Element) -> ast.Node:
        qname = etree.QName(node.tag)
        if node.tag in self.tag_map:
            parse_func = self.tag_map[node.tag]
        elif qname.namespace in self.namespace_map:
            parse_func = self.namespace_map[qname.namespace]
        else:
            raise NodeParsingError(f"Cannot parse XML tag {node.tag}")

        if parse_func.subiter:
            sub_nodes = [self._evaluate_node(child) for child in node.iterchildren()]
            return parse_func(self, node, *sub_nodes)
        else:
            return parse_func(self, node)
