from tests.conftest import my_vcr
from didww.resources.voice_in_trunk_group import VoiceInTrunkGroup
from didww.resources.voice_in_trunk import VoiceInTrunk


class TestVoiceInTrunkGroup:
    @my_vcr.use_cassette("voice_in_trunk_groups/list.yaml")
    def test_list_voice_in_trunk_groups(self, client):
        response = client.voice_in_trunk_groups().list()
        assert len(response.data) > 0

    @my_vcr.use_cassette("voice_in_trunk_groups/create.yaml")
    def test_create_voice_in_trunk_group(self, client):
        group = VoiceInTrunkGroup()
        group.name = "trunk group sample with 2 trunks"
        group.capacity_limit = 1000
        group.set_voice_in_trunks([
            VoiceInTrunk.build("7c15bca2-7f17-46fb-9486-7e2a17158c7e"),
            VoiceInTrunk.build("b07a4cab-48c6-4b3a-9670-11b90b81bdef"),
        ])
        response = client.voice_in_trunk_groups().create(group)
        created = response.data
        assert created.id == "b2319703-ce6c-480d-bb53-614e7abcfc96"
        assert created.name == "trunk group sample with 2 trunks"
        assert created.capacity_limit == 1000
