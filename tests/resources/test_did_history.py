from datetime import datetime, timezone

from tests.conftest import my_vcr


class TestDidHistory:
    @my_vcr.use_cassette("did_history/list.yaml")
    def test_list_did_history(self, client):
        response = client.did_history().list()
        assert len(response.data) == 2
        first = response.data[0]
        assert first.did_number == "12025551234"
        assert first.action == "assigned"
        assert first.method == "api3"

    @my_vcr.use_cassette("did_history/show.yaml")
    def test_find_did_history(self, client):
        response = client.did_history().find("a1b2c3d4-e5f6-7890-abcd-ef1234567890")
        record = response.data
        assert record.id == "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        assert record.did_number == "12025551234"
        assert record.action == "assigned"
        assert record.method == "api3"
        assert record.created_at == datetime(2026, 4, 10, 14, 30, 0, 0, tzinfo=timezone.utc)
