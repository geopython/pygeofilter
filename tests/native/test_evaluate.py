


from dataclasses import dataclass

from datetime import date, time, datetime, timedelta

import pytest

from pygeofilter.parsers.ecql import parse
from pygeofilter.backends.native.evaluate import NativeEvaluator




@dataclass
class Record:
    str_attr: str
    int_attr: int
    float_attr: float
    date_attr: date
    datetime_attr: datetime
    # TODO: geometry


@pytest.fixture
def data():
    return [
        Record(
            'this is a test',
            5,
            5.5,
            date(2010, 5, 7),
            datetime(2010, 1, 1),
        ),
        Record(
            'this is another test',
            8,
            8.5,
            date(2010, 5, 7),
            datetime(2010, 1, 1),
        )
    ]


@pytest.fixture
def filter_():
    def inner(ast, data):
        print(ast)
        return [
            record
            for record in data
            if NativeEvaluator(record).evaluate(ast)
        ]
    return inner


def test_native_evaluator(data, filter_):
    result = filter_(parse('int_attr = 5'), data)
    print(result)
    assert len(result) == 1
    assert result[0].int_attr == 5
