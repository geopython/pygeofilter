# ------------------------------------------------------------------------------
#
# Project: pygeofilter <https://github.com/geopython/pygeofilter>
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2025 Tom Kralidis
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

import logging
import sys

import click

from .parsers.cql_json.parser import parse as parse_cql_json
from .parsers.cql2_json.parser import parse as parse_cql2_json
from .parsers.cql2_text.parser import parse as parse_cql2_text
from .parsers.ecql.parser import parse as parse_ecql
from .parsers.fes.parser import parse as parse_fes
from .parsers.jfe.parser import parse as parse_jfe
from .version import __version__

__all__ = ["__version__"]

PARSERS = {
    'cql_json': parse_cql_json,
    'cql2_json': parse_cql2_json,
    'cql2_text': parse_cql2_text,
    'ecql': parse_ecql,
    'fes': parse_fes,
    'jfe': parse_jfe
}


def CLI_OPTION_VERBOSITY(f):
    """Setup click logging output"""
    def callback(ctx, param, value):
        if value is not None:
            logging.basicConfig(stream=sys.stdout,
                                level=getattr(logging, value))
        return True

    return click.option('--verbosity', '-v',
                        type=click.Choice(['ERROR', 'WARNING', 'INFO', 'DEBUG']),
                        help='Verbosity',
                        callback=callback)(f)


@click.group()
@click.version_option(version=__version__)
def cli():
    pass


@cli.command()
@click.pass_context
@click.argument('parser', type=click.Choice(PARSERS.keys()))
@click.argument('query')
@CLI_OPTION_VERBOSITY
def parse(ctx, parser, query, verbosity):
    """Parse a query into an abstract syntax tree"""

    click.echo(f'Parsing {parser} query into AST')
    try:
        click.echo(PARSERS[parser](query))
    except Exception as err:
        raise click.ClickException(err)


cli.add_command(parse)
