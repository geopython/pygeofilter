from dateparser import parse as parse_datetime
from lark import Transformer, v_args

from ..util import parse_duration


@v_args(inline=True)
class ISO8601Transformer(Transformer):
    def DATETIME(self, dt):
        return parse_datetime(dt)

    def DURATION(self, duration):
        return parse_duration(duration)
