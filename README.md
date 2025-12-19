# pygeofilter
pygeofilter is a pure Python parser implementation of OGC filtering standards

[![PyPI version](https://badge.fury.io/py/pygeofilter.svg)](https://badge.fury.io/py/pygeofilter)
[![Build Status](https://github.com/geopython/pygeofilter/workflows/build%20%E2%9A%99%EF%B8%8F/badge.svg)](https://github.com/geopython/pygeofilter/actions)
[![Documentation Status](https://readthedocs.org/projects/pygeofilter/badge/?version=latest)](https://pygeofilter.readthedocs.io/en/latest/?badge=latest)


## Features

* Parsing of several filter encoding standards
    * [CQL as defined in CSW 2.0](https://portal.ogc.org/files/?artifact_id=20555)
    * [CQL JSON as defined in OGC API - Features - Part 3: Filtering and the Common Query Language (CQL)](https://portal.ogc.org/files/96288#cql-json-schema)
    * [JSON Filter Expressions (JFE)](https://github.com/tschaub/ogcapi-features/tree/json-array-expression/extensions/cql/jfe)
    * Soon:
        * [CQL Text as defined in OGC API - Features - Part 3: Filtering and the Common Query Language (CQL)](https://portal.ogc.org/files/96288#cql-bnf)
        * [FES](http://docs.opengeospatial.org/is/09-026r2/09-026r2.html)
* Several backends included
    * [Django](https://www.djangoproject.com/)
    * [SQLAlchemy](https://www.sqlalchemy.org/)
    * [(Geo)Pandas](https://pandas.pydata.org/)
    * Native Python objects


## Installation

The package can be installed via PIP:

```bash
pip3 install pygeofilter
```

Some features require additional dependencies. This currently only affects the backends. To install these, the features have to be listed:

```bash
# for the Django backend
pip3 install pygeofilter[backend-django]

# for the sqlalchemy backend
pip3 install pygeofilter[backend-sqlalchemy]

# for the native backend
pip3 install pygeofilter[backend-native]
```

## Usage

pygeofilter can be used on various levels. It provides parsers for various filtering languages, such as ECQL or CQL-JSON. Each parser lives in its own sub-package:

```python
>>> from pygeofilter.parsers.ecql import parse as parse_ecql
>>> filters = parse_ecql(filter_expression)
>>> from pygeofilter.parsers.cql_json import parse as parse_json
>>> filters = parse_json(filter_expression)
```

Each parser creates an abstract syntax tree (AST) representation of that filter expression and thus unifies all possible languages to a single common denominator. All possible nodes are defined as classes in the `pygeofilter.ast` module.

### Inspection

The easiest way to inspect the resulting AST is to use the `get_repr` function, which returns a
nice string representation of what was parsed:

```python
>>> filters = pygeofilter.parsers.ecql.parse('id = 10')
>>> print(pygeofilter.get_repr(ast))
ATTRIBUTE id = LITERAL 10.0
>>>
>>>
>>> filter_expr = '(number BETWEEN 5 AND 10 AND string NOT LIKE \'%B\') OR INTERSECTS(geometry, LINESTRING(0 0, 1 1))'
>>> print(pygeofilter.ast.get_repr(pygeofilter.parse(filter_expr)))
(
    (
            ATTRIBUTE number BETWEEN 5 AND 10
    ) AND (
            ATTRIBUTE string NOT LIKE '%B'
    )
) OR (
    INTERSECTS(ATTRIBUTE geometry, Geometry(geometry={'type': 'LineString', 'coordinates': ((0.0, 0.0), (1.0, 1.0))}))
)
```

### Evaluation

A parsed AST can then be evaluated and transformed into filtering mechanisms in the required context. Usually this is a language such as SQL or an object-relational mapper (ORM) interfacing a data store of some kind.

There are a number of pre-defined backends available, where parsed expressions can be applied. For the moment this includes:

* Django
* sqlalchemy
* (Geo)Pandas
* Elasticsearch
* OpenSearch
* Pure Python object filtering

The usage of those are described in their own documentation.

pygeofilter provides mechanisms to help building such an evaluator (the included backends use them as well). The `Evaluator` class allows to conveniently walk through an AST depth-first and build the filters for the API in question. Only handled node classes are evaluated, unsupported ones will raise an exception.

Consider this example:

```python

from pygeofilter import ast
from pygeofilter.backends.evaluator import Evaluator, handle
from myapi import filters   # <- this is where the filters are created.
                            # of course, this can also be done in the
                            # evaluator itself

# Evaluators must derive from the base class `Evaluator` to work
class MyAPIEvaluator(Evaluator):
    # you can use any constructor as you need
    def __init__(self, field_mapping=None, mapping_choices=None):
        self.field_mapping = field_mapping
        self.mapping_choices = mapping_choices

    # specify the handled classes in the `handle` decorator to mark
    # this function as the handler for that node class(es)
    @handle(ast.Not)
    def not_(self, node, sub):
        return filters.negate(sub)

    # multiple classes can be declared for the same handler function
    @handle(ast.And, ast.Or)
    def combination(self, node, lhs, rhs):
        return filters.combine((lhs, rhs), node.op.value)

    # handle all sub-classes, like ast.Equal, ast.NotEqual,
    # ast.LessThan, ast.GreaterThan, ...
    @handle(ast.Comparison, subclasses=True)
    def comparison(self, node, lhs, rhs):
        return filters.compare(
            lhs,
            rhs,
            node.op.value,
            self.mapping_choices
        )

    @handle(ast.Between)
    def between(self, node, lhs, low, high):
        return filters.between(
            lhs,
            low,
            high,
            node.not_
        )

    @handle(ast.Like)
    def like(self, node, lhs):
        return filters.like(
            lhs,
            node.pattern,
            node.nocase,
            node.not_,
            self.mapping_choices
        )

    @handle(ast.In)
    def in_(self, node, lhs, *options):
        return filters.contains(
            lhs,
            options,
            node.not_,
            self.mapping_choices
        )

    def adopt(self, node, *sub_args):
        # a "catch-all" function for node classes that are not
        # handled elsewhere. Use with caution and raise exceptions
        # yourself when a node class is not supported.
        ...

    # ...further ast handlings removed for brevity
```

### Command line utility

pygeofilter also includes a command-line utility (`pygeofilter`).  Current functionality includes testing filter parsing into the native AST.  Examples:

```bash
# display installed version
pygeofilter --version

# parse subcommand functionality
pygeofilter parse 
Usage: pygeofilter parse [OPTIONS] {cql_json|cql2_json|cql2_text|ecql|fes|jfe}
                         QUERY

  Parse a query into an abstract syntax tree

Options:
  -v, --verbosity [ERROR|WARNING|INFO|DEBUG]
                                  Verbosity
  --help                          Show this message and exit.

# parse a CQL2 text string into AST
pygeofilter parse cql2_text "title = "birds'"
Parsing cql2_text query into AST
Equal(lhs=ATTRIBUTE title, rhs='birds')

# parse a FES text string into AST 
pygeofilter parse fes "<Filter xmlns=\"http://www.opengis.net/ogc\"><PropertyIsEqualTo><PropertyName>title</PropertyName><Literal>birds</Literal></PropertyIsEqualTo></Filter>"
Parsing fes query into AST
Equal(lhs=ATTRIBUTE title, rhs='birds')
```

## Testing

For testing, several requirements must be satisfied. These can be installed, via pip:

```bash
pip3 install -r requirements-dev.txt
pip3 install -r requirements-test.txt
```

GDAL must also be available in the local environment.

The functionality can be tested using `pytest`.

```bash
python -m pytest
```

### Docker

To execute tests with Docker Compose:

```
./execute-tests.sh
```

## Backends

The following backends are shipped with `pygeofilter`. Some require additional dependencies, refer to the [installation](#installation) section for further details.

### Django

For Django there is a default backend implementation, where all the filters are translated to the
Django ORM. In order to use this integration, we need two dictionaries, one mapping the available
fields to the Django model fields, and one to map the fields that use `choices`. Consider the
following example models:

```python
from django.contrib.gis.db import models


optional = dict(null=True, blank=True)

class Record(models.Model):
    identifier = models.CharField(max_length=256, unique=True, null=False)
    geometry = models.GeometryField()

    float_attribute = models.FloatField(**optional)
    int_attribute = models.IntegerField(**optional)
    str_attribute = models.CharField(max_length=256, **optional)
    datetime_attribute = models.DateTimeField(**optional)
    choice_attribute = models.PositiveSmallIntegerField(choices=[
                                                                 (1, 'ASCENDING'),
                                                                 (2, 'DESCENDING'),],
                                                        **optional)


class RecordMeta(models.Model):
    record = models.ForeignKey(Record, on_delete=models.CASCADE, related_name='record_metas')

    float_meta_attribute = models.FloatField(**optional)
    int_meta_attribute = models.IntegerField(**optional)
    str_meta_attribute = models.CharField(max_length=256, **optional)
    datetime_meta_attribute = models.DateTimeField(**optional)
    choice_meta_attribute = models.PositiveSmallIntegerField(choices=[
                                                                      (1, 'X'),
                                                                      (2, 'Y'),
                                                                      (3, 'Z')],
                                                             **optional)
```

Now we can specify the field mappings and mapping choices to be used when applying the filters:

```python
FIELD_MAPPING = {
    'identifier': 'identifier',
    'geometry': 'geometry',
    'floatAttribute': 'float_attribute',
    'intAttribute': 'int_attribute',
    'strAttribute': 'str_attribute',
    'datetimeAttribute': 'datetime_attribute',
    'choiceAttribute': 'choice_attribute',

    # meta fields
    'floatMetaAttribute': 'record_metas__float_meta_attribute',
    'intMetaAttribute': 'record_metas__int_meta_attribute',
    'strMetaAttribute': 'record_metas__str_meta_attribute',
    'datetimeMetaAttribute': 'record_metas__datetime_meta_attribute',
    'choiceMetaAttribute': 'record_metas__choice_meta_attribute',
}

MAPPING_CHOICES = {
    'choiceAttribute': dict(Record._meta.get_field('choice_attribute').choices),
    'choiceMetaAttribute': dict(RecordMeta._meta.get_field('choice_meta_attribute').choices),
}
```

Finally we are able to connect the CQL AST to the Django database models. We also provide factory
functions to parse the timestamps, durations, geometries and envelopes, so that they can be used
with the ORM layer:

```python
from pygeofilter.backends.django import to_filter
from pygeofilter.parsers.ecql import parse

cql_expr = 'strMetaAttribute LIKE \'%parent%\' AND datetimeAttribute BEFORE 2000-01-01T00:00:01Z'

ast = parse(cql_expr)
filters = to_filter(ast, mapping, mapping_choices)

qs = Record.objects.filter(**filters)
```

### SQL

`pygeofilter` provides a rudimentary way to create an SQL `WHERE` clause from an AST. The following example shows this usage in conjunction with the OGR `ExecuteSQL` function:

```python
from osgeo import ogr
from pygeofilter.backends.sql import to_sql_where
from pygeofilter.parsers.ecql import parse


FIELD_MAPPING = {
    'str_attr': 'str_attr',
    'maybe_str_attr': 'maybe_str_attr',
    'int_attr': 'int_attr',
    'float_attr': 'float_attr',
    'date_attr': 'date_attr',
    'datetime_attr': 'datetime_attr',
    'point_attr': 'GEOMETRY',
}

FUNCTION_MAP = {
    'sin': 'sin'
}

# parse the expression
ast = parse('int_attr > 6')

# open an OGR DataSource
data = ogr.Open(...)

# create the WHERE clause, field and function mappings must be provided
where = to_sql_where(ast, FIELD_MAPPING, FUNCTION_MAP)

# filter the DataSource to get a result Layer
layer = data.ExecuteSQL(f"""
    SELECT id, str_attr, maybe_str_attr, int_attr, float_attr, date_attr, datetime_attr, GEOMETRY
    FROM layer
    WHERE {where}
""", None, "SQLite")
```

Note that it is vital to specify the `SQLite` dialect as this is the one used internally.

:warning: Input values are *not* sanitized/separated from the generated SQL text. This is due to the compatibility with the OGR API not allowing to separate the SQL from the arguments.


### Optimization

This is a special kind of backend, as the result of the AST evaluation is actually a new AST. The purpose of this backend is to eliminate static branches of the AST, potentially reducing the cost of an actual evaluation for filtering values.

What parts of an AST can be optimized:

- Arithmetic operations of purely static operands
- All predicates (spatial, temporal, array, `like`, `between`, `in`) if all of the operands are already static
- Functions, when passed in a special lookup table and all arguments are static
- `And` and `Or` combinators can be eliminated if either branch can be predicted

What cannot be optimized are branches that contain references to attributes or functions not passed in the dictionary.

The following example shows how a static computation can be optimized to a static value, replacing the whole branch of the AST:

```python
>>> import math
>>> from pygeofilter import ast
>>> from pygeofilter.parsers.ecql import parse
>>> from pygeofilter.backends.optimize import optimize
>>>
>>> root = parse('attr < sin(3.7) - 5')
>>> optimized_root = optimize(root, {'sin': math.sin})
>>> print(ast.get_repr(root))
ATTRIBUTE attr < (
    (
            sin (3.7)
    ) - 5
)
>>> print(ast.get_repr(optimized_root))
ATTRIBUTE attr < -5.529836140908493
```
