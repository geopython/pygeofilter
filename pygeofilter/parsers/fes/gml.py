from owslib.crs import Crs

from .util import handle
from ... import values


NSMAP = {
    "gml": "http://www.opengis.net/gml/3.2"
}


def swap_coordinates_axisorder(coordinates):
    return [
        item
        for sublist in list(zip(coordinates[1::2], coordinates[::2]))
        for item in sublist
    ]


class GML32ParserMixIn:
    namespace = "http://www.opengis.net/gml/3.2"

    @handle('Point', subiter=False)
    def point(self, node):
        crs_name = node.attrib['srsName']
        child = node[0]
        print(child.tag)
        if child.tag == f"{{{NSMAP['gml']}}}pos":
            coordinates = [
                float(v) for v in child.text.split()
            ]
        # TODO: gml:coordinate
        else:
            raise ValueError("Could not find point values")

        crs = Crs(crs_name)
        crs.axisorder
        if crs.axisorder == 'yx':
            coordinates = swap_coordinates_axisorder(coordinates)
            print(coordinates)
        geometry = {
            'type': 'Point',
            'coordinates': coordinates,
        }
        if crs.code != 4326:
            geometry["crs"] = {
                "type": "name",
                "properties": {
                    "name": f"urn:ogc:def:crs:EPSG::{crs.code}"
                }
            }

        return values.Geometry(geometry)
