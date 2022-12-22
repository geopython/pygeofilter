from pygeofilter import ast, values
from pygeofilter.parsers.fes.v11 import parse


def test_and():
    result = parse(
        """
    <ogc:Filter xmlns:ogc="http://www.opengis.net/ogc"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema-datatypes">
      <ogc:And>
        <ogc:PropertyIsLessThan>
          <ogc:ValueReference>attr</ogc:ValueReference>
          <ogc:Literal type="xsd:int">30</ogc:Literal>
        </ogc:PropertyIsLessThan>
        <ogc:PropertyIsGreaterThan>
          <ogc:ValueReference>attr</ogc:ValueReference>
          <ogc:Literal type="xsd:int">10</ogc:Literal>
        </ogc:PropertyIsGreaterThan>
      </ogc:And>
    </ogc:Filter>
    """
    )
    assert result == ast.And(
        ast.LessThan(
            ast.Attribute("attr"),
            30,
        ),
        ast.GreaterThan(
            ast.Attribute("attr"),
            10,
        ),
    )


def test_or():
    result = parse(
        """
    <ogc:Filter xmlns:ogc="http://www.opengis.net/ogc"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema-datatypes">
      <ogc:Or>
        <ogc:PropertyIsLessThanOrEqualTo>
          <ogc:ValueReference>attr</ogc:ValueReference>
          <ogc:Literal type="xsd:double">30.5</ogc:Literal>
        </ogc:PropertyIsLessThanOrEqualTo>
        <ogc:PropertyIsGreaterThanOrEqualTo>
          <ogc:ValueReference>attr</ogc:ValueReference>
          <ogc:Literal type="xsd:double">10.5</ogc:Literal>
        </ogc:PropertyIsGreaterThanOrEqualTo>
      </ogc:Or>
    </ogc:Filter>
    """
    )
    assert result == ast.Or(
        ast.LessEqual(
            ast.Attribute("attr"),
            30.5,
        ),
        ast.GreaterEqual(
            ast.Attribute("attr"),
            10.5,
        ),
    )


def test_not():
    result = parse(
        """
    <ogc:Filter xmlns:ogc="http://www.opengis.net/ogc"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema-datatypes">
      <ogc:Not>
        <ogc:PropertyIsEqualTo>
          <ogc:ValueReference>attr</ogc:ValueReference>
          <ogc:Literal type="xsd:string">value</ogc:Literal>
        </ogc:PropertyIsEqualTo>
      </ogc:Not>
    </ogc:Filter>
    """
    )
    assert result == ast.Not(
        ast.Equal(
            ast.Attribute("attr"),
            "value",
        ),
    )


def test_not_equal():
    result = parse(
        """
    <ogc:Filter xmlns:ogc="http://www.opengis.net/ogc"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema-datatypes">
      <ogc:PropertyIsNotEqualTo>
        <ogc:ValueReference>attr</ogc:ValueReference>
        <ogc:Literal type="xsd:string">value</ogc:Literal>
      </ogc:PropertyIsNotEqualTo>
    </ogc:Filter>
    """
    )
    assert result == ast.NotEqual(
        ast.Attribute("attr"),
        "value",
    )


def test_is_like():
    result = parse(
        """
    <ogc:Filter xmlns:ogc="http://www.opengis.net/ogc"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema-datatypes">
      <ogc:PropertyIsLike
          wildCard="%"
          singleChar="."
          escapeChar="\\"
          matchCase="true">
        <ogc:ValueReference>attr</ogc:ValueReference>
        <ogc:Literal type="xsd:string">some%</ogc:Literal>
      </ogc:PropertyIsLike>
    </ogc:Filter>
    """
    )
    assert result == ast.Like(
        ast.Attribute("attr"),
        "some%",
        nocase=False,
        not_=False,
        wildcard="%",
        singlechar=".",
        escapechar="\\",
    )

    # case insensitive
    result = parse(
        """
    <ogc:Filter xmlns:ogc="http://www.opengis.net/ogc"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema-datatypes">
      <ogc:PropertyIsLike
          wildCard="%"
          singleChar="."
          escapeChar="\\"
          matchCase="false">
        <ogc:ValueReference>attr</ogc:ValueReference>
        <ogc:Literal type="xsd:string">some%</ogc:Literal>
      </ogc:PropertyIsLike>
    </ogc:Filter>
    """
    )
    assert result == ast.Like(
        ast.Attribute("attr"),
        "some%",
        nocase=True,
        not_=False,
        wildcard="%",
        singlechar=".",
        escapechar="\\",
    )


def test_is_null():
    result = parse(
        """
    <ogc:Filter xmlns:ogc="http://www.opengis.net/ogc"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema-datatypes">
      <ogc:PropertyIsNull>
        <ogc:ValueReference>attr</ogc:ValueReference>
      </ogc:PropertyIsNull>
    </ogc:Filter>
    """
    )
    assert result == ast.IsNull(
        ast.Attribute("attr"),
        not_=False,
    )


def test_is_between():
    result = parse(
        """
    <ogc:Filter xmlns:ogc="http://www.opengis.net/ogc"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema-datatypes">
      <ogc:PropertyIsBetween>
        <ogc:ValueReference>attr</ogc:ValueReference>
        <ogc:LowerBoundary>
          <ogc:Literal type="xsd:double">10.5</ogc:Literal>
        </ogc:LowerBoundary>
        <ogc:UpperBoundary>
          <ogc:Literal type="xsd:double">11.5</ogc:Literal>
        </ogc:UpperBoundary>
      </ogc:PropertyIsBetween>
    </ogc:Filter>
    """
    )
    assert result == ast.Between(
        ast.Attribute("attr"),
        10.5,
        11.5,
        not_=False,
    )


def test_geom_equals():
    result = parse(
        """
    <ogc:Filter xmlns:ogc="http://www.opengis.net/ogc"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema-datatypes">
      <ogc:Equals>
        <ogc:ValueReference>attr</ogc:ValueReference>
        <gml:Point gml:id="ID"
            srsName="http://www.opengis.net/def/crs/epsg/0/4326"
            xmlns:gml="http://www.opengis.net/gml">
          <gml:pos>1.0 1.0</gml:pos>
        </gml:Point>
      </ogc:Equals>
    </ogc:Filter>
    """
    )
    assert result == ast.GeometryEquals(
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


def test_geom_disjoint():
    result = parse(
        """
    <ogc:Filter xmlns:ogc="http://www.opengis.net/ogc"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema-datatypes">
      <ogc:Disjoint>
        <ogc:ValueReference>attr</ogc:ValueReference>
        <gml:LineString xmlns:gml="http://www.opengis.net/gml">
          <gml:posList>1.0 1.0 2.0 2.0</gml:posList>
        </gml:LineString>
      </ogc:Disjoint>
    </ogc:Filter>
    """
    )
    assert result == ast.GeometryDisjoint(
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


def test_geom_touches():
    result = parse(
        """
    <ogc:Filter xmlns:ogc="http://www.opengis.net/ogc"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema-datatypes">
      <ogc:Touches>
        <ogc:ValueReference>attr</ogc:ValueReference>
        <gml:Polygon xmlns:gml="http://www.opengis.net/gml">
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
    </ogc:Filter>
    """
    )
    assert result == ast.GeometryTouches(
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


def test_geom_within():
    result = parse(
        """
    <ogc:Filter xmlns:ogc="http://www.opengis.net/ogc"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema-datatypes">
      <ogc:Within>
        <ogc:ValueReference>attr</ogc:ValueReference>
        <gml:Envelope xmlns:gml="http://www.opengis.net/gml">
          <gml:lowerCorner>0.0 1.0</gml:lowerCorner>
          <gml:upperCorner>2.0 3.0</gml:upperCorner>
        </gml:Envelope>
      </ogc:Within>
    </ogc:Filter>
    """
    )
    assert result == ast.GeometryWithin(
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
    )


def test_geom_overlaps():
    result = parse(
        """
    <ogc:Filter xmlns:ogc="http://www.opengis.net/ogc"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema-datatypes">
      <ogc:Overlaps>
        <ogc:ValueReference>attr</ogc:ValueReference>
        <gml:MultiSurface xmlns:gml="http://www.opengis.net/gml">
            <gml:surfaceMember>
                <gml:Polygon>
                    <gml:exterior>
                        <gml:LinearRing>
                            <gml:posList>0.0 0.0 1.0 0.0 0.0 1.0 0.0 0.0
                            </gml:posList>
                        </gml:LinearRing>
                    </gml:exterior>
                    <gml:interior>
                        <gml:LinearRing>
                            <gml:posList>0.2 0.2 0.5 0.2 0.2 0.5 0.2 0.2
                            </gml:posList>
                        </gml:LinearRing>
                    </gml:interior>
                </gml:Polygon>
            </gml:surfaceMember>
            <gml:surfaceMember>
                <gml:Polygon>
                    <gml:exterior>
                        <gml:LinearRing>
                            <gml:posList>
                                10.0 10.0 11.0 10.0 10.0 11.0 10.0 10.0
                            </gml:posList>
                        </gml:LinearRing>
                    </gml:exterior>
                    <gml:interior>
                        <gml:LinearRing>
                            <gml:posList>
                                10.2 10.2 10.5 10.2 10.2 10.5 10.2 10.2
                            </gml:posList>
                        </gml:LinearRing>
                    </gml:interior>
                </gml:Polygon>
            </gml:surfaceMember>
        </gml:MultiSurface>
      </ogc:Overlaps>
    </ogc:Filter>
    """
    )
    assert result == ast.GeometryOverlaps(
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
                        [(10.0, 10.0), (11.0, 10.0), (10.0, 11.0), (10.0, 10.0)],
                        [(10.2, 10.2), (10.5, 10.2), (10.2, 10.5), (10.2, 10.2)],
                    ],
                ],
            }
        ),
    )


def test_geom_crosses():
    result = parse(
        """
    <ogc:Filter xmlns:ogc="http://www.opengis.net/ogc"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema-datatypes">
      <ogc:Crosses>
        <ogc:ValueReference>attr</ogc:ValueReference>
        <georss:line xmlns:georss="http://www.georss.org/georss">
            1.0 2.0 2.0 1.0
        </georss:line>
      </ogc:Crosses>
    </ogc:Filter>
    """
    )
    assert result == ast.GeometryCrosses(
        ast.Attribute("attr"),
        values.Geometry(
            {"type": "LineString", "coordinates": [(2.0, 1.0), (1.0, 2.0)]}
        ),
    )


def test_geom_intersects():
    result = parse(
        """
    <ogc:Filter xmlns:ogc="http://www.opengis.net/ogc"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema-datatypes">
      <ogc:Intersects>
        <ogc:ValueReference>attr</ogc:ValueReference>
        <georss:box xmlns:georss="http://www.georss.org/georss">
            1.0 0.5 2.0 1.5
        </georss:box>
      </ogc:Intersects>
    </ogc:Filter>
    """
    )
    assert result == ast.GeometryIntersects(
        ast.Attribute("attr"),
        values.Geometry(
            {
                "type": "Polygon",
                "bbox": (0.5, 1.0, 1.5, 2.0),
                "coordinates": [
                    [(0.5, 1.0), (0.5, 2.0), (1.5, 2.0), (1.5, 1.0), (0.5, 1.0)]
                ],
            }
        ),
    )


def test_geom_contains():
    result = parse(
        """
    <ogc:Filter xmlns:ogc="http://www.opengis.net/ogc"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema-datatypes">
      <ogc:Contains>
        <ogc:ValueReference>attr</ogc:ValueReference>
        <georss:polygon xmlns:georss="http://www.georss.org/georss">
            1.0 0.5 2.0 0.5 2.0 1.5 1.0 1.5 1.0 0.5
        </georss:polygon>
      </ogc:Contains>
    </ogc:Filter>
    """
    )
    assert result == ast.GeometryContains(
        ast.Attribute("attr"),
        values.Geometry(
            {
                "type": "Polygon",
                "coordinates": [
                    [(0.5, 1.0), (0.5, 2.0), (1.5, 2.0), (1.5, 1.0), (0.5, 1.0)]
                ],
            }
        ),
    )


def test_geom_dwithin():
    result = parse(
        """
    <ogc:Filter xmlns:ogc="http://www.opengis.net/ogc"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema-datatypes">
      <ogc:DWithin>
        <ogc:ValueReference>attr</ogc:ValueReference>
        <georss:point xmlns:georss="http://www.georss.org/georss">
            1.0 1.0
        </georss:point>
        <ogc:Distance uom="m">10</ogc:Distance>
      </ogc:DWithin>
    </ogc:Filter>
    """
    )
    assert result == ast.DistanceWithin(
        ast.Attribute("attr"),
        values.Geometry(
            {
                "type": "Point",
                "coordinates": (1.0, 1.0),
            }
        ),
        distance=10,
        units="m",
    )
