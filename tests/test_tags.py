from urllib.parse import parse_qs

from django.http import QueryDict
from django.test import RequestFactory

from beam.templatetags.beam_tags import preserve_query_string


def test_preserve_query_string_preserves_query_string():
    request = RequestFactory().get("/", data={"a": "b"})
    query = preserve_query_string({"request": request}, page="1")
    assert query == "?a=b&page=1"


def test_preserve_query_string_works_with_mulitple_arguments():
    request = RequestFactory().get("/", data={"a": ["b", "c"]})
    query = preserve_query_string({"request": request}, page="1")
    assert query == "?a=b&a=c&page=1"
