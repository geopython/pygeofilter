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


from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Any, List, Optional, Union

from pygeoif import shape


@dataclass
class Geometry:
    geometry: dict

    @property
    def __geo_interface__(self):
        return self.geometry

    def __eq__(self, o: object) -> bool:
        return shape(self).__geo_interface__ == shape(o).__geo_interface__


@dataclass
class Envelope:
    x1: float
    x2: float
    y1: float
    y2: float

    @property
    def geometry(self):
        return {
            "type": "Polygon",
            "coordinates": [
                [
                    [self.x1, self.y1],
                    [self.x1, self.y2],
                    [self.x2, self.y2],
                    [self.x2, self.y1],
                    [self.x1, self.y1],
                ]
            ],
        }

    @property
    def __geo_interface__(self):
        return self.geometry

    def __eq__(self, o: object) -> bool:
        return shape(self).__geo_interface__ == shape(o).__geo_interface__


@dataclass
class Interval:
    start: Optional[Union[date, datetime, timedelta]] = None
    end: Optional[Union[date, datetime, timedelta]] = None

    def get_sub_nodes(self) -> List[Any]:  # TODO: find way to type this
        return [self.start, self.end]


# used for handler declaration
LITERALS = (list, str, float, int, bool, datetime, date, time, timedelta)

# used for type checking

SpatialValueType = Union[Geometry, Envelope]

TemporalValueType = Union[date, datetime, timedelta, Interval]

ValueType = Union[
    SpatialValueType,
    TemporalValueType,
    bool,
    float,
    int,
    str,
]
