
# tester
# URL: .../items?filter=title = 'test' AND description = 'test2'

from pygeofilter import ast
from pygeofilter.backends.solr import to_filter
from pygeofilter.parsers.ecql import parse


# AND
print('Testing AND')
ast = parse("title = 'test' AND description = 'test2'")

print('AST AND: ', ast)

solr_filter = to_filter(ast)

print('SOLR filter AND: ', solr_filter)
print('\n')

# OR
print('Testing OR')
ast = parse("title = 'test' OR description = 'test2'")

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


# NOT Between
print('Testing NOT BETWEEN')
ast = parse("int_attribute NOT BETWEEN 4 AND 6")
print('AST NOT BETWEEN: ', ast)

solr_filter = to_filter(ast)
print('SOLR filter NOT BETWEEN: ', solr_filter)
print('\n')


# IS_NULL
print('Testing IS_NULL')
ast = parse("maybe_str_attribute IS NULL")
print('AST IS_NULL: ', ast)

solr_filter = to_filter(ast)
print('SOLR filter IS_NULL: ', solr_filter)
print('\n')


# IS_NOT_NULL
print('Testing IS_NOT_NULL')
ast = parse("maybe_str_attribute IS NOT NULL")
print('AST IS_NOT_NULL: ', ast)

solr_filter = to_filter(ast)
print('SOLR filter IS_NOT_NULL: ', solr_filter)
print('\n')

# IS_IN
print('Testing IN')
ast = parse("int_attribute IN ( 1, 2, 3, 4, 5 )")
print('AST IN: ', ast)

solr_filter = to_filter(ast)
print('SOLR filter IN: ', solr_filter)
print('\n')

# IS_NOT_IN
print('Testing NOT IN')
ast = parse("int_attribute NOT IN ( 1, 2, 3, 4, 5 )")
print('AST NOT IN: ', ast)

solr_filter = to_filter(ast)
print('SOLR filter NOT IN: ', solr_filter)
print('\n')

# LIKE
print('Testing LIKE')
ast = parse("str_attribute LIKE 'this is a test'")
print('AST LIKE: ', ast)

solr_filter = to_filter(ast)
print('SOLR filter LIKE: ', solr_filter)
print('\n')


# LIKE %
print('Testing LIKE %')
ast = parse("str_attribute LIKE 'this is % test'")
print('AST LIKE %: ', ast)

solr_filter = to_filter(ast)
print('SOLR filter LIKE %: ', solr_filter)
print('\n')

# NOT LIKE %
print('Testing NOT LIKE %')
ast = parse("str_attribute NOT LIKE '% another test'")
print('AST NOT LIKE %: ', ast)

solr_filter = to_filter(ast)
print('SOLR filter NOT LIKE %: ', solr_filter)
print('\n')


# NOT LIKE .
print('Testing NOT LIKE .')
ast = parse("str_attribute NOT LIKE 'this is . test'")
print('AST NOT LIKE .: ', ast)

solr_filter = to_filter(ast)
print('SOLR filter NOT LIKE .: ', solr_filter)
print('\n')


# ILIKE .
print('Testing ILIKE .')
ast = parse("str_attribute ILIKE 'THIS IS . TEST'")
print('AST ILIKE .: ', ast)

solr_filter = to_filter(ast)
print('SOLR filter ILIKE .: ', solr_filter)
print('\n')


# ILIKE %
print('Testing ILIKE %')
ast = parse("str_attribute ILIKE 'THIS IS % TEST'")
print('AST ILIKE %: ', ast)

solr_filter = to_filter(ast)
print('SOLR filter ILIKE %: ', solr_filter)
print('\n')


# EXISTS
print('Testing EXISTS')
ast = parse("extra_attr EXISTS")
print('AST EXISTS: ', ast)

solr_filter = to_filter(ast)
print('SOLR filter EXISTS: ', solr_filter)
print('\n')


# DOES-NOT-EXIST
print('Testing DOES-NOT-EXIST')
ast = parse("extra_attr DOES-NOT-EXIST")
print('AST DOES-NOT-EXIST: ', ast)

solr_filter = to_filter(ast)
print('SOLR filter DOES-NOT-EXIST: ', solr_filter)
print('\n')


#Testing temporal BEFORE
print('Testing datetime attribute BEFORE')
ast = parse("datetime_attribute BEFORE 2000-01-01T00:00:05.00Z")
print('AST BEFORE:', ast)

solr_filter = to_filter(ast)
print('datetime attribute BEFORE: ', solr_filter)
print('\n')


#Testing temporal AFTER
print('Testing datetime attribute AFTER')
ast = parse("datetime_attribute AFTER 2000-01-01T00:00:05.00Z")
print('AST AFTER:', ast)

solr_filter = to_filter(ast)
print('datetime attribute AFTER: ', solr_filter)
print('\n')


#Testing temporal AFTER
# print('Testing datetime attribute DISJOINT')
# ast = ast.TimeDisjoint(
#             ast.Attribute("datetime_attribute"),
#             [
#                 parse_datetime("2000-01-01T00:00:05.00Z"),
#                 parse_datetime("2000-01-01T00:00:15.00Z"),
#             ],
#         )
# print('AST AFTER:', ast)

# solr_filter = to_filter(ast)
# print('datetime attribute AFTER: ', solr_filter)
# print('\n')


# Test spatial Intersects
print('Testing Spatial Intersects')
ast = parse("INTERSECTS(geometry, ENVELOPE (0.0 1.0 0.0 1.0))")
print('AST Spatial Intersects:', ast)

solr_filter = to_filter(ast)
print('Spatial Intersects: ', solr_filter)
print('\n')


# Test spatial Disjoint
print('Testing Spatial Disjoint')
ast = parse("DISJOINT(geometry, ENVELOPE (0.0 1.0 0.0 1.0))")
print('AST Spatial Disjoint:', ast)

solr_filter = to_filter(ast)
print('Spatial Disjoint: ', solr_filter)
print('\n')


# Test spatial Within
print('Testing Spatial Within')
ast = parse("WITHIN(geometry, ENVELOPE (0.0 1.0 0.0 1.0))")
print('AST Spatial Within:', ast)

solr_filter = to_filter(ast)
print('Spatial Within: ', solr_filter)
print('\n')


# Test spatial Contains
print('Testing Spatial Contains')
ast = parse("CONTAINS(geometry, ENVELOPE (0.0 1.0 0.0 1.0))")
print('AST Spatial Contains:', ast)

solr_filter = to_filter(ast)
print('Spatial Contains: ', solr_filter)
print('\n')

# Test spatial Equals
print('Testing Spatial Equals')
ast = parse("EQUALS(geometry, ENVELOPE (0.0 1.0 0.0 1.0))")
print('AST Spatial Equals:', ast)

solr_filter = to_filter(ast)
print('Spatial Equals: ', solr_filter)
print('\n')


# Test spatial BBOX
print('Testing Spatial BBOX')
ast = parse("BBOX(center, 2, 2, 3, 3)")
print('AST Spatial BBOX:', ast)

solr_filter = to_filter(ast)
print('Spatial BBOX: ', solr_filter)
print('\n')