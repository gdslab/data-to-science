from app.api.api_v1.endpoints.tusd import _extract_access_token_from_cookie_headers


def test_extract_access_token_strips_quotes_and_bearer() -> None:
    headers = ['access_token="Bearer abc.def.ghi"; refresh_token="Bearer r"']
    assert _extract_access_token_from_cookie_headers(headers) == "abc.def.ghi"


def test_extract_access_token_url_decodes_value() -> None:
    headers = ["access_token=%22Bearer%20abc.def.ghi%22"]
    assert _extract_access_token_from_cookie_headers(headers) == "abc.def.ghi"


def test_extract_access_token_prefers_last_duplicate_in_header() -> None:
    # Browsers send a stale unpartitioned cookie before the current Partitioned
    # one with the same name; the last occurrence is the current token.
    headers = [
        'access_token="Bearer old"; refresh_token="Bearer r"; access_token="Bearer new"'
    ]
    assert _extract_access_token_from_cookie_headers(headers) == "new"


def test_extract_access_token_prefers_last_duplicate_across_headers() -> None:
    headers = ['access_token="Bearer old"', 'access_token="Bearer new"']
    assert _extract_access_token_from_cookie_headers(headers) == "new"


def test_extract_access_token_missing() -> None:
    assert _extract_access_token_from_cookie_headers(None) is None
    assert _extract_access_token_from_cookie_headers([]) is None
    headers = ['refresh_token="Bearer r"']
    assert _extract_access_token_from_cookie_headers(headers) is None
