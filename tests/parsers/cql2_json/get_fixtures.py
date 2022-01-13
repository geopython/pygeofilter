"""Get fixtures from the spec."""
import json
import requests
import re

url = (
    "https://raw.githubusercontent.com/radiantearth/"
    "stac-api-spec/dev/fragments/filter/README.md"
)

fixtures = {}
examples_text = requests.get(url).text
examples_raw = re.findall(
    r"### (Example \d+).*?```http" r"(.*?)" r"```.*?```json" r"(.*?)" r"```",
    examples_text,
    re.S,
)
for example in examples_raw:
    fixtures[example[0]] = {
        "text": example[1].replace("\n", ""),
        "json": json.dumps(json.loads(example[2])),
    }

with open("fixtures.json", "w") as f:
    json.dump(fixtures, f, indent=4)
