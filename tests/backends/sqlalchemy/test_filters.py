from typing import cast

import pytest
from geoalchemy2 import Geometry
from sqlalchemy import Column, func

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
            id="with-crs",
        ),
    ],
)
def test_parse_geometry(geom, expected):
    parsed = filters.parse_geometry(cast(dict, geom))
    result = str(parsed.compile(compile_kwargs={"literal_binds": True}))
    assert result == expected


@pytest.mark.parametrize(
    "op, units, distance, expected",
    [
        pytest.param(
            "DWITHIN",
            "meters",
            10,
            "ST_DWithin(geometry, ST_GeomFromEWKT('SRID=4326;POINT(0 0)'), 10)",
            id="dwithin-meters",
        ),
        pytest.param(
            "DWITHIN",
            "kilometers",
            5,
            "ST_DWithin(geometry, "
            "ST_GeomFromEWKT('SRID=4326;POINT(0 0)'), 5000)",
            id="dwithin-kilometers",
        ),
        pytest.param(
            "DWITHIN",
            "miles",
            5,
            "ST_DWithin(geometry, "
            "ST_GeomFromEWKT('SRID=4326;POINT(0 0)'), 8046.7)",
            id="dwithin-miles",
        ),
        pytest.param(
            "BEYOND",
            "kilometers",
            5,
            "NOT ST_DWithin(geometry, "
            "ST_GeomFromEWKT('SRID=4326;POINT(0 0)'), 5000)",
            id="beyond-kilometers",
        ),
    ],
)
def test_spatial_distance_units(op, units, distance, expected):
    geometry = Column("geometry", Geometry(srid=4326))
    rhs = func.ST_GeomFromEWKT("SRID=4326;POINT(0 0)")
    f = filters.spatial(geometry, rhs, op, distance=distance, units=units)
    result = str(f.compile(compile_kwargs={"literal_binds": True}))
    assert result == expected
