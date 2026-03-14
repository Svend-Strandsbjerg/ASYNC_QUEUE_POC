import async_queue_poc.api as api


def test_api_module_is_reserved_for_optional_http_wrapper():
    assert "optional HTTP wrappers" in api.__doc__
