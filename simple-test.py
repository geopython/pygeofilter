
# tester
# URL: .../items?filter=title = 'test' AND description = 'test2'

from pygeofilter.backends.solr import to_filter
from pygeofilter.parsers.cql2_text import parse

ast = parse("title = 'test' and description = 'test2'")

print('AST: ', ast)

solr_filter = to_filter(ast)

print('SOLR filter: ', solr_filter)
