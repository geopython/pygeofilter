from datetime import date

import pytest
from sqlalchemy import and_, column

from pygeofilter import ast
from pygeofilter.backends.cql2_json import to_cql2
from pygeofilter.backends.sqlalchemy import to_filter
from pygeofilter.parsers.cql2_json import parse


def test_interval_debug_representation():
    node = ast.Interval(ast.Attribute("start"), ast.Attribute("end"))
    assert ast.get_repr(node) == "INTERVAL(ATTRIBUTE start, ATTRIBUTE end)"
    assert "INTERVAL" in ast.get_repr(
        ast.TimeDuring(ast.Attribute("time"), node)
    )


@pytest.mark.parametrize(
    "bounds",
    [
        [{"property": "start"}, {"property": "end"}],
        [{"property": "start"}, ".."],
        ["..", {"property": "end"}],
        ["2000-01-01", "2000-01-02"],
    ],
)
def test_interval_json_roundtrip(bounds):
    node = parse(
        {"op": "t_during", "args": [{"property": "time"}, {"interval": bounds}]}
    )
    assert parse(to_cql2(node)) == node


def test_interval_sqlalchemy_translation():
    node = ast.TimeDuring(
        ast.Attribute("time"),
        ast.Interval(ast.Attribute("start"), ast.Attribute("end")),
    )
    mapping = {name: column(name) for name in ["time", "start", "end"]}
    result = to_filter(node, mapping)
    assert result.compare(
        and_(
            mapping["time"] >= mapping["start"],
            mapping["time"] <= mapping["end"],
        )
    )


def test_interval_sqlalchemy_literal_bounds():
    node = ast.TimeDuring(
        ast.Attribute("time"), ast.Interval(date(2000, 1, 1), None)
    )
    result = to_filter(node, {"time": column("time")})
    assert result.compile().params == {"time_1": date(2000, 1, 1)}
