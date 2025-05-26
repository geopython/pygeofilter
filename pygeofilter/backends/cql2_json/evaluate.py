# ------------------------------------------------------------------------------
#
# Project: pygeofilter <https://github.com/geopython/pygeofilter>
# Authors: Fabian Schindler <fabian.schindler@eox.at>,
# David Bitner <bitner@dbspatial.com>
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

import json
from datetime import date, datetime
from typing import Dict, Optional

from ... import ast, values
from ...cql2 import get_op
from ..evaluator import Evaluator, handle


def json_serializer(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if hasattr(obj, "name"):
        return obj.name
    raise TypeError(f"{obj} with type {type(obj)} is not serializable.")


class CQL2Evaluator(Evaluator):
    def __init__(
        self,
        attribute_map: Optional[Dict[str, str]],
        function_map: Optional[Dict[str, str]],
    ):
        self.attribute_map = attribute_map
        self.function_map = function_map

    @handle(
        ast.Condition,
        ast.Comparison,
        ast.TemporalPredicate,
        ast.SpatialComparisonPredicate,
        ast.Arithmetic,
        ast.ArrayPredicate,
        subclasses=True,
    )
    def comparison(self, node, *args):
        op = get_op(node)
        return {"op": op, "args": [*args]}

    @handle(ast.Between)
    def between(self, node, lhs, low, high):
        return {"op": "between", "args": [lhs, [low, high]]}

    @handle(ast.Like)
    def like(self, node, *subargs):
        return {"op": "like", "args": [subargs[0], node.pattern]}

    @handle(ast.IsNull)
    def isnull(self, node, arg):
        ret = {"op": "isNull", "args": [arg]}
        if node.not_:
            ret = {"op": "not", "args": [ret]}
        return ret

    @handle(ast.Function)
    def function(self, node, *args):
        name = node.name.lower()
        if name == "lower":
            ret = {"lower": args[0]}
        elif name == "upper":
            ret = {"upper": args[0]}
        else:
            ret = {"function": name, "args": [*args]}
        return ret

    @handle(ast.In)
    def in_(self, node, lhs, *options):
        return {"op": "in", "args": [lhs, options]}

    @handle(ast.Attribute)
    def attribute(self, node: ast.Attribute):
        return {"property": node.name}

    @handle(values.Interval)
    def interval(self, node: values.Interval, start, end):
        return {"interval": [start, end]}

    @handle(datetime)
    def datetime(self, node: ast.Attribute):
        return {"timestamp": node.name}

    @handle(*values.LITERALS)
    def literal(self, node):
        return node

    @handle(values.Geometry)
    def geometry(self, node: values.Geometry):
        return node.__geo_interface__

    @handle(values.Envelope)
    def envelope(self, node: values.Envelope):
        return node.__geo_interface__


def to_cql2(
    root: ast.Node,
    field_mapping: Optional[Dict[str, str]] = None,
    function_map: Optional[Dict[str, str]] = None,
) -> str:
    return json.dumps(
        CQL2Evaluator(field_mapping, function_map).evaluate(root),
        default=json_serializer,
    )
