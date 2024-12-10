# ------------------------------------------------------------------------------
#
# Project: pygeofilter <https://github.com/geopython/pygeofilter>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
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

from lark import Transformer, v_args


@v_args(meta=False, inline=True)
class WKTTransformer(Transformer):
    def wkt__geometry_with_srid(self, srid, geometry):
        print(srid, geometry)
        geometry["crs"] = {
            "type": "name",
            "properties": {"name": f"urn:ogc:def:crs:EPSG::{srid}"},
        }
        return geometry

    def wkt__geometrycollection(self, *geometries):
        return {"type": "GeometryCollection", "geometries": geometries}

    def wkt__point(self, coordinates):
        return {
            "type": "Point",
            "coordinates": coordinates,
        }

    def wkt__linestring(self, coordinate_list):
        return {
            "type": "LineString",
            "coordinates": coordinate_list,
        }

    def wkt__polygon(self, coordinate_lists):
        return {
            "type": "Polygon",
            "coordinates": coordinate_lists,
        }

    def wkt__multipoint(self, coordinates):
        return {
            "type": "MultiPoint",
            "coordinates": coordinates,
        }

    def wkt__multipoint_2(self, *coordinates):
        print(coordinates)
        return {
            "type": "MultiPoint",
            "coordinates": coordinates,
        }

    def wkt__multilinestring(self, coordinate_lists):
        return {
            "type": "MultiLineString",
            "coordinates": coordinate_lists,
        }

    def wkt__multipolygon(self, *coordinate_lists):
        return {
            "type": "MultiPolygon",
            "coordinates": coordinate_lists,
        }

    def wkt__coordinate_lists(self, *coordinate_lists):
        return coordinate_lists

    def wkt__coordinate_list(self, coordinate_list, coordinate):
        return coordinate_list + (coordinate,)

    def wkt__coordinate_list_start(self, coordinate_list):
        return (coordinate_list,)

    def wkt__coordinate(self, *components):
        return components

    def wkt__SIGNED_NUMBER(self, value):
        return float(value)

    def wkt__NUMBER(self, value):
        return float(value)
