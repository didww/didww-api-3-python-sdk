import json
import os
import pytest
import vcr

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def _json_body_matcher(r1, r2):
    if r1.body is None and r2.body is None:
        return True
    if r1.body is None or r2.body is None:
        return False
    try:
        b1 = r1.body if isinstance(r1.body, str) else r1.body.decode("utf-8")
        b2 = r2.body if isinstance(r2.body, str) else r2.body.decode("utf-8")
        return json.loads(b1) == json.loads(b2)
    except (TypeError, json.JSONDecodeError, UnicodeDecodeError):
        return r1.body == r2.body


my_vcr = vcr.VCR(
    cassette_library_dir=FIXTURES_DIR,
    record_mode="none",
    match_on=["method", "path", "body"],
)
my_vcr.register_matcher("body", _json_body_matcher)

my_vcr_no_body = vcr.VCR(
    cassette_library_dir=FIXTURES_DIR,
    record_mode="none",
    match_on=["method", "path"],
)


@pytest.fixture
def client():
    from didww.client import DidwwClient
    from didww.configuration import Environment

    return DidwwClient(api_key="test-api-key", environment=Environment.SANDBOX)
