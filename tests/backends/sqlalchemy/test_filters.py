from typing import cast
import pytest

from pygeofilter.backends.sqlalchemy import filters


@pytest.mark.parametrize("geom, expected", [
    pytest.param(
        {
            "type": "Point",
            "coordinates": [10, 12]
        },
        "ST_GeomFromEWKT('SRID=4326;POINT (10 12)')",
        id="without-crs"
    ),
    pytest.param(
        {
            "type": "Point",
            "coordinates": [1, 2],
            "crs": {
                "type": "name",
                "properties": {
                    "name": "urn:ogc:def:crs:EPSG::3004"
                }
            }
        },
        "ST_GeomFromEWKT('SRID=3004;POINT (1 2)')",
        id="with-crs"
    ),
])
def test_parse_geometry(geom, expected):
    parsed = filters.parse_geometry(cast(dict, geom))
    result = str(parsed.compile(compile_kwargs={"literal_binds": True}))
    assert result == expected
