# ------------------------------------------------------------------------------
#
# Project: pygeofilter <https://github.com/geopython/pygeofilter>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
# Johannes Eberenz <johannes.eberenz@alliander.com>
#
# ------------------------------------------------------------------------------
# Copyright (c) 2021 geopython
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

from typing import Literal

from lxml.etree import Element, tostring
from pygml import v32

from pygeofilter import ast, values
from pygeofilter.backends.evaluator import Evaluator, handle

FES20_URI = "http://www.opengis.net/fes/2.0"
XSD_URI = "http://www.w3.org/2001/XMLSchema-datatypes"
FES10_URI = "http://www.opengis.net/ogc"
GML_URI = "http://www.opengis.net/gml"
FES_VERSION = Literal["v1.1"]

COMPARISON_OP_MAP = {
    ast.ComparisonOp.EQ: "PropertyIsEqualTo",
    ast.ComparisonOp.NE: "PropertyIsNotEqualTo",
    ast.ComparisonOp.LT: "PropertyIsLessThan",
    ast.ComparisonOp.LE: "PropertyIsLessThanOrEqualTo",
    ast.ComparisonOp.GT: "PropertyIsGreaterThan",
    ast.ComparisonOp.GE: "PropertyIsGreaterThanOrEqualTo",
}


ARITHMETIC_OP_MAP = {
    ast.ArithmeticOp.ADD: "Add",
    ast.ArithmeticOp.SUB: "Sub",
    ast.ArithmeticOp.MUL: "Mul",
    ast.ArithmeticOp.DIV: "Div",
}

SPATIAL_COMPARISON_OP_MAP = {
    ast.SpatialComparisonOp.INTERSECTS: "Intersects",
    ast.SpatialComparisonOp.DISJOINT: "Disjoint",
    ast.SpatialComparisonOp.CONTAINS: "Contains",
    ast.SpatialComparisonOp.WITHIN: "Within",
    ast.SpatialComparisonOp.TOUCHES: "Touches",
    ast.SpatialComparisonOp.CROSSES: "Crosses",
    ast.SpatialComparisonOp.OVERLAPS: "Overlaps",
    ast.SpatialComparisonOp.EQUALS: "Equals",
}

SPATIAL_DISTANCE_OP_MAP = {
    ast.SpatialDistanceOp.DWITHIN: "Dwithin",
    ast.SpatialDistanceOp.BEYOND: "Beyond",
}


class FESEvaluator(Evaluator):
    def __init__(
        self,
        namespace: str,
        fes_version: FES_VERSION = "v1.1",
        gml_identifier: str | None = None,
    ):
        if fes_version != "v1.1":
            raise (NotImplementedError("Only FES v1.1 is supported"))
        self.ns = namespace
        if namespace in ("", "{}"):
            self.gml32_encoder = v32.GML3Encoder(
                namespace="", nsmap=None, id_required=False
            )
        else:

            self.gml32_encoder = v32.GML3Encoder(
                namespace=v32.NAMESPACE, nsmap=v32.NSMAP, id_required=False
            )
        self.gml_identifier = gml_identifier

    def negate_if_not(self, node, el) -> Element:
        if node.not_:
            return self.not_(None, el)
        return el

    @handle(ast.Not)
    def not_(self, node, sub):
        el = Element(self.ns + "Not")
        el.append(sub)
        return el

    @handle(ast.And, ast.Or)
    def combination(self, node, lhs, rhs):
        el = Element(self.ns + node.op.value.title())
        el.append(lhs)
        el.append(rhs)
        return el

    @handle(ast.Comparison, subclasses=True)
    def comparison(self, node, lhs, rhs):
        el = Element(self.ns + COMPARISON_OP_MAP[node.op])
        el.append(lhs)
        el.append(rhs)
        return el

    @handle(ast.Between)
    def between(self, node, lhs, low, high):
        el = Element(self.ns + "PropertyIsBetween")
        low_el = Element(self.ns + "LowerBoundary")
        low_el.append(low)
        high_el = Element(self.ns + "UpperBoundary")
        high_el.append(high)
        el.append(lhs)
        el.append(low_el)
        el.append(high_el)
        return self.negate_if_not(node, el)

    @handle(ast.Like)
    def like(self, node, lhs):
        el = Element(self.ns + "PropertyIsLike")
        el.append(lhs)
        # ast.
        el.append(self.literal(node.pattern))
        if node.wildcard:
            el.attrib["wildCard"] = node.wildcard
        if node.singlechar:
            el.attrib["singleChar"] = node.singlechar
        if node.escapechar:
            el.attrib["escapeChar"] = node.escapechar
        el.attrib["matchCase"] = str(not node.nocase).lower()

        return self.negate_if_not(node, el)

    @handle(ast.IsNull)
    def null(self, node, lhs):
        el = Element(self.ns + "PropertyIsNull")
        el.append(lhs)
        return self.negate_if_not(node, el)

    @handle(ast.SpatialComparisonPredicate, subclasses=True)
    def spatial_operation(self, node, lhs, rhs):
        op = SPATIAL_COMPARISON_OP_MAP[node.op]
        el = Element(self.ns + op)
        el.append(lhs)
        el.append(rhs)
        return el

    @handle(ast.BBox)
    def bbox(self, node, lhs):
        el = Element(self.ns + "BBOX")
        if lhs is not None:
            el.append(lhs)
        envelope_el = self.envelope(
            ast.values.Envelope(node.minx, node.maxx, node.miny, node.maxy)
        )
        if node.crs is not None:
            envelope_el.attrib["srsName"] = node.crs
        el.append(envelope_el)
        return el

    @handle(ast.SpatialDistancePredicate, subclasses=True)
    def dwithin(self, node, lhs, rhs):
        op = SPATIAL_DISTANCE_OP_MAP[node.op]
        el = Element(self.ns + op)
        el.append(lhs)
        el.append(rhs)
        dist_el = Element(self.ns + "Distance")
        dist_el.text = str(node.distance)
        dist_el.attrib["uom"] = node.units
        el.append(dist_el)
        return el

    @handle(ast.Arithmetic, subclasses=True)
    def arithmetic(self, node: ast.Arithmetic, lhs, rhs):
        op = ARITHMETIC_OP_MAP[node.op]
        el = Element(self.ns + op)
        el.append(lhs)
        el.append(rhs)
        return el

    @handle(ast.Function)
    def function(self, node, *arguments):
        el = Element(self.ns + "Function")
        el.attrib["name"] = node.name
        for arg in arguments:
            el.append(arg)
        return el

    @handle(ast.Attribute)
    def attribute(self, node: ast.Attribute):
        el = Element(self.ns + "PropertyName")
        el.text = node.name
        return el

    @handle(*values.LITERALS)
    def literal(self, node):
        el = Element(self.ns + "Literal")
        el.text = str(node)
        if self.ns != "":
            match node:
                case str():
                    el.attrib["type"] = "xsd:string"
                case int():
                    el.attrib["type"] = "xsd:int"
                case float():
                    el.attrib["type"] = "xsd:double"
                case bool():
                    el.attrib["type"] = "xsd:boolean"
                    el.text = str(node).lower()
        return el

    @handle(values.Geometry)
    def geometry(self, node: values.Geometry):
        gml = self.gml32_encoder.encode(
            geometry=node.geometry, identifier=self.gml_identifier
        )
        if "srsName" in gml.attrib and "crs" not in node.geometry:
            gml.attrib.pop(
                "srsName"
            )  # remove the default CRS, assumed by pygml
        return gml

    @handle(values.Envelope)
    def envelope(self, node: values.Envelope):
        """
        Envelope values are converted to an WKT ENVELOPE for Solr.

        If min_x > max_x, solr assume dateline crossing.
        """
        ns = f"{{{self.gml32_encoder.namespace}}}"
        el = Element(ns + "Envelope", nsmap=self.gml32_encoder.nsmap)
        lc_el = Element(self.ns + "lowerCorner")
        lc_el.text = f"{node.x1} {node.y1}"
        uc_el = Element(self.ns + "upperCorner")
        uc_el.text = f"{node.x2} {node.y2}"
        el.append(lc_el)
        el.append(uc_el)
        return el

    # @handle(ast.In)
    # def in_(self, node, lhs, *options):
    #     raise NotImplementedError("'In' comparison is not supported by FES v1.1")


def to_lxml_etree(
    root,
    namespaces=True,
    fes_version: FES_VERSION = "v1.1",
    gml_identifier: str | None = None,
):
    """Converts to OGC Feature encoding standard (FES) lxml elememt tree.
    Only FES v1.1 is supported."""
    if namespaces:
        nsmap = {"ogc": FES10_URI, "xsd": XSD_URI}
        fes_ns = f"{{{FES10_URI}}}"
        filter_el = Element(fes_ns + "Filter", nsmap=nsmap)
    else:
        fes_ns = ""
        filter_el = Element("Filter")
    filter_el.append(
        FESEvaluator(namespace=fes_ns, gml_identifier=gml_identifier).evaluate(
            node=root
        )
    )
    return filter_el


def to_xml_str(
    root,
    pretty_print: bool = False,
    namespaces: bool = True,
    fes_version: FES_VERSION = "v1.1",
    gml_identifier: str | None = None,
) -> str:
    """Converts to OGC Feature encoding standard (FES) XML string.
    Keyword arguments:
    pretty_print -- format output (default False)
    namspaces -- add XML namespaces (default True)
    fes_version -- Only FES v1.1 is supported (default v1.1)
    gml_identifier -- prefix for id attribute of geometry tags (default None)
    """
    filter_el = to_lxml_etree(
        root,
        namespaces=namespaces,
        fes_version=fes_version,
        gml_identifier=gml_identifier,
    )
    xml_str = tostring(filter_el, encoding="unicode", pretty_print=pretty_print)
    return xml_str
