# ------------------------------------------------------------------------------
#
# Project: pygeofilter <https://github.com/geopython/pygeofilter>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2021 EOX IT Services GmbH
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

import pytest

from pygeofilter.util import extract_srid, like_pattern_to_re

SEARCH_STRING = "This is a test"


def test_basic_single():
    pattern = r"This is . test"
    regex = like_pattern_to_re(
        pattern,
        nocase=False,
        wildcard="%",
        single_char=".",
        escape_char="\\",
    )
    assert regex.match(SEARCH_STRING) is not None


def test_basic():
    pattern = r"% a test"
    regex = like_pattern_to_re(
        pattern,
        nocase=False,
        wildcard="%",
        single_char=".",
        escape_char="\\",
    )
    assert regex.match(SEARCH_STRING) is not None


def test_basic_nocase():
    pattern = r"% A TEST"
    regex = like_pattern_to_re(
        pattern,
        nocase=True,
        wildcard="%",
        single_char=".",
        escape_char="\\",
    )
    assert regex.match(SEARCH_STRING) is not None


def test_basic_regex_escape_re_func():
    pattern = r".* a test"
    regex = like_pattern_to_re(
        pattern,
        nocase=True,
        wildcard="%",
        single_char=".",
        escape_char="\\",
    )
    assert regex.match(SEARCH_STRING) is None


def test_basic_regex_escape_char():
    search_string = r"This is a % sign"
    pattern = r"This is a /% sign"
    regex = like_pattern_to_re(
        pattern,
        nocase=True,
        wildcard="%",
        single_char=".",
        escape_char="/",
    )
    assert regex.match(search_string) is not None


def test_basic_regex_escape_char_2():
    search_string = r"This is a . sign"
    pattern = r"This is a /. sign"
    regex = like_pattern_to_re(
        pattern,
        nocase=True,
        wildcard="%",
        single_char=".",
        escape_char="/",
    )
    assert regex.match(search_string) is not None


@pytest.mark.parametrize(
    "identifier, expected",
    [
        ("4326", 4326),
        ("EPSG:3004", 3004),
        (" epsg:3857 ", 3857),
        ("urn:ogc:def:crs:EPSG::4326", 4326),
        ("urn:ogc:def:crs:EPSG:6.6:3004", 3004),
        ("urn:ogc:def:crs:EPSG:1.3:3035", 3035),
        ("urn:ogc:def:crs:EPSG:4326", 4326),
        ("urn:x-ogc:def:crs:EPSG:6.11.2:3857", 3857),
        ("URN:OGC:DEF:CRS:epsg::4326", 4326),
        ("urn:EPSG:geographicCRS:4326", 4326),
        ("urn:EPSG:projectedCRS:3004", 3004),
        ("urn:ogc:def:crs:OGC:1.3:CRS27", 4267),
        ("urn:ogc:def:crs:OGC:1.3:CRS83", 4269),
        ("urn:ogc:def:crs:OGC:1.3:CRS84", 4326),
        ("urn:ogc:def:crs:OGC::CRS84h", 4979),
        ("OGC:CRS84", 4326),
        ("CRS:27", 4267),
        ("CRS:83", 4269),
        ("CRS:84", 4326),
        ("CRS:88", 5703),
        ("OGC:CRS88", 5703),
        ("http://www.opengis.net/def/crs/EPSG/0/4326", 4326),
        ("https://www.opengis.net/def/crs/epsg/9.8.4/3004/", 3004),
        ("https://www.opengis.net/def/crs/OGC/1.3/CRS83", 4269),
        ("https://www.opengis.net/def/crs/OGC/0/CRS84h", 4979),
        ("http://www.opengis.net/gml/srs/epsg.xml#4326", 4326),
        ("https://www.opengis.net/gml/srs/EPSG.xml#3004", 3004),
        ("https://crs.example/def/crs/EPSG/0/3857", 3857),
        ("https://crs.example/def/crs/%45PSG/0/%34%33%32%36", 4326),
        ("https://crs.example/gml/srs/epsg.xml#%34%33%32%36", 4326),
        ("https://www.opengis.net/def/crs/EPSG/0/4326?format=gml", 4326),
        ("https://spatialreference.org/ref/epsg/4326/", 4326),
        ("https://epsg.io/3004", 3004),
        ("http://www.epsg.io/3857/", 3857),
        ("https://epsg.org/crs_4326/WGS-84.html", 4326),
        ("https://www.epsg.org/crs_3857", 3857),
    ],
)
def test_extract_srid(identifier, expected):
    assert extract_srid(identifier) == expected


@pytest.mark.parametrize(
    "identifier",
    [
        "",
        "not-a-crs",
        "0",
        "EPSG:0",
        "EPSG:-4326",
        "EPSG:4326junk",
        "EPSG:٤٣٢٦",
        "ESRI:102100",
        "urn:ogc:def:crs:ESRI::102100",
        "urn:ogc:def:datum:EPSG::6326",
        "urn:ogc:def:crs:EPSG:6.6:",
        "urn:ogc:def:crs:EPSG::4326:extra",
        "urn:ogc:def:crs,crs:EPSG::4326,crs:EPSG::5703",
        "urn:ogc:def:crs:OGC:1.3:CRS1",
        "urn:ogc:def:crs:OGC:1.3:fakeCRS83",
        "https://www.opengis.net/def/crs/ESRI/0/102100",
        "https://www.opengis.net/def/crs/OGC/0/4326",
        "https://www.opengis.net/def/crs/EPSG/0/",
        "https://www.opengis.net/def/crs/EPSG/4326",
        "https://www.opengis.net/def/crs/EPSG/0/4326/extra",
        "https://www.opengis.net/def/crs/EPSG/0/4326#3857",
        "https://www.opengis.net/def/uom/EPSG/0/9001",
        "https://www.opengis.net/def/crs-compound?1=4326&2=5703",
        "https://example.com/4326",
        "https://example.com/CRS83",
        "https://example.com/?crs=EPSG:4326",
        "https://epsg.io/4326junk",
        "https://epsg.io.evil.example/4326",
        "ftp://www.opengis.net/def/crs/EPSG/0/4326",
        "/def/crs/EPSG/0/4326",
        "https://epsg.org/datum_6326/World-Geodetic-System-1984.html",
        "https://epsg.org.evil.example/crs_4326/WGS-84.html",
    ],
)
def test_extract_srid_invalid(identifier):
    with pytest.raises(ValueError, match="Could not extract an EPSG SRID"):
        extract_srid(identifier)
