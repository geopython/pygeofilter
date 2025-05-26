# ------------------------------------------------------------------------------
#
# Project: pygeofilter <https://github.com/geopython/pygeofilter>
# Authors: Magnar Martinsen <magnarem@met.no>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2025 Norwegian Meteorological Institute
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# ------------------------------------------------------------------------------

""" General utilities for the Apache Solr backend.
"""

import re


def like_to_wildcard(
    value: str, wildcard: str, single_char: str, escape_char: str = "\\"
) -> str:
    """Adapts a "LIKE" pattern to create a Solr "wildcard"
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
