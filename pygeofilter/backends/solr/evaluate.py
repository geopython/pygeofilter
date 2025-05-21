# ------------------------------------------------------------------------------
#
# Project: pygeofilter <https://github.com/geopython/pygeofilter>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2022 EOX IT Services GmbH
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
Apache SolR filter evaluator.

"""


# pylint: disable=E1130,C0103,W0223

from datetime import date, datetime
from typing import Dict, Optional, Union

from packaging.version import Version

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
    def __init__(self, query='*:*', filter=None):
        super().__init__()
        self['query'] = query
        if filter is not None:
            self['filter'] = filter

class SOLRDSLEvaluator(Evaluator):
    """A filter evaluator for Apache SolR"""

    def __init__(
        self,
        attribute_map: Optional[Dict[str, str]] = None,
        version: Optional[Version] = None,
    ):
        self.attribute_map = attribute_map
        self.version = version or Version("9.8.1")
   
    @handle(ast.And)
    def and_(self, _, lhs, rhs):
        """Joins two filter objects with an `and` operator."""
        lhs = handle_combination_query(lhs)
        rhs = handle_combination_query(rhs)
        return SolrDSLQuery(f"{lhs} AND {rhs}")

    @handle(ast.Or)
    def or_(self, _, lhs, rhs):
        """Joins two filter objects with an `or` operator."""
        lhs = handle_combination_query(lhs)
        rhs = handle_combination_query(rhs)
        return SolrDSLQuery(f"{lhs} OR {rhs}")

    @handle(ast.LessThan, ast.LessEqual, ast.GreaterThan, ast.GreaterEqual)
    def comparison(self, node, lhs, rhs):
        """Creates a `range` filter."""
        return SolrDSLQuery(f"{COMPARISON_OP_MAP[node.op]}".format(lhs=lhs, rhs=rhs))

    @handle(ast.Between)
    def between(self, node: ast.Between, lhs, low, high):
        """Creates a `range` filter."""
        q = f"{lhs}:[{low} TO {high}]"
        if node.not_:
            q = f"-{q}"
        return SolrDSLQuery(q)

    @handle(ast.In)
    def in_(self, node, lhs, *options):
        """Creates a `terms` filter."""
        options_str = " OR ".join(str(option) for option in options)
        q = f"{lhs}:({options_str})"
        if node.not_:
            q = f"-{q}"
        return SolrDSLQuery(q)

    @handle(ast.IsNull)
    def null(self, node: ast.IsNull, lhs):
        """Performs a null check."""
        q = f"(*:* -{lhs}:*)"
        if node.not_:
            q = f"{lhs}:*"
        return SolrDSLQuery(q)

    @handle(ast.Exists)
    def exists(self, node: ast.Exists, lhs):
        """Performs an existense check."""
        q = f"{lhs}:[* TO *]"
        if node.not_:
            q = f"-{lhs}:[* TO *]"
        return SolrDSLQuery(q)

    @handle(ast.Attribute)
    def attribute(self, node: ast.Attribute):
        """Attribute mapping from filter fields to Solr fields.
        If an attribute mapping is provided, it is used to look up the
        field name from there.
        """
        if self.attribute_map is not None:
            return self.attribute_map[node.name]
        return node.name

    @handle(*values.LITERALS)
    def literal(self, node):
        """Literal values are directly passed to Solr"""
        return node
    
    @handle(ast.Not)
    def not_(self, _, sub):
        """Inverts a filter object."""
        return SolrDSLQuery(f"-{sub}")

    @handle(ast.Like)
    def like(self, node: ast.Like, lhs):
        """Transforms the provided LIKE pattern to a Solr wildcard
        pattern. This only works properly on fields that are not tokenized.
        """
        pattern = like_to_wildcard(
            node.pattern, node.wildcard, node.singlechar, node.escapechar
        )
        # q = f"{{!complexphrase}}{lhs}:\"{pattern}\""
        q = f"{lhs}:\"{pattern}\""
        if node.not_:
            q = f"-{q}"
        return SolrDSLQuery(q)

    @handle(values.Geometry)
    def geometry(self, node: values.Geometry):
        """Geometry values are converted to a Solr spatial query.
        This assumes that 'geom' is the field in Solr schema which holds the geometry data.
        """
        print(node.op)
        self.attribute_map[node.name]
        return f"{lhs}:\"Intersects({node.geometry})\""


    @handle(ast.Equal, ast.NotEqual)
    def equality(self, node, lhs, rhs):
        """Creates a match filter."""
        return SolrDSLQuery(f"{COMPARISON_OP_MAP[node.op]}".format(lhs=lhs, rhs=rhs))


    @handle(ast.TemporalPredicate, subclasses=True)
    def temporal(self, node: ast.TemporalPredicate, lhs, rhs):
        """Creates a filter to match the given temporal predicate"""
        op = node.op
        if isinstance(rhs, (date, datetime)):
            low = high = rhs.strftime('%Y-%m-%dT%H:%M:%SZ')
        else:
            low, high = rhs[0].strftime('%Y-%m-%dT%H:%M:%SZ'), rhs[1].strftime('%Y-%m-%dT%H:%M:%SZ')

        query = None
        if op == ast.TemporalComparisonOp.DISJOINT:
            query = f"-{lhs}:[{low} TO {high}]"
        elif op == ast.TemporalComparisonOp.AFTER:
            query = f"{lhs}:{{{high} TO *]"
        elif op == ast.TemporalComparisonOp.BEFORE:
            query = f"{lhs}:[* TO {low}}}"
        elif (
            op == ast.TemporalComparisonOp.TOVERLAPS
            or op == ast.TemporalComparisonOp.OVERLAPPEDBY
        ):
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

    @handle(
        ast.GeometryIntersects,
        ast.GeometryDisjoint,
        ast.GeometryWithin,
        ast.GeometryContains,
        ast.GeometryEquals
    )
    def spatial_comparison(self, node: ast.SpatialComparisonPredicate, lhs: str, rhs):
        """Creates a spatial query for the given spatial comparison
        predicate.
        """
        # Solr need capitalized first letter of operator
        op = node.op.value.lower().capitalize()
        query = f"{{!field f={lhs}}}{op}({rhs})"
        return SolrDSLQuery(query)


    @handle(ast.BBox)
    def bbox(self, node: ast.BBox, lhs):
        """Performs a spatial query for the given bounding box.
        Ignores CRS parameter, as it is not supported by SolR.
        """
        bbox = self.envelope(
            values.Envelope(node.minx, node.maxx, node.miny, node.maxy)
            )
        query = f"{{!field f={lhs}}}Intersects({bbox})"
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
        """Envelope values are converted to an WKT ENVELOPE for SolR."""
        min_x = min(node.x1, node.x2)
        max_x = max(node.x1, node.x2)
        min_y = min(node.y1, node.y2)
        max_y = max(node.y1, node.y2)
        return f"ENVELOPE({min_x}, {max_x}, {max_y}, {min_y})"



def handle_combination_query(q):
    if isinstance(q, dict):
        if q['query']:
            return q['query']


def to_filter(
    root,
    attribute_map: Optional[Dict[str, str]] = None,
    version: Optional[str] = None,
):
    """Shorthand function to convert a pygeofilter AST to an Apache SolR
    filter structure.
    """
    return SOLRDSLEvaluator(
        attribute_map, Version(version) if version else None
    ).evaluate(root)
