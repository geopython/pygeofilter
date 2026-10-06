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
from urllib.parse import unquote, urlsplit

from dateparser import parse as _parse_datetime

__all__ = [
    "parse_datetime",
    "RE_ISO_8601",
    "parse_duration",
    "like_pattern_to_re_pattern",
    "like_pattern_to_re",
    "extract_srid",
]

# Match complete identifiers so a version, a different authority's code, or
# a component of a compound CRS cannot accidentally become the SRID.
_CRS_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"(?P<authority>EPSG|OGC|CRS):(?P<code>[^:/\s]+)",
        r"urn:(?:ogc|x-ogc):def:crs:(?P<authority>[^:\s]+):"
        r"(?:[^:\s]*:)?(?P<code>[^:\s]+)",
        r"urn:(?P<authority>EPSG):"
        r"(?:geographic|projected|geocentric|vertical|compound)CRS:"
        r"(?P<code>[0-9]+)",
    )
)
_CRS_URL_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"/def/crs/(?P<authority>[^/\s]+)/[^/\s]*/(?P<code>[^/\s]+)/?",
        r"/gml/srs/(?P<authority>[^/\s]+)\.xml#(?P<code>[^/\s]+)",
        r"/ref/(?P<authority>EPSG)/(?P<code>[0-9]+)/?",
    )
)

_OGC_SRIDS = {
    "CRS27": 4267,
    "CRS83": 4269,
    "CRS84": 4326,
    "CRS84H": 4979,
    "CRS88": 5703,
}
_EPSG_URL_PATTERNS = {
    "epsg.io": re.compile(r"/([0-9]+)/?"),
    "epsg.org": re.compile(r"/crs_([0-9]+)(?:/[^/\s]+)?/?", re.IGNORECASE),
}


def _parse_crs_identifier(identifier: str) -> tuple[str, str]:
    if re.fullmatch(r"[0-9]+", identifier):
        return "EPSG", identifier

    patterns = _CRS_PATTERNS
    url = urlsplit(identifier)
    if url.scheme.lower() in ("http", "https") and url.hostname:
        patterns = _CRS_URL_PATTERNS
        identifier = unquote(url.path)
        if url.fragment:
            identifier += "#" + unquote(url.fragment)
        registry_pattern = _EPSG_URL_PATTERNS.get(
            url.hostname.lower().removeprefix("www.")
        )
        if registry_pattern:
            match = registry_pattern.fullmatch(identifier)
            if match:
                return "EPSG", match[1]

    for pattern in patterns:
        match = pattern.fullmatch(identifier)
        if match:
            return match["authority"].upper(), match["code"].upper()
    return "", ""


def extract_srid(crs_identifier: str) -> int:
    """Extract an EPSG SRID from a commonly used CRS identifier.

    Accepts numeric strings, ``EPSG:<code>``, OGC and legacy x-ogc URNs
    (with or without a version), legacy EPSG URNs, HTTP(S) definition URLs
    (``/def/crs/<authority>/<version>/<code>``), GML URLs
    (``/gml/srs/epsg.xml#<code>``), spatialreference.org EPSG URLs, and
    epsg.org and epsg.io URLs. Definition and GML paths also work on custom
    resolvers.
    URL components may be percent-encoded; surrounding whitespace and
    case differences are tolerated.

    OGC CRS27, CRS83, CRS84, CRS84h and CRS88 map to their EPSG equivalents.
    WMS shorthand such as ``CRS:84`` is also supported.
    This extracts a code only; it does not reorder coordinates or check
    that an EPSG code exists in a registry. No network lookup is performed.

    Raises ``ValueError`` for malformed or unsupported identifiers,
    including other authorities and compound identifiers that cannot be
    represented by a single EPSG code.
    """
    authority, code = _parse_crs_identifier(crs_identifier.strip())
    if authority == "EPSG" and re.fullmatch(r"[0-9]+", code):
        srid = int(code)
        if srid > 0:
            return srid
    elif authority in ("OGC", "CRS"):
        if authority == "CRS":
            code = "CRS" + code
        if code in _OGC_SRIDS:
            return _OGC_SRIDS[code]

    raise ValueError(f"Could not extract an EPSG SRID from {crs_identifier!r}.")


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
