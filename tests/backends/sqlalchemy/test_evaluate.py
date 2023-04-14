import ctypes.util

import dateparser
import pytest
from geoalchemy2 import Geometry
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    create_engine,
)
from sqlalchemy.event import listen
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.sql import func, select

from pygeofilter.backends.sqlalchemy.evaluate import to_filter
from pygeofilter.parsers.ecql import parse

Base = declarative_base()


class Record(Base):
    __tablename__ = "record"
    identifier = Column(String, primary_key=True)
    geometry = Column(
        Geometry(
            geometry_type="MULTIPOLYGON",
            srid=4326,
            spatial_index=False,
        )
    )
    float_attribute = Column(Float)
    int_attribute = Column(Integer)
    str_attribute = Column(String)
    datetime_attribute = Column(DateTime)
    choice_attribute = Column(Integer)


class RecordMeta(Base):
    __tablename__ = "record_meta"
    identifier = Column(Integer, primary_key=True)
    record = Column(String, ForeignKey("record.identifier"))
    float_meta_attribute = Column(Float)
    int_meta_attribute = Column(Integer)
    str_meta_attribute = Column(String)
    datetime_meta_attribute = Column(DateTime)
    choice_meta_attribute = Column(Integer)


FIELD_MAPPING = {
    "identifier": Record.identifier,
    "geometry": Record.geometry,
    "floatAttribute": Record.float_attribute,
    "intAttribute": Record.int_attribute,
    "strAttribute": Record.str_attribute,
    "datetimeAttribute": Record.datetime_attribute,
    "choiceAttribute": Record.choice_attribute,
    # meta fields
    "floatMetaAttribute": RecordMeta.float_meta_attribute,
    "intMetaAttribute": RecordMeta.int_meta_attribute,
    "strMetaAttribute": RecordMeta.str_meta_attribute,
    "datetimeMetaAttribute": RecordMeta.datetime_meta_attribute,
    "choiceMetaAttribute": RecordMeta.choice_meta_attribute,
}


def load_spatialite(dbapi_conn, connection_record):
    dbapi_conn.enable_load_extension(True)
    dbapi_conn.load_extension(
        ctypes.util.find_library("mod_spatialite")
        or "/usr/lib/x86_64-linux-gnu/mod_spatialite.so"
    )


@pytest.fixture(scope="session")
def connection():
    engine = create_engine("sqlite://", echo=True)
    listen(engine, "connect", load_spatialite)
    return engine.connect()


def seed_database(db_session):
    record = Record(
        identifier="A",
        geometry="SRID=4326;MULTIPOLYGON(((0 0, 0 5, 5 5,5 0,0 0)))",
        float_attribute=0.0,
        int_attribute=10,
        str_attribute="AAA",
        datetime_attribute=dateparser.parse("2000-01-01T00:00:00Z"),
        choice_attribute=1,
    )
    db_session.add(record)

    record_meta = RecordMeta(
        float_meta_attribute=10.0,
        int_meta_attribute=20,
        str_meta_attribute="AparentA",
        datetime_meta_attribute=dateparser.parse("2000-01-01T00:00:05Z"),
        choice_meta_attribute=1,
        record=record.identifier,
    )
    db_session.add(record_meta)

    record = Record(
        identifier="B",
        geometry="SRID=4326;MULTIPOLYGON(((5 5, 5 10, 10 10,10 5,5 5)))",
        float_attribute=30.0,
        int_attribute=None,
        str_attribute="BBB",
        datetime_attribute=dateparser.parse("2000-01-01T00:00:10Z"),
        choice_attribute=1,
    )
    db_session.add(record)

    record_meta = RecordMeta(
        float_meta_attribute=20.0,
        int_meta_attribute=30,
        str_meta_attribute="BparentB",
        datetime_meta_attribute=dateparser.parse("2000-01-01T00:00:05Z"),
        choice_meta_attribute=1,
        record=record.identifier,
    )
    db_session.add(record_meta)
    db_session.commit()


@pytest.fixture(scope="session")
def setup_database(connection):
    connection.execute(select(func.InitSpatialMetaData()))
    Base.metadata.create_all(connection)
    connection.commit()

    seed_database(
        scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=connection))
    )

    yield

    Base.metadata.drop_all(connection)


@pytest.fixture
def db_session(setup_database, connection):
    transaction = connection.begin()
    yield scoped_session(
        sessionmaker(autocommit=False, autoflush=False, bind=connection)
    )
    transaction.rollback()


def evaluate(session, cql_expr, expected_ids):
    ast = parse(cql_expr)
    filters = to_filter(ast, FIELD_MAPPING)

    q = session.query(Record).join(RecordMeta).filter(filters)
    results = [row.identifier for row in q]

    assert expected_ids == type(expected_ids)(results)


# common comparisons


def test_id_eq(db_session):
    evaluate(db_session, "identifier = 'A'", ("A",))


def test_id_ne(db_session):
    evaluate(db_session, "identifier <> 'B'", ("A",))


def test_float_lt(db_session):
    evaluate(db_session, "floatAttribute < 30", ("A",))


def test_float_le(db_session):
    evaluate(db_session, "floatAttribute <= 20", ("A",))


def test_float_gt(db_session):
    evaluate(db_session, "floatAttribute > 20", ("B",))


def test_float_ge(db_session):
    evaluate(db_session, "floatAttribute >= 30", ("B",))


def test_float_between(db_session):
    evaluate(db_session, "floatAttribute BETWEEN -1 AND 1", ("A",))


# test different field types


def test_common_value_eq(db_session):
    evaluate(db_session, "strAttribute = 'AAA'", ("A",))


def test_common_value_in(db_session):
    evaluate(db_session, "strAttribute IN ('AAA', 'XXX')", ("A",))


def test_common_value_like(db_session):
    evaluate(db_session, "strAttribute LIKE 'AA%'", ("A",))


def test_common_value_like_middle(db_session):
    evaluate(db_session, "strAttribute LIKE 'A%A'", ("A",))


def test_like_beginswith(db_session):
    evaluate(db_session, "strMetaAttribute LIKE 'A%'", ("A",))


def test_ilike_beginswith(db_session):
    evaluate(db_session, "strMetaAttribute ILIKE 'a%'", ("A",))


def test_like_endswith(db_session):
    evaluate(db_session, "strMetaAttribute LIKE '%A'", ("A",))


def test_ilike_endswith(db_session):
    evaluate(db_session, "strMetaAttribute ILIKE '%a'", ("A",))


def test_like_middle(db_session):
    evaluate(db_session, "strMetaAttribute LIKE '%parent%'", ("A", "B"))


def test_like_startswith_middle(db_session):
    evaluate(db_session, "strMetaAttribute LIKE 'A%rent%'", ("A",))


def test_like_middle_endswith(db_session):
    evaluate(db_session, "strMetaAttribute LIKE '%ren%A'", ("A",))


def test_like_startswith_middle_endswith(db_session):
    evaluate(db_session, "strMetaAttribute LIKE 'A%ren%A'", ("A",))


def test_ilike_middle(db_session):
    evaluate(db_session, "strMetaAttribute ILIKE '%PaReNT%'", ("A", "B"))


def test_not_like_beginswith(db_session):
    evaluate(db_session, "strMetaAttribute NOT LIKE 'B%'", ("A",))


def test_not_ilike_beginswith(db_session):
    evaluate(db_session, "strMetaAttribute NOT ILIKE 'b%'", ("A",))


def test_not_like_endswith(db_session):
    evaluate(db_session, "strMetaAttribute NOT LIKE '%B'", ("A",))


def test_not_ilike_endswith(db_session):
    evaluate(db_session, "strMetaAttribute NOT ILIKE '%b'", ("A",))


# (NOT) IN


def test_string_in(db_session):
    evaluate(db_session, "identifier IN ('A', 'B')", ("A", "B"))


def test_string_not_in(db_session):
    evaluate(db_session, "identifier NOT IN ('B', 'C')", ("A",))


# (NOT) NULL


def test_string_null(db_session):
    evaluate(db_session, "intAttribute IS NULL", ("B",))


def test_string_not_null(db_session):
    evaluate(db_session, "intAttribute IS NOT NULL", ("A",))


# temporal predicates


def test_before(db_session):
    evaluate(db_session, "datetimeAttribute BEFORE 2000-01-01T00:00:01Z", ("A",))


def test_before_or_during_dt_dt(db_session):
    evaluate(
        db_session,
        "datetimeAttribute BEFORE OR DURING "
        "2000-01-01T00:00:00Z / 2000-01-01T00:00:01Z",
        ("A",),
    )


def test_before_or_during_dt_td(db_session):
    evaluate(
        db_session,
        "datetimeAttribute BEFORE OR DURING " "2000-01-01T00:00:00Z / PT4S",
        ("A",),
    )


def test_before_or_during_td_dt(db_session):
    evaluate(
        db_session,
        "datetimeAttribute BEFORE OR DURING " "PT4S / 2000-01-01T00:00:03Z",
        ("A",),
    )


def test_during_td_dt(db_session):
    evaluate(
        db_session,
        "datetimeAttribute BEFORE OR DURING " "PT4S / 2000-01-01T00:00:03Z",
        ("A",),
    )


# spatial predicates


def test_intersects_point(db_session):
    evaluate(db_session, "INTERSECTS(geometry, POINT(1 1.0))", ("A",))


def test_intersects_mulitipoint_1(db_session):
    evaluate(db_session, "INTERSECTS(geometry, MULTIPOINT(0 0, 1 1))", ("A",))


def test_intersects_mulitipoint_2(db_session):
    evaluate(db_session, "INTERSECTS(geometry, MULTIPOINT((0 0), (1 1)))", ("A",))


def test_intersects_linestring(db_session):
    evaluate(db_session, "INTERSECTS(geometry, LINESTRING(0 0, 1 1))", ("A",))


def test_intersects_multilinestring(db_session):
    evaluate(
        db_session,
        "INTERSECTS(geometry, MULTILINESTRING((0 0, 1 1), (2 1, 1 2)))",
        ("A",),
    )


def test_intersects_polygon(db_session):
    evaluate(
        db_session,
        "INTERSECTS(geometry, "
        "POLYGON((0 0, 3 0, 3 3, 0 3, 0 0), (1 1, 2 1, 2 2, 1 2, 1 1)))",
        ("A",),
    )


def test_intersects_multipolygon(db_session):
    evaluate(
        db_session,
        "INTERSECTS(geometry, "
        "MULTIPOLYGON(((0 0, 3 0, 3 3, 0 3, 0 0), "
        "(1 1, 2 1, 2 2, 1 2, 1 1))))",
        ("A",),
    )


def test_intersects_envelope(db_session):
    evaluate(db_session, "INTERSECTS(geometry, ENVELOPE(0 1.0 0 1.0))", ("A",))


# Commented out as not supported in spatialite for testing
# def test_dwithin(db_session):
#    evaluate(db_session, "DWITHIN(geometry, POINT(0 0), 10, meters)", ("A",))

# def test_beyond(db_session):
#     evaluate(db_session, "BEYOND(geometry, POINT(0 0), 10, meters)", ("B",))


def test_bbox(db_session):
    evaluate(db_session, "BBOX(geometry, 0, 0, 1, 1, '4326')", ("A",))


# arithmethic expressions


def test_arith_simple_plus(db_session):
    evaluate(db_session, "intMetaAttribute = 10 + 10", ("A",))


def test_arith_field_plus_1(db_session):
    evaluate(db_session, "intMetaAttribute = floatMetaAttribute + 10", ("A", "B"))


def test_arith_field_plus_2(db_session):
    evaluate(db_session, "intMetaAttribute = 10 + floatMetaAttribute", ("A", "B"))


def test_arith_field_plus_field(db_session):
    evaluate(
        db_session, "intMetaAttribute = " "floatMetaAttribute + intAttribute", ("A",)
    )


def test_arith_field_plus_mul_1(db_session):
    evaluate(db_session, "intMetaAttribute = intAttribute * 1.5 + 5", ("A",))


def test_arith_field_plus_mul_2(db_session):
    evaluate(db_session, "intMetaAttribute = 5 + intAttribute * 1.5", ("A",))
