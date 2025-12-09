# ------------------------------------------------------------------------------
#
# Project: pygeofilter <https://github.com/geopython/pygeofilter>
# Authors: Magnar Martinsen <magnarem@met.no>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2025 Norwegian Meteorological Institute
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
Apache Solr filter evaluator.

Uses native Python to return dict of JSON request payload
"""

# pylint: disable=E1130,C0103,W0223
from datetime import date, datetime
from typing import Optional

import shapely.wkt
from packaging.version import Version
from pygeoif import shape

from ... import ast, values
from ..evaluator import Evaluator, handle
from .util import like_to_wildcard

VERSION_9_8_1 = Version("9.8.1")

COMPARISON_OP_MAP = {
    ast.ComparisonOp.EQ: "{lhs}:{rhs}",
    ast.ComparisonOp.NE: "-{lhs}:{rhs}",
    ast.ComparisonOp.GT: "{lhs}:{{{rhs} TO *]",
    ast.ComparisonOp.GE: "{lhs}:[{rhs} TO *]",
    ast.ComparisonOp.LT: "{lhs}:[* TO {rhs}}}",
    ast.ComparisonOp.LE: "{lhs}:[* TO {rhs}]",
}

ARITHMETIC_OP_MAP = {
    ast.ArithmeticOp.ADD: "+",
    ast.ArithmeticOp.SUB: "-",
    ast.ArithmeticOp.MUL: "*",
    ast.ArithmeticOp.DIV: "/",
}


class SolrDSLQuery(dict):
    def __init__(self, query="*:*", filters=None):
        """
        Initialize a Solr JSON DSL query object.

        :param query: The main query (default is '*:*').
        :param filters: Optional filters to apply.
        """
        super().__init__()
        if isinstance(query, (str, dict)):
            self["query"] = query
        else:
            raise ValueError(f"Unsupported query type: {type(query)}")

        if filters is not None:
            if "filter" not in self:
                self["filter"] = []
            if isinstance(filters, str):
                self.add_filter(filters)
            if isinstance(filters, list):
                self["filter"] = filters

    def add_filter(self, filter_query):
        """
        Adds a filter query to the JSON DSL.

        :param filter_query: The filter query to add.
        """
        if "filter" not in self:
            self["filter"] = []
        self["filter"].append(filter_query)


class SOLRDSLEvaluator(Evaluator):
    """
    A filter evaluator for Apache Solr

    This evaluator uses the solr.SpatialRecursivePrefixTreeFieldType
    with the JTS context for querying on geometries, and the solr.DateRangeField
    for querying date ranges. See the test_evaluator py in this project
    for field definitions.
    """

    def __init__(
        self,
        attribute_map: Optional[dict[str, str]] = None,
        version: Optional[Version] = None,
    ):
        self.attribute_map = attribute_map
        self.version = version or Version("9.8.1")

    @handle(ast.And)
    def and_(self, _, lhs, rhs):
        """Joins two filter objects with an `and` operator."""
        # Extract the inner queries if lhs or rhs are SolrDSLQuery objects
        lhs = unwrap_query(lhs)
        rhs = unwrap_query(rhs)

        # Merge `must` and `must_not` properly
        combined_query = {"bool": {"must": []}}

        if "bool" in lhs and "must_not" in lhs["bool"]:
            # If `lhs` has a must_not clause, merge it
            combined_query["bool"]["must_not"] = lhs["bool"]["must_not"]
            lhs_must = {key: value for key, value in lhs["bool"].items() if key != "must_not"}
            if lhs_must:
                combined_query["bool"]["must"].append()
        else:
            # If `lhs` has no must_not clause, append it to must
            combined_query["bool"]["must"].append(lhs)

        if "bool" in rhs and "must_not" in rhs["bool"]:
            # If `rhs` has a must_not clause, merge it
            if "must_not" in combined_query["bool"]:
                combined_query["bool"]["must_not"].extend(rhs["bool"]["must_not"])
            else:
                combined_query["bool"]["must_not"] = rhs["bool"]["must_not"]
                rhs_must = {key: value for key, value in rhs["bool"].items() if key != "must_not"}
                if rhs_must:
                    combined_query["bool"]["must"].append()
        else:
            # If `rhs` has no must_not clause, append it to must
            combined_query["bool"]["must"].append(rhs)

        return SolrDSLQuery(combined_query)

    @handle(ast.Or)
    def or_(self, _, lhs, rhs):
        # Extract the inner queries if lhs or rhs are SolrDSLQuery objects
        lhs = unwrap_query(lhs)
        rhs = unwrap_query(rhs)

        # Merge `must` and `must_not` properly
        combined_query = {"bool": {"should": []}}

        if "bool" in lhs and "must_not" in lhs["bool"]:
            # If `lhs` has a must_not clause, merge it
            combined_query["bool"]["must_not"] = lhs["bool"]["must_not"]
            lhs_must = {key: value for key, value in lhs["bool"].items() if key != "must_not"}
            if lhs_must:
                combined_query["bool"]["should"].append()
        else:
            # If `lhs` has no must_not clause, append it to must
            combined_query["bool"]["should"].append(lhs)

        if "bool" in rhs and "must_not" in rhs["bool"]:
            # If `rhs` has a must_not clause, merge it
            if "must_not" in combined_query["bool"]:
                combined_query["bool"]["must_not"].extend(rhs["bool"]["must_not"])
            else:
                combined_query["bool"]["must_not"] = rhs["bool"]["must_not"]
                rhs_must = {key: value for key, value in rhs["bool"].items() if key != "must_not"}
                if rhs_must:
                    combined_query["bool"]["should"].append()
        else:
            # If `rhs` has no must_not clause, append it to must
            combined_query["bool"]["should"].append(rhs)

        return SolrDSLQuery(combined_query)

    @handle(ast.LessThan, ast.LessEqual, ast.GreaterThan, ast.GreaterEqual)
    def comparison(self, node, lhs, rhs):
        """
        Creates a range query for comparison operators.
        """
        return SolrDSLQuery(f"{COMPARISON_OP_MAP[node.op]}".format(lhs=lhs, rhs=rhs))

    @handle(ast.Between)
    def between(self, node: ast.Between, lhs, low, high):
        """
        Creates a range query for between conditions.
        """
        range_query = f"{lhs}:[{low} TO {high}]"
        if node.not_:
            # Negate the range query for NOT Between
            return SolrDSLQuery({"bool": {"must_not": [range_query]}})
        return SolrDSLQuery({"bool": {"must": [range_query]}})

    @handle(ast.In)
    def in_(self, node, lhs, *options):
        """
        Creates a terms query for `IN` conditions.
        """
        options_str = " OR ".join(str(option) for option in options)
        terms_query = f"{lhs}:({options_str})"
        if node.not_:
            # Negate the terms query for NOT IN
            return SolrDSLQuery({"bool": {"must_not": [terms_query]}})
        return SolrDSLQuery({"bool": {"must": [terms_query]}})

    @handle(ast.IsNull)
    def null(self, node: ast.IsNull, lhs):
        """
        Creates a query to check for null values.
        """
        exists_query = f"(*:* -{lhs}:*)"
        if node.not_:
            exists_query = f"{lhs}:*"
        return SolrDSLQuery(exists_query)

    @handle(ast.Exists)
    def exists(self, node: ast.Exists, lhs):
        """
        Creates a query to check if a field exists.
        """
        exists_query = f"{lhs}:[* TO *]"
        if node.not_:
            exists_query = f"-{lhs}:[* TO *]"
        return SolrDSLQuery(exists_query)

    @handle(ast.Attribute)
    def attribute(self, node: ast.Attribute):
        """Attribute mapping from filter fields to Solr fields.
        If an attribute mapping is provided, it is used to look up the
        field name from there.
        """
        if self.attribute_map is not None:
            return self.attribute_map.get(node.name, node.name)
        return node.name

    @handle(*values.LITERALS)
    def literal(self, node):
        """Literal values are directly passed to Solr"""
        return node

    @handle(ast.Not)
    def not_(self, _, sub):
        """Inverts a filter object."""
        # Extract the inner query if sub is a SolrDSLQuery
        sub_query = sub["query"] if isinstance(sub, SolrDSLQuery) else sub

        # Handle the case where the sub-query is already a "must_not"
        if isinstance(sub_query, dict) and "bool" in sub_query and "must_not" in sub_query["bool"]:
            # If the sub-query is already a must_not, remove the negation
            return SolrDSLQuery({"bool": {"must": sub_query["bool"]["must_not"]}})

        # Otherwise, create a new must_not clause
        return SolrDSLQuery({"bool": {"must_not": [sub_query]}})

    @handle(ast.Like)
    def like(self, node: ast.Like, lhs):
        """Transforms the provided LIKE pattern to a Solr wildcard
        pattern. This only works properly on fields that are not tokenized.
        """
        pattern = like_to_wildcard(node.pattern, node.wildcard, node.singlechar, node.escapechar)
        if "*" in pattern:
            p = pattern.split("*")
            if p[0] == "":
                q = f"{{!complexphrase}}{lhs}:*{p[1].strip()}"
                if node.not_:
                    q = f'{{!complexphrase}}-{lhs}:"*{p[1].strip()}"'
            elif p[1] == "":
                q = f'{{!complexphrase}}{lhs}:"{p[0].strip()}*"'
                if node.not_:
                    q = f"{{!complexphrase}}-{lhs}:{p[0].strip()}*"
            else:
                q = f'{{!complexphrase}}{lhs}:"{p[0].strip()}"*"{p[1].strip()}"'
        elif "?" in pattern:
            q = f'{{!complexphrase}}{lhs}:"{pattern}"'
            if node.not_:
                q = f'{{!complexphrase}}-{lhs}:"{pattern}"'

        else:
            q = f'{lhs}:"{pattern}"'
            if node.not_:
                q = f"-{q}"
        return SolrDSLQuery(q)

    @handle(values.Geometry)
    def geometry(self, node: values.Geometry):
        """Geometry values are converted to a Solr spatial query."""
        """Convert to wkt and make sure polygons are counter clockwise"""
        geom_wkt = shape(node).wkt
        geom = shapely.wkt.loads(geom_wkt)
        if geom.geom_type == "Polygon" or geom.geom_type == "MultiPolygon":
            geom = geom.reverse() if not geom.exterior.is_ccw else geom
        return geom.wkt

    @handle(ast.Equal, ast.NotEqual)
    def equality(self, node, lhs, rhs):
        """
        Creates a term query for equality or inequality conditions.
        """
        if node.op == ast.ComparisonOp.EQ:
            # Use a term query for equality
            return SolrDSLQuery(f"{lhs}:{rhs}")
        elif node.op == ast.ComparisonOp.NE:
            # Use a boolean must_not query for inequality
            return SolrDSLQuery(f"-{lhs}:{rhs}")

    @handle(ast.TemporalPredicate, subclasses=True)
    def temporal(self, node: ast.TemporalPredicate, lhs, rhs):
        """Creates a filter to match the given temporal predicate"""
        op = node.op
        if isinstance(rhs, (date, datetime)):
            low = high = rhs.strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            low, high = rhs[0].strftime("%Y-%m-%dT%H:%M:%SZ"), rhs[1].strftime("%Y-%m-%dT%H:%M:%SZ")

        query = None
        if op == ast.TemporalComparisonOp.DISJOINT:
            query = f"-{lhs}:[{low} TO {high}]"
        elif op == ast.TemporalComparisonOp.AFTER:
            query = f"{lhs}:{{{high} TO *]"
        elif op == ast.TemporalComparisonOp.BEFORE:
            query = f"{lhs}:[* TO {low}}}"
        elif op == ast.TemporalComparisonOp.TOVERLAPS or op == ast.TemporalComparisonOp.OVERLAPPEDBY:
            query = f"{lhs}:[{low} TO {high}]"
        elif op == ast.TemporalComparisonOp.BEGINS:
            query = f"{lhs}:{low}"
        elif op == ast.TemporalComparisonOp.BEGUNBY:
            query = f"{lhs}:{high}"
        elif op == ast.TemporalComparisonOp.DURING:
            query = f"{lhs}:{{{low} TO {high}}}"
        elif op == ast.TemporalComparisonOp.TCONTAINS:
            query = f"{lhs}:[{low} TO {high}]"
        # elif op == ast.TemporalComparisonOp.ENDS:
        #     pass
        # elif op == ast.TemporalComparisonOp.ENDEDBY:
        #     pass
        # elif op == ast.TemporalComparisonOp.TEQUALS:
        #     pass
        # elif op == ast.TemporalComparisonOp.BEFORE_OR_DURING:
        #     pass
        # elif op == ast.TemporalComparisonOp.DURING_OR_AFTER:
        #     pass
        else:
            raise NotImplementedError(f"Unsupported temporal operator: {op}")

        return SolrDSLQuery(query)

    @handle(ast.GeometryIntersects, ast.GeometryDisjoint, ast.GeometryWithin, ast.GeometryContains, ast.GeometryEquals)
    def spatial_comparison(self, node: ast.SpatialComparisonPredicate, lhs: str, rhs):
        """Creates a spatial query for the given spatial comparison
        predicate.
        """
        query = {}
        # Solr need capitalized first letter of operator
        op = node.op.value.lower().capitalize()
        if op == "Disjoint":
            geo_filter = f"{{!field f={lhs} v='Intersects({rhs})'}}"
            query = {"bool": {"must_not": [geo_filter]}}
            return SolrDSLQuery(query)

        query = f"{{!field f={lhs} v='{op}({rhs})'}}"
        return SolrDSLQuery(query)

    @handle(ast.BBox)
    def bbox(self, node: ast.BBox, lhs):
        """Performs a spatial query for the given bounding box.
        Ignores CRS parameter, as it is not supported by Solr.
        """
        bbox = self.envelope(values.Envelope(node.minx, node.maxx, node.miny, node.maxy))
        query = f"{{!field f={lhs} v='Intersects({bbox})'}}"
        return SolrDSLQuery(query)

    # @handle(ast.Arithmetic, subclasses=True)
    # def arithmetic(self, node: ast.Arithmetic, lhs, rhs):
    #     op = ARITHMETIC_OP_MAP[node.op]
    #     return f"({lhs} {op} {rhs})"

    # @handle(ast.Function)
    # def function(self, node, *arguments):
    #     func = self.function_map[node.name]
    #     return f"{func}({','.join(arguments)})"

    @handle(values.Envelope)
    def envelope(self, node: values.Envelope):
        """Envelope values are converted to an WKT ENVELOPE for Solr."""
        min_x = float(min(node.x1, node.x2))
        max_x = float(max(node.x1, node.x2))
        min_y = float(min(node.y1, node.y2))
        max_y = float(max(node.y1, node.y2))
        return f"ENVELOPE({min_x}, {max_x}, {max_y}, {min_y})"


def to_filter(
    root,
    attribute_map: Optional[dict[str, str]] = None,
    version: Optional[Version] = None,
):
    """Shorthand function to convert a pygeofilter AST to an Apache Solr
    filter structure.
    """
    return SOLRDSLEvaluator(attribute_map, Version(version) if version else None).evaluate(root)


def unwrap_query(obj):
    """Extract the inner query from a SolrDSLQuery or return the object directly."""
    if isinstance(obj, SolrDSLQuery):
        # Return the inner query only if it is not empty
        return obj.get("query", {})
    return obj
