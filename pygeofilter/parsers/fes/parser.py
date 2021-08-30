from typing import Union

from lxml import etree

from .v11 import FES11Parser
from .v20 import FES20Parser


def parse(xml: Union[str, etree._Element]):
    if isinstance(xml, str):
        xml = etree.fromstring(xml)

    # decide upon namespace which parser to use
    namespace = etree.QName(xml).namespace
    if namespace == FES11Parser.namespace:
        return FES11Parser().parse(xml)
    elif namespace == FES20Parser.namespace:
        return FES20Parser().parse(xml)
