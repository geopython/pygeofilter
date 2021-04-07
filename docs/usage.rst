Usage
=====


The basic functionality parses the input string to an abstract syntax tree
(AST) representation. This AST can then be used to build database filters
or similar functionality.

.. code-block:: pycon

    >>> import pygeofilter
    >>> ast = pygeofilter.parse(filter_expression)

What is returned by the :func:`pygeofilter.parser.parse` is the root
:class:`pygeofilter.ast.Node` of the AST representation.

Inspection
----------

The easiest way to inspect the resulting AST is to use the
:func:`pygeofilter.ast.get_repr` function, which returns a nice string
representation of what was parsed:

.. code-block:: pycon

    >>> ast = pygeofilter.parse('id = 10')
    >>> print(pygeofilter.get_repr(ast))
    ATTRIBUTE id = LITERAL 10.0
    >>>
    >>>
    >>> filter_expr = '(number BETWEEN 5 AND 10 AND string NOT LIKE "%B") OR INTERSECTS(geometry, LINESTRING(0 0, 1 1))'
    >>> print(pygeofilter.get_repr(pygeofilter.parse(filter_expr)))
    (
        (
                ATTRIBUTE number BETWEEN LITERAL 5.0 AND LITERAL 10.0
        ) AND (
                ATTRIBUTE string NOT ILIKE LITERAL '%B'
        )
    ) OR (
        INTERSECTS(ATTRIBUTE geometry, LITERAL GEOMETRY 'LINESTRING(0 0, 1 1)')
    )

Evaluation
----------

In order to create useful filters from the resulting AST, it has to be
evaluated. For the Django integration, this was done using a recursive
descent into the AST, evaluating the subnodes first and constructing a
`Q` object. Consider having a `filters` API (for an example look at the
Django one) which creates the filter. Now the evaluator looks something
like this:

.. code-block:: python

    from pygeofilter.ast import *
    from myapi import filters   # <- this is where the filters are created.
                                # of course, this can also be done in the
                                # evaluator itself
    class FilterEvaluator:
        def __init__(self, field_mapping=None, mapping_choices=None):
            self.field_mapping = field_mapping
            self.mapping_choices = mapping_choices

        def to_filter(self, node):
            to_filter = self.to_filter
            if isinstance(node, NotConditionNode):
                return filters.negate(to_filter(node.sub_node))
            elif isinstance(node, CombinationConditionNode):
                return filters.combine(
                    (to_filter(node.lhs), to_filter(node.rhs)), node.op
                )
            elif isinstance(node, ComparisonPredicateNode):
                return filters.compare(
                    to_filter(node.lhs), to_filter(node.rhs), node.op,
                    self.mapping_choices
                )
            elif isinstance(node, BetweenPredicateNode):
                return filters.between(
                    to_filter(node.lhs), to_filter(node.low),
                    to_filter(node.high), node.not_
                )
            elif isinstance(node, BetweenPredicateNode):
                return filters.between(
                    to_filter(node.lhs), to_filter(node.low),
                    to_filter(node.high), node.not_
                )

            # ... Some nodes are left out for brevity

            elif isinstance(node, AttributeExpression):
                return filters.attribute(node.name, self.field_mapping)

            elif isinstance(node, LiteralExpression):
                return node.value

            elif isinstance(node, ArithmeticExpressionNode):
                return filters.arithmetic(
                    to_filter(node.lhs), to_filter(node.rhs), node.op
                )

            return node

As mentionend, the `to_filter` method is the recursion.


Django integration
------------------

For Django there is a default bridging implementation, where all the filters
are translated to the Django ORM. In order to use this integration, we need
two dictionaries, one mapping the available fields to the Django model fields,
and one to map the fields that use ``choices``. Consider the following example
models:

.. code-block:: python

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


Now we can specify the field mappings and mapping choices to be used when
applying the filters:

.. code-block:: python

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


Finally we are able to connect the CQL AST to the Django database models. We
also provide factory functions to parse the timestamps, durations, geometries and
envelopes, so that they can be used with the ORM layer:

.. code-block:: python

    from pygeofilter.integrations.django import to_filter, parse

    cql_expr = 'strMetaAttribute LIKE "%parent%" AND datetimeAttribute BEFORE 2000-01-01T00:00:01Z'

    # NOTE: we are using the django integration `parse` wrapper here
    ast = parse(cql_expr)
    filters = to_filter(ast, mapping, mapping_choices)

    qs = Record.objects.filter(**filters)

