# ------------------------------------------------------------------------------
#
# Project: pygeofilter <https://github.com/geopython/pygeofilter>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2019 EOX IT Services GmbH
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

import re
from collections.abc import Mapping
from datetime import date, datetime, timedelta

from dateparser import parse as _parse_datetime

__all__ = [
    "parse_datetime",
    "RE_ISO_8601",
    "parse_duration",
    "like_pattern_to_re_pattern",
    "like_pattern_to_re",
]

RE_ISO_8601 = re.compile(
    r"^(?P<sign>[+-])?P"
    r"(?:(?P<years>\d+(\.\d+)?)Y)?"
    r"(?:(?P<months>\d+(\.\d+)?)M)?"
    r"(?:(?P<days>\d+(\.\d+)?)D)?"
    r"T?(?:(?P<hours>\d+(\.\d+)?)H)?"
    r"(?:(?P<minutes>\d+(\.\d+)?)M)?"
    r"(?:(?P<seconds>\d+(\.\d+)?)S)?$"
)


def parse_duration(value: str) -> timedelta:
    """Parses an ISO 8601 duration string into a python timedelta object.
    Raises a ``ValueError`` if a conversion was not possible.

    :param value: the ISO8601 duration string to parse
    :type value: str
    :return: the parsed duration
    :rtype: datetime.timedelta
    """

    match = RE_ISO_8601.match(value)
    if not match:
        raise ValueError("Could not parse ISO 8601 duration from '%s'." % value)
    parts = match.groupdict()

    sign = -1 if "-" == parts["sign"] else 1
    days = float(parts["days"] or 0)
    days += float(parts["months"] or 0) * 30  # ?!
    days += float(parts["years"] or 0) * 365  # ?!
    fsec = float(parts["seconds"] or 0)
    fsec += float(parts["minutes"] or 0) * 60
    fsec += float(parts["hours"] or 0) * 3600

    return sign * timedelta(days, fsec)


def parse_date(value: str) -> date:
    """Backport for `fromisoformat` for dates in Python 3.6"""
    return date(*(int(part) for part in value.split("-")))


def parse_datetime(value: str) -> datetime:
    parsed = _parse_datetime(value)
    if parsed is None:
        raise ValueError(value)
    return parsed


def like_pattern_to_re_pattern(like, wildcard, single_char, escape_char):
    x_wildcard = re.escape(wildcard)
    x_single_char = re.escape(single_char)

    dx_wildcard = re.escape(x_wildcard)
    dx_single_char = re.escape(x_single_char)

    # special handling if escape char clashes with re escape char
    if escape_char == "\\":
        x_escape_char = "\\\\\\\\"
    else:
        x_escape_char = re.escape(escape_char)
    dx_escape_char = re.escape(x_escape_char)

    pattern = re.escape(like)

    # handle not escaped wildcards/single chars
    pattern = re.sub(
        f"(?<!{x_escape_char}){dx_wildcard}",
        ".*",
        pattern,
    )
    pattern = re.sub(
        f"(?<!{x_escape_char}){dx_single_char}",
        ".",
        pattern,
    )

    # handle escaped wildcard, single chars and escape chars
    pattern = re.sub(
        f"{dx_escape_char}{dx_wildcard}",
        x_wildcard,
        pattern,
    )
    pattern = re.sub(
        f"{dx_escape_char}{dx_single_char}",
        x_single_char,
        pattern,
    )
    pattern = re.sub(
        f"{x_escape_char}{x_escape_char}",
        x_escape_char,
        pattern,
    )

    return f"^{pattern}$"


def like_pattern_to_re(like, nocase, wildcard, single_char, escape_char):
    flags = re.I if nocase else 0
    return re.compile(
        like_pattern_to_re_pattern(like, wildcard, single_char, escape_char),
        flags=flags,
    )


class IdempotentDict(Mapping):
    "A dict class that always returns the key"

    def __getitem__(self, key):
        return key

    def __iter__(self):
        return iter(())

    def __len__(self) -> int:
        return 0
