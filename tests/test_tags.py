from django.test import RequestFactory

from beam.templatetags.beam_tags import preserve_query_string, _add_params_to_url_if_new


def test_preserve_query_string_preserves_query_string():
    request = RequestFactory().get("/", data={"a": "b"})
    query = preserve_query_string({"request": request}, page="1")
    assert query == "?a=b&page=1"


def test_preserve_query_string_works_with_mulitple_arguments():
    request = RequestFactory().get("/", data={"a": ["b", "c"]})
    query = preserve_query_string({"request": request}, page="1")
    assert query == "?a=b&a=c&page=1"


def test_add_url_params_works():
    url = "https://example.com"
    assert (
        _add_params_to_url_if_new(url, {"foo": "bar"}) == "https://example.com?foo=bar"
    )


def test_add_url_params_preserves_existing():
    url = "https://example.com?one=1"
    assert (
        _add_params_to_url_if_new(url, {"foo": "bar"})
        == "https://example.com?foo=bar&one=1"
    )


def test_add_url_params_prefers_existing():
    url = "https://example.com?one=1"
    assert _add_params_to_url_if_new(url, {"one": "2"}) == "https://example.com?one=1"
