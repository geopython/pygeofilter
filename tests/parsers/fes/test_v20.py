import pytest
from pygeofilter.parsers.fes.v20 import parse
from pygeofilter import ast
from pygeofilter import values


xml = """
<fes:Filter xmlns:fes="http://www.opengis.net/fes/2.0" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.opengis.net/fes/2.0 http://schemas.opengis.net/filter/2.0/filterAll.xsd http://www.opengis.net/gml/3.2 http://schemas.opengis.net/gml/3.2.1/gml.xsd">
  <fes:DWithin>
    <fes:ValueReference>geometry</fes:ValueReference>
    <gml:Point gml:id="P1" srsName="urn:ogc:def:crs:EPSG::4326">
      <gml:pos>43.716589 -79.340686</gml:pos>
    </gml:Point>
    <fes:Distance uom="m">10</fes:Distance>
  </fes:DWithin>
</fes:Filter>
"""


def test_1():
    result = parse(xml)

    assert result == ast.DistanceWithin(
        ast.Attribute('geometry'),
        values.Geometry({
            "type": "Point",
            "coordinates": [-79.340686, 43.716589],
        }),
        distance=10,
        units="m",
    )
