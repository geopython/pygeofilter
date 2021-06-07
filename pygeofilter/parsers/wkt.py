from lark import Transformer, v_args


@v_args(inline=True)
class WKTTransformer(Transformer):
    def wkt__geometrycollection(self, value):
        pass

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

    def wkt__NUMBER(self, value):
        return float(value)
