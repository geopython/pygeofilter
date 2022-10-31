from datetime import date, datetime, timedelta
from typing import Dict, Union

from lxml import etree

from ... import values
from ...util import parse_datetime, parse_duration
from .util import Element

Temporal = Union[date, datetime, timedelta, values.Interval]


def _parse_time_position(node: Element, nsmap: Dict[str, str]) -> datetime:
    return parse_datetime(node.text)


def _parse_time_instant(node: Element, nsmap: Dict[str, str]) -> datetime:
    position = node.xpath("gml:timePosition", namespaces=nsmap)[0]
    return _parse_time_position(position, nsmap)


def _parse_time_period(node: Element, nsmap: Dict[str, str]) -> values.Interval:
    begin = node.xpath(
        "gml:begin/gml:TimeInstant/gml:timePosition|gml:beginPosition", namespaces=nsmap
    )[0]
    end = node.xpath(
        "gml:end/gml:TimeInstant/gml:timePosition|gml:endPosition", namespaces=nsmap
    )[0]
    return values.Interval(
        _parse_time_position(begin, nsmap),
        _parse_time_position(end, nsmap),
    )


def _parse_valid_time(node: Element, nsmap: Dict[str, str]) -> Temporal:
    return parse_temporal(node[0], nsmap)


def _parse_duration(node: Element, nsmap: Dict[str, str]) -> timedelta:
    return parse_duration(node.text)


PARSER_MAP = {
    "validTime": _parse_valid_time,
    "timePosition": _parse_time_position,
    "TimeInstant": _parse_time_instant,
    "TimePeriod": _parse_time_period,
    "duration": _parse_duration,
}


def is_temporal(node: Element) -> bool:
    return etree.QName(node).localname in PARSER_MAP


def parse_temporal(node: Element, nsmap: Dict[str, str]) -> Temporal:
    parser = PARSER_MAP[etree.QName(node).localname]
    return parser(node, nsmap)
