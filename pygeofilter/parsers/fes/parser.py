from typing import Union

from lxml import etree

from ... import ast
from .util import Element, ElementTree
from .v11 import FES11Parser
from .v20 import FES20Parser


def parse(xml: Union[str, Element, ElementTree]) -> ast.Node:
    if isinstance(xml, str):
        root = etree.fromstring(xml)
    else:
        root = xml

    # decide upon namespace which parser to use
    namespace = etree.QName(root).namespace
    if namespace == FES11Parser.namespace:
        return FES11Parser().parse(root)
    elif namespace == FES20Parser.namespace:
        return FES20Parser().parse(root)

    raise ValueError(f"Unsupported namespace {namespace}")
