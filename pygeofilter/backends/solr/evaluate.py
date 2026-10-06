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
from typing import Optional, Union

import shapely.wkt
from dateutil import parser
from packaging.version import Version
from pygeoif import shape
from pytz import UTC

from ... import ast, values
from ..evaluator import Evaluator, handle
from .util import like_to_wildcard

VERSION_9_8_1 = Version("9.8.1")


def _split_query_and_filters(part):
    """Return (query, filters) for a SolrDSLQuery-like part."""
    if isinstance(part, SolrDSLQuery):
        return part.get("query", "*:*"), list(part.get("filter", []))
    return part, []


def _invert_filter_query(filter_query):
    """Invert a Solr filter expression.

    For string filters, toggles a leading '-' prefix. For non-string filters
    (e.g., bool dicts), wraps the filter in a bool.must_not structure.
    """
    if isinstance(filter_query, str):
        return (
            filter_query[1:]
            if filter_query.startswith("-")
            else f"-{filter_query}"
        )
    if (
        isinstance(filter_query, dict)
        and "bool" in filter_query
        and "must_not" in filter_query["bool"]
    ):
        return {"bool": {"must": filter_query["bool"]["must_not"]}}
    return {"bool": {"must_not": [filter_query]}}


def _to_solr_date(value):
    """Convert input date/datetime to Solr UTC datetime string: YYYY-MM-DDTHH:MM:SSZ.

    Returns None for empty input.
    Raises ValueError for unparseable input.
    """
    if value is None:
        return None

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        return value

    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            # dateutil handles many formats:
            # 2024-11-04, 2024-11-04T10:00:00Z, 2024-11-04 10:00:00+01:00, etc.
            dt = parser.isoparse(text)
        except (ValueError, TypeError, OverflowError):
            try:
                dt = parser.parse(text)
            except (ValueError, TypeError, OverflowError):
                # Not a date-like string: keep term value as-is.
                return value
    else:
        return value

    # If no timezone is provided, assume UTC (adjust if your source is local time).
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)

    dt_utc = dt.astimezone(UTC)

    # Solr wants Zulu time with second precision.
    return dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")


COMPARISON_OP_MAP = {
    ast.ComparisonOp.EQ: '{lhs}:"{rhs}"',
    ast.ComparisonOp.NE: '-{lhs}:"{rhs}"',
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
    def __init__(self, query: Union[dict, str] = "*:*", filters=None):
        """
        Initialize a Solr JSON DSL query object.

        :param query: The main query (default is "*:*").
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
        """Joins two filter objects with an `and` operator.

        Spatial {!field ...} filters live in the SolrDSLQuery 'filter' key and must
        not be merged into bool.must (they don't work correctly in the query position
        for Geo3D fields). Non-spatial queries are combined in bool.must as before.
        """
        lhs_q = (
            lhs.get("query", "*:*") if isinstance(lhs, SolrDSLQuery) else lhs
        )
        rhs_q = (
            rhs.get("query", "*:*") if isinstance(rhs, SolrDSLQuery) else rhs
        )
        lhs_filters = (
            list(lhs.get("filter", [])) if isinstance(lhs, SolrDSLQuery) else []
        )
        rhs_filters = (
            list(rhs.get("filter", [])) if isinstance(rhs, SolrDSLQuery) else []
        )
        combined_filters = lhs_filters + rhs_filters

        # Build must list from non-trivial (non-wildcard) query parts
        must_parts = []
        must_not_parts = []
        for q in [lhs_q, rhs_q]:
            if q == "*:*":
                continue
            if isinstance(q, dict) and "bool" in q:
                if "must_not" in q["bool"]:
                    must_not_parts.extend(q["bool"]["must_not"])
                if "must" in q["bool"]:
                    must_parts.extend(q["bool"]["must"])
            else:
                must_parts.append(q)

        if not must_parts and not must_not_parts:
            combined_q = "*:*"
        elif not must_parts and must_not_parts:
            combined_q = {"bool": {"must_not": must_not_parts}}
        else:
            combined_q = {"bool": {"must": must_parts}}
            if must_not_parts:
                combined_q["bool"]["must_not"] = must_not_parts

        result = SolrDSLQuery(combined_q)
        if combined_filters:
            result["filter"] = combined_filters
        return result

    @handle(ast.Or)
    def or_(self, _, lhs, rhs):
        def to_or_clause(query_part, filter_parts):
            def normalize_clause(clause):
                if isinstance(clause, str) and clause.startswith("-"):
                    return {"bool": {"must": ["*:*"], "must_not": [clause[1:]]}}
                if isinstance(clause, dict) and "bool" in clause:
                    bool_part = clause["bool"]
                    if (
                        "must_not" in bool_part
                        and "must" not in bool_part
                        and "should" not in bool_part
                    ):
                        normalized = dict(clause)
                        normalized["bool"] = dict(bool_part)
                        normalized["bool"]["must"] = ["*:*"]
                        return normalized
                return clause

            clauses = []
            if query_part != "*:*":
                clauses.append(normalize_clause(query_part))
            clauses.extend(normalize_clause(clause) for clause in filter_parts)
            if not clauses:
                return "*:*"
            if len(clauses) == 1:
                return clauses[0]
            return {"bool": {"must": clauses}}

        lhs_q, lhs_filters = _split_query_and_filters(lhs)
        rhs_q, rhs_filters = _split_query_and_filters(rhs)

        lhs_clause = to_or_clause(lhs_q, lhs_filters)
        rhs_clause = to_or_clause(rhs_q, rhs_filters)

        # OR with a match-all branch is a no-op.
        if lhs_clause == "*:*" or rhs_clause == "*:*":
            return SolrDSLQuery("*:*")

        # Keep OR in filter[] so spatial predicates remain in filter context.
        or_filter = {"bool": {"should": [lhs_clause, rhs_clause]}}
        return SolrDSLQuery("*:*", filters=[or_filter])

    @handle(ast.LessThan, ast.LessEqual, ast.GreaterThan, ast.GreaterEqual)
    def comparison(self, node, lhs, rhs):
        """
        Creates a range query for comparison operators.
        """
        rhs = _to_solr_date(rhs)
        return SolrDSLQuery(
            f"{COMPARISON_OP_MAP[node.op]}".format(lhs=lhs, rhs=rhs)
        )

    @handle(ast.Between)
    def between(self, node: ast.Between, lhs, low, high):
        """
        Creates a range query for between conditions.
        """
        low = _to_solr_date(low)
        high = _to_solr_date(high)
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

        def _quote(v):
            if isinstance(v, str):
                return '"' + v.replace('"', '\\"') + '"'
            return str(v)

        options_str = " OR ".join(_quote(option) for option in options)
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
        if isinstance(sub, SolrDSLQuery):
            sub_query, sub_filters = _split_query_and_filters(sub)

            result = SolrDSLQuery("*:*")
            if sub_filters:
                result["filter"] = [
                    _invert_filter_query(fq) for fq in sub_filters
                ]

            # A wildcard query contributes no restriction and does not need
            # query-level negation.
            if sub_query == "*:*":
                return result

            if (
                isinstance(sub_query, dict)
                and "bool" in sub_query
                and "must_not" in sub_query["bool"]
            ):
                result["query"] = {
                    "bool": {"must": sub_query["bool"]["must_not"]}
                }
                return result

            result["query"] = {"bool": {"must_not": [sub_query]}}
            return result

        # Non-SolrDSLQuery fallback.
        if (
            isinstance(sub, dict)
            and "bool" in sub
            and "must_not" in sub["bool"]
        ):
            return SolrDSLQuery({"bool": {"must": sub["bool"]["must_not"]}})
        return SolrDSLQuery({"bool": {"must_not": [sub]}})

    @handle(ast.Like)
    def like(self, node: ast.Like, lhs):
        """Transforms the provided LIKE pattern to a Solr wildcard
        pattern. This only works properly on fields that are not tokenized.
        """
        pattern = like_to_wildcard(
            node.pattern, node.wildcard, node.singlechar, node.escapechar
        )
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
        geom_wkt = shape(node).wkt
        geom = shapely.wkt.loads(geom_wkt)
        if geom.geom_type == "Polygon" or geom.geom_type == "MultiPolygon":
            # Rectangular polygons (from BBox) must use ENVELOPE format for Geo3D.
            # WKT polygons with coordinates at ±180/±90 are "coplanar" in 3D space
            # (poles and antimeridian are degenerate points), causing Solr to reject
            # or mishandle them. ENVELOPE is safe and correct for axis-aligned boxes.
            coords = list(geom.exterior.coords)
            if (
                len(coords) == 5
                and len({c[0] for c in coords[:-1]}) == 2
                and len({c[1] for c in coords[:-1]}) == 2
            ):
                minx, miny, maxx, maxy = geom.bounds
                # Global bbox covers the whole Earth — spatial predicate is a no-op.
                if minx <= -180 and miny <= -90 and maxx >= 180 and maxy >= 90:
                    return None
                if (minx <= -179.9999 and maxx >= 179.9999) or (
                    miny <= -89.9999 and maxy >= 89.9999
                ):
                    return f"ENVELOPE({minx}, {maxx}, {maxy}, {miny})"
            geom = geom.reverse() if not geom.exterior.is_ccw else geom
        return geom.wkt

    @handle(ast.Equal, ast.NotEqual)
    def equality(self, node, lhs, rhs):
        """
        Creates a term query for equality or inequality conditions.
        """
        rhs = _to_solr_date(rhs)
        if isinstance(rhs, str):
            escaped_rhs = rhs.replace('"', '\\"')
            rhs = f'"{escaped_rhs}"'
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
            low, high = (
                rhs[0].strftime("%Y-%m-%dT%H:%M:%SZ"),
                rhs[1].strftime("%Y-%m-%dT%H:%M:%SZ"),
            )

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
        ast.GeometryEquals,
    )
    def spatial_comparison(
        self, node: ast.SpatialComparisonPredicate, lhs: str, rhs
    ):
        """Creates a spatial query for the given spatial comparison predicate.

        Spatial {!field ...} queries MUST go into the Solr filter[] array, not the
        main query field. When placed in query, Geo3D fields return wrong counts.
        """
        # rhs is None when geometry() detected a global bbox — no filter needed.
        if rhs is None:
            return SolrDSLQuery("*:*")
        op = node.op.value.lower().capitalize()
        geo_filter = f"{{!field f={lhs} v='Intersects({rhs})'}}"
        if op == "Disjoint":
            return SolrDSLQuery("*:*", filters=[f"-{geo_filter}"])
        geo_filter = f"{{!field f={lhs} v='{op}({rhs})'}}"
        return SolrDSLQuery("*:*", filters=[geo_filter])

    @handle(ast.BBox)
    def bbox(self, node: ast.BBox, lhs):
        """Performs a spatial query for the given bounding box.
        Ignores CRS parameter, as it is not supported by Solr.
        """
        bbox = self.envelope(
            values.Envelope(node.minx, node.maxx, node.miny, node.maxy)
        )
        query = f"{{!field f={lhs} v='Intersects({bbox})'}}"
        return SolrDSLQuery("*:*", filters=[query])

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
        """
        Envelope values are converted to an WKT ENVELOPE for Solr.

        If min_x > max_x, solr assume dateline crossing.
        """
        min_x = float(node.x1)
        max_x = float(node.x2)
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
    return SOLRDSLEvaluator(
        attribute_map, Version(str(version)) if version else None
    ).evaluate(root)


def unwrap_query(obj):
    """Extract the inner query from a SolrDSLQuery or return the object directly."""
    if isinstance(obj, SolrDSLQuery):
        # Return the inner query only if it is not empty
        return obj.get("query", {})
    return obj
