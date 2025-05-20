
# tester
# URL: .../items?filter=title = 'test' AND description = 'test2'

from pygeofilter.backends.solr import to_filter
from pygeofilter.parsers.cql2_text import parse


# AND
print('Testing AND')
ast = parse("title = 'test' and description = 'test2'")

print('AST AND: ', ast)

solr_filter = to_filter(ast)

print('SOLR filter AND: ', solr_filter)
print('\n')

# OR
print('Testing OR')
ast = parse("title = 'test' or description = 'test2'")

print('AST OR: ', ast)

solr_filter = to_filter(ast)

print('SOLR filter OR: ', solr_filter)
print('\n')

# =
print('Testing Equals =')
ast = parse("int_attribute = 5")
print('AST =: ', ast)

solr_filter = to_filter(ast)
print('SOLR filter =: ', solr_filter)
print('\n')

# <>
print('Testing NOT EQUAL <>')
ast = parse("int_attribute <> 0.0")
print('AST <>: ', ast)

solr_filter = to_filter(ast)
print('SOLR filter <>: ', solr_filter)
print('\n')

# <
print('Testing LessThan <')
ast = parse("float_attribute < 6")
print('AST <: ', ast)

solr_filter = to_filter(ast)
print('SOLR filter <: ', solr_filter)
print('\n')


# >
print('Testing GraterThan >')
ast = parse("float_attribute > 6")
print('AST >: ', ast)

solr_filter = to_filter(ast)
print('SOLR filter >: ', solr_filter)
print('\n')


# <=
print('Testing LessEqual <=')
ast = parse("int_attribute <= 6")
print('AST <=: ', ast)

solr_filter = to_filter(ast)
print('SOLR filter <=: ', solr_filter)
print('\n')


# >=
print('Testing LessEqual >=')
ast = parse("float_attribute >= 8")
print('AST >=: ', ast)

solr_filter = to_filter(ast)
print('SOLR filter >=: ', solr_filter)
print('\n')


# Combination AND
print('Testing Combination AND')
ast = parse("int_attribute = 5 AND float_attribute < 6.0")
print('AST Combination AND: ', ast)

solr_filter = to_filter(ast)
print('SOLR filter Combination AND: ', solr_filter)
print('\n')


# Combination OR
print('Testing Combination OR')
ast = parse("int_attribute = 6 OR float_attribute < 6.0")
print('AST Combination OR: ', ast)

solr_filter = to_filter(ast)
print('SOLR filter Combination OR: ', solr_filter)
print('\n')


# Between
print('Testing BETWEEN')
ast = parse("float_attribute BETWEEN -1 AND 1")
print('AST BETWEEN: ', ast)

solr_filter = to_filter(ast)
print('SOLR filter BETWEEN: ', solr_filter)
print('\n')



# NOT Between
print('Testing NOT BETWEEN')
ast = parse("int_attribute NOT BETWEEN 4 AND 6")
print('AST NOT BETWEEN: ', ast)

solr_filter = to_filter(ast)
print('SOLR filter NOT BETWEEN: ', solr_filter)
print('\n')
