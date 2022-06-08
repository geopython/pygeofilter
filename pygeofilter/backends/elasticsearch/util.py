""" General utilities for the Elasticsearch backend.
"""

import re


def like_to_wildcard(
    value: str, wildcard: str, single_char: str, escape_char: str = "\\"
) -> str:
    """Adapts a "LIKE" pattern to create an elasticsearch "wildcard"
    pattern.
    """

    x_wildcard = re.escape(wildcard)
    x_single_char = re.escape(single_char)

    if escape_char == "\\":
        x_escape_char = "\\\\\\\\"
    else:
        x_escape_char = re.escape(escape_char)

    if wildcard != "*":
        value = re.sub(
            f"(?<!{x_escape_char}){x_wildcard}",
            "*",
            value,
        )

    if single_char != "?":
        value = re.sub(
            f"(?<!{x_escape_char}){x_single_char}",
            "?",
            value,
        )

    return value
