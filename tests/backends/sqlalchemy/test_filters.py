from typing import cast

import pytest

from pygeofilter.backends.sqlalchemy import filters


@pytest.mark.parametrize(
    "geom, expected",
    [
        pytest.param(
            {"type": "Point", "coordinates": [10, 12]},
            "ST_GeomFromEWKT('SRID=4326;POINT (10 12)')",
            id="without-crs",
        ),
        pytest.param(
            {
                "type": "Point",
                "coordinates": [1, 2],
                "crs": {
                    "type": "name",
                    "properties": {"name": "urn:ogc:def:crs:EPSG::3004"},
                },
            },
            "ST_GeomFromEWKT('SRID=3004;POINT (1 2)')",
            id="with-crs-urn",
        ),
        pytest.param(
            {
                "type": "Point",
                "coordinates": [1, 2],
                "crs": {
                    "type": "name",
                    "properties": {
                        "name": "http://www.opengis.net/def/crs/EPSG/0/3004"
                    },
                },
            },
            "ST_GeomFromEWKT('SRID=3004;POINT (1 2)')",
            id="with-crs-url",
        ),
        pytest.param(
            {
                "type": "Point",
                "coordinates": [1, 2],
                "crs": {
                    "type": "name",
                    "properties": {
                        "name": "https://www.opengis.net/def/crs/OGC/1.3/CRS83"
                    },
                },
            },
            "ST_GeomFromEWKT('SRID=4269;POINT (1 2)')",
            id="with-crs83-url",
        ),
    ],
)
def test_parse_geometry(geom, expected):
    parsed = filters.parse_geometry(cast(dict, geom))
    result = str(parsed.compile(compile_kwargs={"literal_binds": True}))
    assert result == expected


@pytest.mark.parametrize(
    "identifier, expected_srid",
    [
        ("urn:ogc:def:crs:EPSG:6.6:3004", 3004),
        ("http://www.opengis.net/gml/srs/epsg.xml#3004", 3004),
        ("EPSG:3857", 3857),
        ("urn:ogc:def:crs:OGC:1.3:CRS84", 4326),
    ],
)
def test_parse_geometry_srid(identifier, expected_srid):
    geometry = {
        "type": "Point",
        "coordinates": [1, 2],
        "crs": {"type": "name", "properties": {"name": identifier}},
    }
    parsed = filters.parse_geometry(geometry)
    result = str(parsed.compile(compile_kwargs={"literal_binds": True}))
    assert result == f"ST_GeomFromEWKT('SRID={expected_srid};POINT (1 2)')"


def test_parse_geometry_invalid_crs():
    geometry = {
        "type": "Point",
        "coordinates": [1, 2],
        "crs": {"type": "name", "properties": {"name": "not-a-crs"}},
    }
    with pytest.raises(ValueError, match="Could not extract an EPSG SRID"):
        filters.parse_geometry(geometry)
