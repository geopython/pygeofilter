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
            "ST_GeomFromEWKT('SRID=4326;POINT (1 2)')",
            id="with-crs83-url",
        ),
    ],
)
def test_parse_geometry(geom, expected):
    parsed = filters.parse_geometry(cast(dict, geom))
    result = str(parsed.compile(compile_kwargs={"literal_binds": True}))
    assert result == expected


@pytest.mark.parametrize(
    "identifier, expected",
    [
        # URN form
        ("urn:ogc:def:crs:EPSG::4326", 4326),
        ("urn:ogc:def:crs:EPSG::3004", 3004),
        ("urn:ogc:def:crs:EPSG:1.3:3035", 3035),
        # URL form (http and https)
        ("http://www.opengis.net/def/crs/EPSG/0/4326", 4326),
        ("https://www.opengis.net/def/crs/EPSG/0/3004", 3004),
        # CRS83/CRS84 are the OGC axis-order variants of EPSG:4326
        ("https://www.opengis.net/def/crs/OGC/1.3/CRS83", 4326),
        ("urn:ogc:def:crs:OGC:1.3:CRS84", 4326),
        # Unknown identifier should raise
        pytest.param("urn:ogc:def:crs:UNKNOWN::abc", ValueError, id="unknown-crs"),
    ],
)
def test_extract_srid(identifier, expected):
    if expected is ValueError:
        with pytest.raises(ValueError):
            filters._extract_srid(identifier)
    else:
        assert filters._extract_srid(identifier) == expected
