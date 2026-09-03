import re

import pytest
from lxml import etree

from pygeofilter import ast, values
from pygeofilter.backends.fes import to_lxml_etree, to_xml_str


def strip_xml(xml_string: str) -> str:
    """Remove newlines and whitespace"""
    xml_string = re.sub(r"\s+<", "<", xml_string)
    xml_string = re.sub(r"\n[ ]{2,}", " ", xml_string).strip()
    return xml_string


def test_strip_xml():
    formatted_xml = """
    <ogc:Filter xmlns:ogc="http://www.opengis.net/ogc"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema-datatypes">
      <ogc:Not>
        <ogc:PropertyIsEqualTo>
          <ogc:PropertyName>attr</ogc:PropertyName>
          <ogc:Literal type="xsd:string">value</ogc:Literal>
        </ogc:PropertyIsEqualTo>
      </ogc:Not>
    </ogc:Filter>
    """
    result = strip_xml(formatted_xml)
    expected = (
        '<ogc:Filter xmlns:ogc="http://www.opengis.net/ogc"'
        ' xmlns:xsd="http://www.w3.org/2001/XMLSchema-datatypes">'
        "<ogc:Not><ogc:PropertyIsEqualTo><ogc:PropertyName>attr"
        '</ogc:PropertyName><ogc:Literal type="xsd:string">'
        "value</ogc:Literal></ogc:PropertyIsEqualTo>"
        "</ogc:Not></ogc:Filter>"
    )
    assert result == expected


def test_and():
    # fmt: off
    expected_xml = strip_xml("""<ogc:Filter xmlns:ogc="http://www.opengis.net/ogc"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema-datatypes">
      <ogc:And>
        <ogc:PropertyIsLessThan>
          <ogc:PropertyName>attr</ogc:PropertyName>
          <ogc:Literal type="xsd:int">30</ogc:Literal>
        </ogc:PropertyIsLessThan>
        <ogc:PropertyIsGreaterThan>
          <ogc:PropertyName>attr</ogc:PropertyName>
          <ogc:Literal type="xsd:int">10</ogc:Literal>
        </ogc:PropertyIsGreaterThan>
      </ogc:And>
    </ogc:Filter>""")

    result = to_xml_str(
        ast.And(
            ast.LessThan(
                ast.Attribute("attr"),
                30,
            ),
            ast.GreaterThan(
                ast.Attribute("attr"),
                10,
            ),
        )
    )
    assert result == expected_xml


def test_or():
    expected_xml = strip_xml("""<Filter>
      <Or>
        <PropertyIsLessThanOrEqualTo>
        <PropertyName>attr</PropertyName>
        <Literal>30.5</Literal>
        </PropertyIsLessThanOrEqualTo>
        <PropertyIsGreaterThanOrEqualTo>
        <PropertyName>attr</PropertyName>
        <Literal>10.5</Literal>
        </PropertyIsGreaterThanOrEqualTo>
      </Or>
    </Filter>""")
    result = to_xml_str(
        ast.Or(
            ast.LessEqual(
                ast.Attribute("attr"),
                30.5,
            ),
            ast.GreaterEqual(
                ast.Attribute("attr"),
                10.5,
            ),
        ),
        namespaces=False,
    )
    assert result == expected_xml


def test_not():
    expected_xml = strip_xml("""<ogc:Filter xmlns:ogc="http://www.opengis.net/ogc"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema-datatypes">
      <ogc:Not>
        <ogc:PropertyIsEqualTo>
          <ogc:PropertyName>attr</ogc:PropertyName>
          <ogc:Literal type="xsd:string">value</ogc:Literal>
        </ogc:PropertyIsEqualTo>
      </ogc:Not>
    </ogc:Filter>""")
    result = to_xml_str(
        ast.Not(
            ast.Equal(
                ast.Attribute("attr"),
                "value",
            )
        )
    )
    assert result == expected_xml


def test_not_equal():
    expected_xml = strip_xml("""<ogc:Filter xmlns:ogc="http://www.opengis.net/ogc"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema-datatypes">
      <ogc:PropertyIsNotEqualTo>
        <ogc:PropertyName>attr</ogc:PropertyName>
        <ogc:Literal type="xsd:string">value</ogc:Literal>
      </ogc:PropertyIsNotEqualTo>
    </ogc:Filter>""")
    result = to_xml_str(ast.NotEqual(ast.Attribute("attr"), "value"))
    assert result == expected_xml


def test_is_like():
    expected_xml = strip_xml("""<ogc:Filter xmlns:ogc="http://www.opengis.net/ogc"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema-datatypes">
      <ogc:PropertyIsLike
          wildCard="%"
          singleChar="."
          escapeChar="\\"
          matchCase="true">
        <ogc:PropertyName>attr</ogc:PropertyName>
        <ogc:Literal type="xsd:string">some%</ogc:Literal>
      </ogc:PropertyIsLike>
    </ogc:Filter>""")
    result = to_xml_str(
        ast.Like(
            ast.Attribute("attr"),
            "some%",
            nocase=False,
            not_=False,
            wildcard="%",
            singlechar=".",
            escapechar="\\",
        )
    )
    assert result == expected_xml

    # case insensitive
    expected_xml = strip_xml("""<ogc:Filter xmlns:ogc="http://www.opengis.net/ogc"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema-datatypes">
      <ogc:PropertyIsLike
          wildCard="%"
          singleChar="."
          escapeChar="\\"
          matchCase="false">
        <ogc:PropertyName>attr</ogc:PropertyName>
        <ogc:Literal type="xsd:string">some%</ogc:Literal>
      </ogc:PropertyIsLike>
    </ogc:Filter>""")
    result = to_xml_str(
        ast.Like(
            ast.Attribute("attr"),
            "some%",
            nocase=True,
            not_=False,
            wildcard="%",
            singlechar=".",
            escapechar="\\",
        )
    )
    assert result == expected_xml


def test_is_null():
    expected_xml = strip_xml("""<ogc:Filter xmlns:ogc="http://www.opengis.net/ogc"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema-datatypes">
      <ogc:PropertyIsNull>
        <ogc:PropertyName>attr</ogc:PropertyName>
      </ogc:PropertyIsNull>
    </ogc:Filter>""")
    result = to_xml_str(ast.IsNull(ast.Attribute("attr"), not_=False))
    assert result == expected_xml

    # Not
    expected_xml = "<Filter><Not><PropertyIsNull><PropertyName>attr</PropertyName></PropertyIsNull></Not></Filter>"  # noqa
    result = to_xml_str(
        ast.IsNull(ast.Attribute("attr"), not_=True), namespaces=False
    )
    assert result == expected_xml


def test_is_between():
    expected_xml = strip_xml("""<ogc:Filter xmlns:ogc="http://www.opengis.net/ogc"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema-datatypes">
      <ogc:PropertyIsBetween>
        <ogc:PropertyName>attr</ogc:PropertyName>
        <ogc:LowerBoundary>
          <ogc:Literal type="xsd:double">10.5</ogc:Literal>
        </ogc:LowerBoundary>
        <ogc:UpperBoundary>
          <ogc:Literal type="xsd:double">11.5</ogc:Literal>
        </ogc:UpperBoundary>
      </ogc:PropertyIsBetween>
    </ogc:Filter>""")
    result = to_xml_str(
        ast.Between(ast.Attribute("attr"), 10.5, 11.5, not_=False)
    )
    assert result == expected_xml


def test_geom_equals():
    expected_xml = strip_xml("""<ogc:Filter xmlns:ogc="http://www.opengis.net/ogc"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema-datatypes">
      <ogc:Equals>
        <ogc:PropertyName>attr</ogc:PropertyName>
        <gml:Point xmlns:gml="http://www.opengis.net/gml/3.2"
                  srsName="http://www.opengis.net/def/crs/epsg/0/4326">
          <gml:pos>1.0 1.0</gml:pos>
        </gml:Point>
      </ogc:Equals>
    </ogc:Filter>""")
    result = to_xml_str(
        ast.GeometryEquals(
            ast.Attribute("attr"),
            values.Geometry(
                {
                    "type": "Point",
                    "coordinates": (1.0, 1.0),
                    "crs": {
                        "type": "name",
                        "properties": {
                            "name": "http://www.opengis.net/def/crs/epsg/0/4326"
                        },
                    },
                }
            ),
        )
    )
    assert result == expected_xml


def test_geom_disjoint():
    expected_xml = strip_xml("""<ogc:Filter xmlns:ogc="http://www.opengis.net/ogc"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema-datatypes">
      <ogc:Disjoint>
        <ogc:PropertyName>attr</ogc:PropertyName>
        <gml:LineString xmlns:gml="http://www.opengis.net/gml/3.2">
          <gml:posList>1.0 1.0 2.0 2.0</gml:posList>
        </gml:LineString>
      </ogc:Disjoint>
    </ogc:Filter>""")
    result = to_xml_str(
        ast.GeometryDisjoint(
            ast.Attribute("attr"),
            values.Geometry(
                {
                    "type": "LineString",
                    "coordinates": [
                        (1.0, 1.0),
                        (2.0, 2.0),
                    ],
                }
            ),
        )
    )
    assert result == expected_xml


def test_geom_touches():
    expected_xml = strip_xml("""<ogc:Filter xmlns:ogc="http://www.opengis.net/ogc"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema-datatypes">
      <ogc:Touches>
        <ogc:PropertyName>attr</ogc:PropertyName>
        <gml:Polygon xmlns:gml="http://www.opengis.net/gml/3.2">
            <gml:exterior>
                <gml:LinearRing>
                    <gml:posList>0.0 0.0 1.0 0.0 0.0 1.0 0.0 0.0</gml:posList>
                </gml:LinearRing>
            </gml:exterior>
            <gml:interior>
                <gml:LinearRing>
                    <gml:posList>0.2 0.2 0.5 0.2 0.2 0.5 0.2 0.2</gml:posList>
                </gml:LinearRing>
            </gml:interior>
        </gml:Polygon>
      </ogc:Touches>
    </ogc:Filter>""")
    result = to_xml_str(
        ast.GeometryTouches(
            ast.Attribute("attr"),
            values.Geometry(
                {
                    "type": "Polygon",
                    "coordinates": [
                        [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0), (0.0, 0.0)],
                        [(0.2, 0.2), (0.5, 0.2), (0.2, 0.5), (0.2, 0.2)],
                    ],
                }
            ),
        )
    )
    assert result == expected_xml


def test_geom_within():
    expected_xml = strip_xml("""<Filter>
    <Within>
        <PropertyName>attr</PropertyName>
        <Polygon>
        <exterior>
            <LinearRing>
            <posList>0.0 1.0 0.0 3.0 2.0 3.0 2.0 1.0 0.0 1.0</posList>
            </LinearRing>
        </exterior>
        </Polygon>
    </Within>
    </Filter>""")
    result = to_xml_str(
        ast.GeometryWithin(
            ast.Attribute("attr"),
            values.Geometry(
                {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            (0.0, 1.0),
                            (0.0, 3.0),
                            (2.0, 3.0),
                            (2.0, 1.0),
                            (0.0, 1.0),
                        ],
                    ],
                }
            ),
        ),
        namespaces=False,
    )
    assert result == expected_xml


def test_geom_overlaps():
    expected_xml = strip_xml("""<Filter>
      <Overlaps>
        <PropertyName>attr</PropertyName>
        <MultiSurface id="id">
          <surfaceMembers>
            <Polygon id="id_0">
              <exterior>
                <LinearRing>
                  <posList>0.0 0.0 1.0 0.0 0.0 1.0 0.0 0.0</posList>
                </LinearRing>
              </exterior>
              <interior>
                <LinearRing>
                  <posList>0.2 0.2 0.5 0.2 0.2 0.5 0.2 0.2</posList>
                </LinearRing>
              </interior>
            </Polygon>
            <Polygon id="id_1">
              <exterior>
                <LinearRing>
                  <posList>10.0 10.0 11.0 10.0 10.0 11.0 10.0 10.0</posList>
                </LinearRing>
              </exterior>
              <interior>
                <LinearRing>
                  <posList>10.2 10.2 10.5 10.2 10.2 10.5 10.2 10.2</posList>
                </LinearRing>
              </interior>
            </Polygon>
          </surfaceMembers>
        </MultiSurface>
      </Overlaps>
    </Filter>""")
    result = to_xml_str(
        ast.GeometryOverlaps(
            ast.Attribute("attr"),
            values.Geometry(
                {
                    "type": "MultiPolygon",
                    "coordinates": [
                        [
                            [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0), (0.0, 0.0)],
                            [(0.2, 0.2), (0.5, 0.2), (0.2, 0.5), (0.2, 0.2)],
                        ],
                        [
                            [
                                (10.0, 10.0),
                                (11.0, 10.0),
                                (10.0, 11.0),
                                (10.0, 10.0),
                            ],
                            [
                                (10.2, 10.2),
                                (10.5, 10.2),
                                (10.2, 10.5),
                                (10.2, 10.2),
                            ],
                        ],
                    ],
                }
            ),
        ),
        namespaces=False,
        gml_identifier="id",
    )
    assert result == expected_xml


def test_geom_crosses():
    expected_xml = strip_xml("""<Filter>
      <Crosses>
        <PropertyName>attr</PropertyName>
        <LineString>
          <posList>2.0 1.0 1.0 2.0</posList>
        </LineString>
      </Crosses>
    </Filter>""")
    result = to_xml_str(
        ast.GeometryCrosses(
            ast.Attribute("attr"),
            values.Geometry(
                {"type": "LineString", "coordinates": [(2.0, 1.0), (1.0, 2.0)]}
            ),
        ),
        namespaces=False,
    )
    assert result == expected_xml


def test_geom_intersects():
    expected_xml = strip_xml("""<Filter>
      <Intersects>
        <PropertyName>attr</PropertyName>
        <Polygon>
          <exterior>
            <LinearRing>
              <posList>0.5 1.0 0.5 2.0 1.5 2.0 1.5 1.0 0.5 1.0</posList>
            </LinearRing>
          </exterior>
        </Polygon>
      </Intersects>
    </Filter>""")
    result = to_xml_str(
        ast.GeometryIntersects(
            ast.Attribute("attr"),
            values.Geometry(
                {
                    "type": "Polygon",
                    "bbox": (0.5, 1.0, 1.5, 2.0),
                    "coordinates": [
                        [
                            (0.5, 1.0),
                            (0.5, 2.0),
                            (1.5, 2.0),
                            (1.5, 1.0),
                            (0.5, 1.0),
                        ]
                    ],
                }
            ),
        ),
        namespaces=False,
    )
    assert result == expected_xml


def test_geom_bbox():
    expected_xml = strip_xml("""<ogc:Filter xmlns:ogc="http://www.opengis.net/ogc"
                xmlns:xsd="http://www.w3.org/2001/XMLSchema-datatypes">
      <ogc:BBOX>
        <ogc:PropertyName>geom_attr</ogc:PropertyName>
        <gml:Envelope xmlns:gml="http://www.opengis.net/gml/3.2" srsName="epsg:4306">
          <ogc:lowerCorner>13.0983 31.5899</ogc:lowerCorner>
          <ogc:upperCorner>35.5472 42.8143</ogc:upperCorner>
        </gml:Envelope>
      </ogc:BBOX>
    </ogc:Filter>""")
    result = to_xml_str(
        ast.BBox(
            lhs=ast.Attribute("geom_attr"),
            minx=13.0983,
            miny=31.5899,
            maxx=35.5472,
            maxy=42.8143,
            crs="epsg:4306",
        ), namespaces=True
    )
    assert result == expected_xml


    # no namespaces
    expected_xml = strip_xml("""<Filter>
      <BBOX>
        <PropertyName>geom_attr</PropertyName>
        <Envelope srsName="epsg:4306">
          <lowerCorner>13.0983 31.5899</lowerCorner>
          <upperCorner>35.5472 42.8143</upperCorner>
        </Envelope>
      </BBOX>
    </Filter>""")
    result = to_xml_str(
        ast.BBox(
            lhs=ast.Attribute("geom_attr"),
            minx=13.0983,
            miny=31.5899,
            maxx=35.5472,
            maxy=42.8143,
            crs="epsg:4306",
        ), namespaces=False
    )
    assert result == expected_xml

def test_geom_contains():
    expected_xml = strip_xml("""<Filter>
      <Contains>
        <PropertyName>attr</PropertyName>
        <Polygon>
          <exterior>
            <LinearRing>
              <posList>0.5 1.0 0.5 2.0 1.5 2.0 1.5 1.0 0.5 1.0</posList>
            </LinearRing>
          </exterior>
        </Polygon>
      </Contains>
    </Filter>""")
    result = to_xml_str(
        ast.GeometryContains(
            ast.Attribute("attr"),
            values.Geometry(
                {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            (0.5, 1.0),
                            (0.5, 2.0),
                            (1.5, 2.0),
                            (1.5, 1.0),
                            (0.5, 1.0),
                        ]
                    ],
                }
            ),
        ),
        namespaces=False,
    )
    assert result == expected_xml


def test_geom_dwithin():
    expected_xml = strip_xml("""<Filter>
      <Dwithin>
        <PropertyName>attr</PropertyName>
        <Point srsName="http://www.opengis.net/def/crs/EPSG/0/28992">
          <pos>142898.9 473511.1</pos>
        </Point>
        <Distance uom="km">10</Distance>
      </Dwithin>
    </Filter>""")
    result = to_xml_str(
        ast.DistanceWithin(
            ast.Attribute("attr"),
            values.Geometry(
                {
                    "type": "Point",
                    "coordinates": (142898.9, 473511.1),
                    "crs": {
                        "type": "name",
                        "properties": {
                            "name": "http://www.opengis.net/def/crs/EPSG/0/28992"
                        },
                    },
                }
            ),
            distance=10,
            units="km",
        ),
        namespaces=False,
    )
    assert result == expected_xml


def test_aritmethic():
    expected_xml = strip_xml("""<Filter>
      <PropertyIsEqualTo>
        <PropertyName>PROPA</PropertyName>
        <Add>
          <PropertyName>PROPB</PropertyName>
          <Literal>100</Literal>
        </Add>
      </PropertyIsEqualTo>
    </Filter>""")
    result = to_xml_str(
        ast.Equal(ast.Attribute("PROPA"), ast.Add(ast.Attribute("PROPB"), 100)),
        namespaces=False,
    )
    assert result == expected_xml


def test_function():
    expected_xml = strip_xml("""<Filter>
      <PropertyIsEqualTo>
        <Function name="SIN">
          <PropertyName>DISPERSION_ANGLE</PropertyName>
        </Function>
        <Literal>1</Literal>
      </PropertyIsEqualTo>
    </Filter>""")
    result = to_xml_str(
        ast.Equal(ast.Function("SIN", [ast.Attribute("DISPERSION_ANGLE")]), 1),
        namespaces=False,
    )
    assert result == expected_xml


def test_xml_tree():
    xml_str = """<Filter>
      <PropertyIsEqualTo>
        <Function name="SIN">
          <PropertyName>DISPERSION_ANGLE</PropertyName>
        </Function>
        <Literal>1</Literal>
      </PropertyIsEqualTo>
    </Filter>"""
    result = to_lxml_etree(
        ast.Equal(ast.Function("SIN", [ast.Attribute("DISPERSION_ANGLE")]), 1),
        namespaces=False,
    )
    assert type(result) is etree._Element
    assert etree.tostring(result, encoding="unicode") == strip_xml(xml_str)


def test_v20():
    with pytest.raises(NotImplementedError):
        to_xml_str(None, fes_version="v2.0")  # type: ignore
