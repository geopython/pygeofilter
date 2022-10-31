from datetime import datetime, timedelta

from dateparser.timezone_parser import StaticTzInfo

from pygeofilter import ast, values
from pygeofilter.parsers.fes.v20 import parse


def test_and():
    result = parse(
        """
    <fes:Filter xmlns:fes="http://www.opengis.net/fes/2.0"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema-datatypes">
      <fes:And>
        <fes:PropertyIsLessThan>
          <fes:ValueReference>attr</fes:ValueReference>
          <fes:Literal type="xsd:int">30</fes:Literal>
        </fes:PropertyIsLessThan>
        <fes:PropertyIsGreaterThan>
          <fes:ValueReference>attr</fes:ValueReference>
          <fes:Literal type="xsd:int">10</fes:Literal>
        </fes:PropertyIsGreaterThan>
      </fes:And>
    </fes:Filter>
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
    <fes:Filter xmlns:fes="http://www.opengis.net/fes/2.0"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema-datatypes">
      <fes:Or>
        <fes:PropertyIsLessThanOrEqualTo>
          <fes:ValueReference>attr</fes:ValueReference>
          <fes:Literal type="xsd:double">30.5</fes:Literal>
        </fes:PropertyIsLessThanOrEqualTo>
        <fes:PropertyIsGreaterThanOrEqualTo>
          <fes:ValueReference>attr</fes:ValueReference>
          <fes:Literal type="xsd:double">10.5</fes:Literal>
        </fes:PropertyIsGreaterThanOrEqualTo>
      </fes:Or>
    </fes:Filter>
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
    <fes:Filter xmlns:fes="http://www.opengis.net/fes/2.0"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema-datatypes">
      <fes:Not>
        <fes:PropertyIsEqualTo>
          <fes:ValueReference>attr</fes:ValueReference>
          <fes:Literal type="xsd:string">value</fes:Literal>
        </fes:PropertyIsEqualTo>
      </fes:Not>
    </fes:Filter>
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
    <fes:Filter xmlns:fes="http://www.opengis.net/fes/2.0"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema-datatypes">
      <fes:PropertyIsNotEqualTo>
        <fes:ValueReference>attr</fes:ValueReference>
        <fes:Literal type="xsd:string">value</fes:Literal>
      </fes:PropertyIsNotEqualTo>
    </fes:Filter>
    """
    )
    assert result == ast.NotEqual(
        ast.Attribute("attr"),
        "value",
    )


def test_is_like():
    result = parse(
        """
    <fes:Filter xmlns:fes="http://www.opengis.net/fes/2.0"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema-datatypes">
      <fes:PropertyIsLike
          wildCard="%"
          singleChar="."
          escapeChar="\\"
          matchCase="true">
        <fes:ValueReference>attr</fes:ValueReference>
        <fes:Literal type="xsd:string">some%</fes:Literal>
      </fes:PropertyIsLike>
    </fes:Filter>
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
    <fes:Filter xmlns:fes="http://www.opengis.net/fes/2.0"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema-datatypes">
      <fes:PropertyIsLike
          wildCard="%"
          singleChar="."
          escapeChar="\\"
          matchCase="false">
        <fes:ValueReference>attr</fes:ValueReference>
        <fes:Literal type="xsd:string">some%</fes:Literal>
      </fes:PropertyIsLike>
    </fes:Filter>
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
    <fes:Filter xmlns:fes="http://www.opengis.net/fes/2.0"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema-datatypes">
      <fes:PropertyIsNull>
        <fes:ValueReference>attr</fes:ValueReference>
      </fes:PropertyIsNull>
    </fes:Filter>
    """
    )
    assert result == ast.IsNull(
        ast.Attribute("attr"),
        not_=False,
    )


def test_is_between():
    result = parse(
        """
    <fes:Filter xmlns:fes="http://www.opengis.net/fes/2.0"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema-datatypes">
      <fes:PropertyIsBetween>
        <fes:ValueReference>attr</fes:ValueReference>
        <fes:LowerBoundary>
          <fes:Literal type="xsd:double">10.5</fes:Literal>
        </fes:LowerBoundary>
        <fes:UpperBoundary>
          <fes:Literal type="xsd:double">11.5</fes:Literal>
        </fes:UpperBoundary>
      </fes:PropertyIsBetween>
    </fes:Filter>
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
    <fes:Filter xmlns:fes="http://www.opengis.net/fes/2.0"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema-datatypes">
      <fes:Equals>
        <fes:ValueReference>attr</fes:ValueReference>
        <gml:Point gml:id="ID"
            srsName="http://www.opengis.net/def/crs/epsg/0/4326"
            xmlns:gml="http://www.opengis.net/gml">
          <gml:pos>1.0 1.0</gml:pos>
        </gml:Point>
      </fes:Equals>
    </fes:Filter>
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
    <fes:Filter xmlns:fes="http://www.opengis.net/fes/2.0"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema-datatypes">
      <fes:Disjoint>
        <fes:ValueReference>attr</fes:ValueReference>
        <gml:LineString xmlns:gml="http://www.opengis.net/gml">
          <gml:posList>1.0 1.0 2.0 2.0</gml:posList>
        </gml:LineString>
      </fes:Disjoint>
    </fes:Filter>
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
    <fes:Filter xmlns:fes="http://www.opengis.net/fes/2.0"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema-datatypes">
      <fes:Touches>
        <fes:ValueReference>attr</fes:ValueReference>
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
      </fes:Touches>
    </fes:Filter>
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
    <fes:Filter xmlns:fes="http://www.opengis.net/fes/2.0"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema-datatypes">
      <fes:Within>
        <fes:ValueReference>attr</fes:ValueReference>
        <gml:Envelope xmlns:gml="http://www.opengis.net/gml">
          <gml:lowerCorner>0.0 1.0</gml:lowerCorner>
          <gml:upperCorner>2.0 3.0</gml:upperCorner>
        </gml:Envelope>
      </fes:Within>
    </fes:Filter>
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
    <fes:Filter xmlns:fes="http://www.opengis.net/fes/2.0"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema-datatypes">
      <fes:Overlaps>
        <fes:ValueReference>attr</fes:ValueReference>
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
      </fes:Overlaps>
    </fes:Filter>
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
    <fes:Filter xmlns:fes="http://www.opengis.net/fes/2.0"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema-datatypes">
      <fes:Crosses>
        <fes:ValueReference>attr</fes:ValueReference>
        <georss:line xmlns:georss="http://www.georss.org/georss">
            1.0 2.0 2.0 1.0
        </georss:line>
      </fes:Crosses>
    </fes:Filter>
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
    <fes:Filter xmlns:fes="http://www.opengis.net/fes/2.0"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema-datatypes">
      <fes:Intersects>
        <fes:ValueReference>attr</fes:ValueReference>
        <georss:box xmlns:georss="http://www.georss.org/georss">
            1.0 0.5 2.0 1.5
        </georss:box>
      </fes:Intersects>
    </fes:Filter>
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
    <fes:Filter xmlns:fes="http://www.opengis.net/fes/2.0"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema-datatypes">
      <fes:Contains>
        <fes:ValueReference>attr</fes:ValueReference>
        <georss:polygon xmlns:georss="http://www.georss.org/georss">
            1.0 0.5 2.0 0.5 2.0 1.5 1.0 1.5 1.0 0.5
        </georss:polygon>
      </fes:Contains>
    </fes:Filter>
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
    <fes:Filter xmlns:fes="http://www.opengis.net/fes/2.0"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema-datatypes">
      <fes:DWithin>
        <fes:ValueReference>attr</fes:ValueReference>
        <georss:point xmlns:georss="http://www.georss.org/georss">
            1.0 1.0
        </georss:point>
        <fes:Distance uom="m">10</fes:Distance>
      </fes:DWithin>
    </fes:Filter>
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


def test_after():
    result = parse(
        """
    <fes:Filter xmlns:fes="http://www.opengis.net/fes/2.0"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema-datatypes"
        xmlns:gml="http://www.opengis.net/gml">
      <fes:After>
        <fes:ValueReference>attr</fes:ValueReference>
        <gml:TimeInstant>
          <gml:timePosition>2000-01-01T00:00:00Z</gml:timePosition>
        </gml:TimeInstant>
      </fes:After>
    </fes:Filter>
    """
    )
    assert result == ast.TimeAfter(
        ast.Attribute("attr"),
        datetime(2000, 1, 1, 0, 0, 0, tzinfo=StaticTzInfo("Z", timedelta(0))),
    )


def test_before():
    # using timePosition directly
    result = parse(
        """
    <fes:Filter xmlns:fes="http://www.opengis.net/fes/2.0"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema-datatypes"
        xmlns:gml="http://www.opengis.net/gml">
      <fes:Before>
        <fes:ValueReference>attr</fes:ValueReference>
        <gml:timePosition>2000-01-01T00:00:00Z</gml:timePosition>
      </fes:Before>
    </fes:Filter>
    """
    )
    assert result == ast.TimeBefore(
        ast.Attribute("attr"),
        datetime(2000, 1, 1, 0, 0, 0, tzinfo=StaticTzInfo("Z", timedelta(0))),
    )


def test_begins():
    # using timePosition directly
    result = parse(
        """
    <fes:Filter xmlns:fes="http://www.opengis.net/fes/2.0"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema-datatypes"
        xmlns:gml="http://www.opengis.net/gml">
      <fes:Begins>
        <fes:ValueReference>attr</fes:ValueReference>
        <gml:TimePeriod>
          <gml:begin>
            <gml:TimeInstant>
              <gml:timePosition>2000-01-01T00:00:00Z</gml:timePosition>
            </gml:TimeInstant>
          </gml:begin>
          <gml:end>
            <gml:TimeInstant>
              <gml:timePosition>2001-01-01T00:00:00Z</gml:timePosition>
            </gml:TimeInstant>
          </gml:end>
        </gml:TimePeriod>
      </fes:Begins>
    </fes:Filter>
    """
    )
    assert result == ast.TimeBegins(
        ast.Attribute("attr"),
        values.Interval(
            datetime(2000, 1, 1, 0, 0, 0, tzinfo=StaticTzInfo("Z", timedelta(0))),
            datetime(2001, 1, 1, 0, 0, 0, tzinfo=StaticTzInfo("Z", timedelta(0))),
        ),
    )
