import json
import pathlib

from pygeofilter.backends.cql2_json import to_cql2
from pygeofilter.frontends.cql2_json import parse as json_parse
from pygeofilter.frontends.cql2_text import parse as text_parse

dir = pathlib.Path(__file__).parent.resolve()
fixtures = pathlib.Path(dir, "fixtures.json")


def test_fixtures():
    """Test against fixtures from spec documentation.

    Parses both cql2_text and cql2_json from spec
    documentation and makes sure AST is the same
    and that json when each are converted back to
    cql2_json is the same.
    """
    with open(fixtures) as f:
        examples = json.load(f)

    for _, v in examples.items():
        t = v["text"].replace("filter=", "")
        j = v["json"]
        parsed_text = text_parse(t)
        parsed_json = json_parse(j)
        assert parsed_text == parsed_json
        assert to_cql2(parsed_text) == to_cql2(parsed_json)
