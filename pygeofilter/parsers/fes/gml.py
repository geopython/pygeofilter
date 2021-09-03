from lxml import etree
from dateparser import parse as parse_datetime

from ... import values
from ... import util


def _parse_time_position(node, nsmap):
    return parse_datetime(node.text)


def _parse_time_instant(node, nsmap):
    position = node.xpath('gml:timePosition', namespaces=nsmap)[0]
    return _parse_time_position(position, nsmap)


def _parse_time_period(node, nsmap):
    begin = node.xpath(
        'gml:begin/gml:TimeInstant/gml:timePosition|gml:beginPosition',
        namespaces=nsmap
    )[0]
    end = node.xpath(
        'gml:end/gml:TimeInstant/gml:timePosition|gml:endPosition',
        namespaces=nsmap
    )[0]
    return values.Interval(
        _parse_time_position(begin, nsmap),
        _parse_time_position(end, nsmap),
    )


def _parse_valid_time(node, nsmap):
    return parse_temporal(node[0])


def _parse_duration(node, nsmap):
    return util.parse_duration(node.text)


PARSER_MAP = {
    'validTime': _parse_valid_time,
    'timePosition': _parse_time_position,
    'TimeInstant': _parse_time_instant,
    'TimePeriod': _parse_time_period,
    'duration': _parse_duration,
}


def is_temporal(node):
    return etree.QName(node).localname in PARSER_MAP


def parse_temporal(node, nsmap):
    parser = PARSER_MAP[etree.QName(node).localname]
    return parser(node, nsmap)
