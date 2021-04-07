## SQLAlchemy Integration

The SQLAlchemy Integration translates the AST into a set of filters suitable for input into a filter of a SQLAlchemy Query.

Given the following example model:

```python
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from geoalchemy2 import Geometry
Base = declarative_base()


class Record(Base):
    __tablename__ = "record"
    identifier = Column(String, primary_key=True)
    geometry = Column(
        Geometry(
            geometry_type="MULTIPOLYGON",
            srid=4326,
            spatial_index=False,
            management=True,
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
```

Now we can specify the field mappings to be used when applying the filters:

```python
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
```

Finally we are able to connect the CQL AST to the SQLAlchemy database models. We also provide factory
functions to parse the timestamps, durations, geometries and envelopes, so that they can be used
with the ORM layer:

```python
from pygeofilter.integrations.sqlalchemy import to_filter, parse

cql_expr = 'strMetaAttribute LIKE "%parent%" AND datetimeAttribute BEFORE 2000-01-01T00:00:01Z'

# NOTE: we are using the sqlalchemy integration `parse` wrapper here
ast = parse(cql_expr)
print(ast)
filters = to_filter(ast, FIELD_MAPPING)

q = session.query(Record).join(RecordMeta).filter(filters)
```

## Tests
Tests for the sqlalchemy integration can be run as following:

```shell
python -m unittest discover tests/sqlalchemy_test/ tests.py
```
