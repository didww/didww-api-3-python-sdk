from tests.conftest import my_vcr


class TestPublicKey:
    @my_vcr.use_cassette("public_keys/list.yaml")
    def test_list_public_keys(self, client):
        response = client.public_keys().list()
        assert len(response.data) == 2
        first = response.data[0]
        assert first.id == "dcf2bfcb-a1d0-3b58-bbf0-3ec22a510ba8"
        assert "BEGIN PUBLIC KEY" in first.key
