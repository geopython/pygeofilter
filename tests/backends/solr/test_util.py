from pygeofilter.backends.elasticsearch.util import like_to_wildcard


def test_like_to_wildcard():
    assert "This ? a test" == like_to_wildcard("This . a test", "*", ".")
    assert "This * a test" == like_to_wildcard("This * a test", "*", ".")
