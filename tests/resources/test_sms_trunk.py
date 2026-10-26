import json
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from tests.conftest import my_vcr
from didww.enums import SmsBodyType, SmsHttpMethod, SmsServerLocation
from didww.exceptions import DidwwApiError
from didww.query_params import QueryParams
from didww.resources.did import Did
from didww.resources.sender_id_verification import SenderIdVerification
from didww.resources.sms_trunk import SmsTrunk
from didww.resources.sms_trunk_configuration import (
    GenericSmsTrunkConfiguration,
    HttpInConfiguration,
    HttpOutConfiguration,
    SmppEsmeConfiguration,
    SmppSmscConfiguration,
    SmsToEmailConfiguration,
)
from didww.resources.sms_trunk_group import SmsTrunkGroup

HTTP_IN_ID = "1a2b3c4d-0002-4a5b-8c6d-7e8f9a0b1c02"
HTTP_OUT_ID = "1a2b3c4d-0003-4a5b-8c6d-7e8f9a0b1c03"
UNKNOWN_ID = "1a2b3c4d-0006-4a5b-8c6d-7e8f9a0b1c06"
GROUP_ID = "2b3c4d5e-0001-4b6c-9d7e-8f9a0b1c2d01"
DID_ID = "9df99644-f1a5-4a3c-99a4-559d758eb96b"
HOST = "https://sms-out.example.com/outbound_messages"


def sent_body(cassette):
    return json.loads(cassette.requests[-1].body, parse_float=Decimal)


def assert_cleared_http_in(config):
    assert isinstance(config, HttpInConfiguration)
    assert config.http_method == SmsHttpMethod.GET
    assert config.body_type is None
    assert config.body is None
    assert config.url == "https://example.com/sms/v2"


class TestSmsTrunkRead:
    @my_vcr.use_cassette("sms_trunks/list.yaml")
    def test_list_dispatches_every_configuration_type(self, client):
        response = client.sms_trunks().list()
        trunks = response.data
        assert [type(t.configuration) for t in trunks] == [
            SmsToEmailConfiguration,
            HttpInConfiguration,
            HttpOutConfiguration,
            SmppEsmeConfiguration,
            SmppSmscConfiguration,
        ]
        assert response.meta["total_records"] == 5
        email, http_in, http_out, esme, smsc = trunks
        assert email.name == "sms_to_email trunk"
        assert email.priority == 100
        assert email.allow_in is True
        assert email.allow_out is False
        assert email.blocked is False
        assert email.allow_any_did_as_source is False
        assert email.created_at == datetime(2026, 10, 1, 10, 0, tzinfo=timezone.utc)
        assert email.configuration.send_to == "sms@example.com"
        assert http_in.configuration.http_method == SmsHttpMethod.POST
        assert http_in.configuration.body_type == SmsBodyType.JSON
        assert http_in.configuration.headers == {"X-Source": "didww"}
        assert http_out.priority is None
        assert http_out.host == HOST
        assert http_out.configuration.auth_name == "generated-name"
        assert esme.configuration.server_location == SmsServerLocation.NYC
        assert esme.host is None
        assert smsc.configuration.tx_port == 2775

    @my_vcr.use_cassette("sms_trunks/list_with_sms_trunk_group.yaml")
    def test_list_with_included_sms_trunk_group(self, client):
        trunks = client.sms_trunks().list(QueryParams().include("sms_trunk_group")).data
        group = trunks[0].sms_trunk_group
        assert isinstance(group, SmsTrunkGroup)
        assert group.id == GROUP_ID
        assert group.name == "Inbound SMS"

    @my_vcr.use_cassette("sms_trunks/show.yaml")
    def test_find_http_out_trunk(self, client):
        trunk = client.sms_trunks().find(HTTP_OUT_ID).data
        assert trunk.id == HTTP_OUT_ID
        assert trunk.name == "http_out trunk"
        assert trunk.host == HOST
        assert trunk.meta == {"host": HOST}
        config = trunk.configuration
        assert isinstance(config, HttpOutConfiguration)
        assert config.callback_url == "https://example.com/sms/status"
        assert config.allowed_ips == ["203.0.113.10"]
        assert config.auth_name == "generated-name"
        assert config.auth_password == "generated-password"  # NOSONAR
        assert trunk.sms_trunk_group is None

    @my_vcr.use_cassette("sms_trunks/show_with_sender_id_verifications.yaml")
    def test_find_with_sender_id_verifications(self, client):
        params = QueryParams().include("sender_id_verifications")
        trunk = client.sms_trunks().find(HTTP_OUT_ID, params).data
        verifications = trunk.sender_id_verifications
        assert len(verifications) == 1
        assert isinstance(verifications[0], SenderIdVerification)
        assert verifications[0].name == "ACME alerts"

    @my_vcr.use_cassette("sms_trunks/show_not_found.yaml")
    def test_find_not_found(self, client):
        with pytest.raises(DidwwApiError) as exc_info:
            client.sms_trunks().find(HTTP_OUT_ID)
        assert exc_info.value.status_code == 404
        assert exc_info.value.errors[0]["title"] == "Record not found"

    def test_loaded_trunk_repr_does_not_show_credentials(self):
        trunk = SmsTrunk.from_jsonapi({
            "id": HTTP_OUT_ID,
            "type": "sms_trunks",
            "attributes": {"configuration": {"type": "http_out", "attributes": {
                "auth_name": "generated-name", "auth_password": "generated-password"}}},
        })
        assert "generated" not in repr(trunk)
        assert "generated" not in repr(trunk.configuration)
        assert "generated" not in str(trunk.configuration)


class TestSmsTrunkCreate:
    @my_vcr.use_cassette("sms_trunks/create_sms_to_email.yaml")
    def test_create_sms_to_email(self, client):
        config = SmsToEmailConfiguration()
        config.send_to = "sms@example.com"
        config.subject = "Inbound SMS"
        config.message = "You have a new message."
        trunk = SmsTrunk()
        trunk.name = "sms_to_email trunk"
        trunk.configuration = config
        created = client.sms_trunks().create(trunk).data
        assert created.id == "1a2b3c4d-0001-4a5b-8c6d-7e8f9a0b1c01"
        assert isinstance(created.configuration, SmsToEmailConfiguration)

    @my_vcr.use_cassette("sms_trunks/create_http_in.yaml")
    def test_create_http_in(self, client):
        config = HttpInConfiguration()
        config.url = "https://example.com/sms"
        config.http_method = SmsHttpMethod.POST
        config.headers = {"X-Source": "didww"}
        config.body_type = SmsBodyType.JSON
        config.body = '{"text":"{SMS_TEXT}","from":"{SMS_SRC_ADDR}"}'
        config.follow_redirect = False
        config.validate_https_certificate = True
        trunk = SmsTrunk()
        trunk.name = "http_in trunk"
        trunk.configuration = config
        created = client.sms_trunks().create(trunk).data
        assert created.id == HTTP_IN_ID
        assert created.configuration.http_method == SmsHttpMethod.POST

    @my_vcr.use_cassette("sms_trunks/create_http_out.yaml")
    def test_create_http_out_keeps_meta_host(self, client):
        config = HttpOutConfiguration()
        config.callback_url = "https://example.com/sms/status"
        config.allowed_ips = ["203.0.113.10"]
        trunk = SmsTrunk()
        trunk.name = "http_out trunk"
        trunk.configuration = config
        created = client.sms_trunks().create(trunk).data
        assert created.id == HTTP_OUT_ID
        assert created.priority is None
        assert created.host == HOST
        assert created.configuration.auth_password == "generated-password"  # NOSONAR

    @my_vcr.use_cassette("sms_trunks/create_smpp_esme.yaml")
    def test_create_smpp_esme(self, client):
        config = SmppEsmeConfiguration()
        config.allowed_ips = ["203.0.113.10"]
        config.server_location = SmsServerLocation.NYC
        trunk = SmsTrunk()
        trunk.name = "smpp_esme trunk"
        trunk.configuration = config
        created = client.sms_trunks().create(trunk).data
        assert created.configuration.system_id == "esme1234"
        assert created.configuration.password == "gen12345"  # NOSONAR

    @my_vcr.use_cassette("sms_trunks/create_smpp_smsc.yaml")
    def test_create_smpp_smsc(self, client):
        config = SmppSmscConfiguration()
        config.host = "smsc.example.com"
        config.tx_port = 2775
        config.rx_port = 2776
        config.transceiver_mode = True
        config.connection_timeout = 30
        config.use_ssl = False
        config.system_id = "didww"
        config.password = "secret"  # NOSONAR
        config.server_location = SmsServerLocation.NYC
        trunk = SmsTrunk()
        trunk.name = "smpp_smsc trunk"
        trunk.configuration = config
        created = client.sms_trunks().create(trunk).data
        assert created.id == "1a2b3c4d-0005-4a5b-8c6d-7e8f9a0b1c05"
        assert created.configuration.system_type is None

    @my_vcr.use_cassette("sms_trunks/create_with_relationships.yaml")
    def test_create_with_relationships(self, client):
        config = SmppSmscConfiguration()
        config.host = "smsc.example.com"
        config.system_id = "didww"
        config.password = "secret"  # NOSONAR
        config.server_location = SmsServerLocation.NYC
        trunk = SmsTrunk()
        trunk.name = "smpp_smsc trunk"
        trunk.configuration = config
        trunk.sms_trunk_group = SmsTrunkGroup.build(GROUP_ID)
        trunk.outgoing_dids = [Did.build(DID_ID)]
        assert client.sms_trunks().create(trunk).data.id == "1a2b3c4d-0005-4a5b-8c6d-7e8f9a0b1c05"

    @my_vcr.use_cassette("sms_trunks/create_error.yaml")
    def test_create_error(self, client):
        trunk = SmsTrunk()
        trunk.name = "sms_to_email trunk"
        trunk.configuration = SmsToEmailConfiguration()
        with pytest.raises(DidwwApiError) as exc_info:
            client.sms_trunks().create(trunk)
        assert exc_info.value.status_code == 422
        assert "send_to" in exc_info.value.errors[0]["detail"]

    def test_create_keeps_false_and_zero(self):
        trunk = SmsTrunk()
        trunk.blocked = False
        trunk.priority = 0
        attrs = trunk.to_jsonapi()["attributes"]
        assert attrs["blocked"] is False
        assert attrs["priority"] == 0

    def test_create_drops_read_only_attributes(self):
        trunk = SmsTrunk()
        trunk.name = "n"
        trunk.attributes["allow_in"] = True
        trunk.attributes["created_at"] = "2026-10-01T10:00:00.000Z"
        assert trunk.to_jsonapi()["attributes"] == {"name": "n"}


class TestSmsTrunkUpdate:
    @my_vcr.use_cassette("sms_trunks/update_http_in.yaml")
    def test_update_name_and_url(self, client):
        trunk = SmsTrunk.build(HTTP_IN_ID)
        trunk.name = "Webhook"
        config = HttpInConfiguration()
        config.url = "https://example.com/sms/v2"
        trunk.configuration = config
        updated = client.sms_trunks().update(trunk).data
        assert updated.name == "Webhook"
        assert updated.configuration.url == "https://example.com/sms/v2"

    @my_vcr.use_cassette("sms_trunks/update_http_out_from_loaded.yaml")
    def test_update_loaded_http_out_strips_generated_credentials(self, client):
        trunk = client.sms_trunks().find(HTTP_OUT_ID).data
        config = trunk.configuration
        config.callback_url = "https://example.com/sms/status/v2"
        trunk.configuration = config
        updated = client.sms_trunks().update(trunk).data
        assert updated.configuration.callback_url == "https://example.com/sms/status/v2"
        assert updated.host == HOST

    @my_vcr.use_cassette("sms_trunks/update_loaded_no_changes.yaml")
    def test_update_loaded_without_changes_sends_empty_attributes(self, client):
        trunk = client.sms_trunks().find(HTTP_OUT_ID).data
        assert client.sms_trunks().update(trunk).data.id == HTTP_OUT_ID

    def test_editing_the_read_configuration_needs_assignment(self):
        trunk = SmsTrunk.from_jsonapi({
            "id": HTTP_IN_ID,
            "type": "sms_trunks",
            "attributes": {"configuration": {"type": "http_in", "attributes": {"url": "https://example.com/sms"}}},
        })
        trunk.configuration.url = "https://example.com/other"
        assert trunk.configuration.url == "https://example.com/sms"
        assert trunk.to_jsonapi(include_id=True, dirty_only=True)["attributes"] == {}

    def test_raw_configuration_dict_is_stripped(self):
        trunk = SmsTrunk.build(HTTP_OUT_ID, configuration={
            "type": "http_out",
            "attributes": {"callback_url": "https://example.com/cb", "auth_name": "n", "auth_password": "p"},
        })
        assert trunk.to_jsonapi(include_id=True, dirty_only=True)["attributes"] == {
            "configuration": {"type": "http_out", "attributes": {"callback_url": "https://example.com/cb"}},
        }
        trunk = SmsTrunk.build(HTTP_OUT_ID)
        trunk.configuration = {"type": "http_out", "attributes": {"auth_password": "p", "allowed_ips": None}}
        assert trunk.to_jsonapi(include_id=True, dirty_only=True)["attributes"] == {
            "configuration": {"type": "http_out", "attributes": {"allowed_ips": None}},
        }

    def test_update_unknown_configuration_keeps_exact_numbers(self, client):
        with my_vcr.use_cassette("sms_trunks/update_unknown_configuration.yaml") as cassette:
            trunk = client.sms_trunks().find(UNKNOWN_ID).data
            config = trunk.configuration
            assert isinstance(config, GenericSmsTrunkConfiguration)
            assert config.type == "future_transport"
            assert config.attributes["ratio"] == Decimal("1.10")
            assert str(config.attributes["ratio"]) == "1.10"
            assert config.attributes["sequence"] == 9007199254740993
            assert config.attributes["nested"]["ids"] == [123456789012345678901234567890]
            config.attributes["endpoint"] = "https://example.com/future/v2"
            trunk.configuration = config
            updated = client.sms_trunks().update(trunk).data

            raw = cassette.requests[-1].body
            raw = raw.decode("utf-8") if isinstance(raw, bytes) else raw
            assert '"ratio":1.10' in raw
            assert '"sequence":9007199254740993' in raw
            assert '"ids":[123456789012345678901234567890]' in raw
            sent = sent_body(cassette)["data"]["attributes"]["configuration"]["attributes"]
            assert str(sent["ratio"]) == "1.10"
            assert sent["sequence"] == 9007199254740993
            assert sent["nested"]["ids"] == [123456789012345678901234567890]
            assert "cleared" in sent["nested"] and sent["nested"]["cleared"] is None
        assert updated.configuration.attributes["endpoint"] == "https://example.com/future/v2"

    @my_vcr.use_cassette("sms_trunks/update_generic_nulls.yaml")
    def test_update_generic_configuration_sends_nulls(self, client):
        trunk = SmsTrunk.build(HTTP_IN_ID)
        trunk.configuration = GenericSmsTrunkConfiguration(
            "http_in", {"http_method": "get", "body_type": None, "body": None})
        updated = client.sms_trunks().update(trunk).data
        assert updated.id == HTTP_IN_ID
        assert_cleared_http_in(updated.configuration)

    @my_vcr.use_cassette("sms_trunks/update_generic_nulls.yaml")
    def test_update_typed_configuration_sends_nulls(self, client):
        config = HttpInConfiguration()
        config.http_method = SmsHttpMethod.GET
        config.body_type = None
        config.body = None
        trunk = SmsTrunk.build(HTTP_IN_ID)
        trunk.configuration = config
        updated = client.sms_trunks().update(trunk).data
        assert updated.id == HTTP_IN_ID
        assert_cleared_http_in(updated.configuration)

    @my_vcr.use_cassette("sms_trunks/update_clear_relationships.yaml")
    def test_update_clears_relationships(self, client):
        trunk = SmsTrunk.build(HTTP_IN_ID)
        trunk.sms_trunk_group = None
        trunk.outgoing_dids = []
        assert trunk.sms_trunk_group is None
        assert client.sms_trunks().update(trunk).data.id == HTTP_IN_ID

    def test_outgoing_dids_none_clears_the_list(self):
        trunk = SmsTrunk.build(HTTP_IN_ID)
        trunk.outgoing_dids = None
        assert trunk.to_jsonapi(include_id=True, dirty_only=True)["relationships"] == {
            "outgoing_dids": {"data": []},
        }

    def test_outgoing_dids_rejects_a_single_resource(self):
        trunk = SmsTrunk.build(HTTP_IN_ID)
        with pytest.raises(TypeError):
            trunk.outgoing_dids = Did.build(DID_ID)

    @my_vcr.use_cassette("sms_trunks/update_name_with_included_relationships.yaml")
    def test_included_relationships_are_not_sent_back(self, client):
        params = QueryParams().include("incoming_dids", "sms_trunk_group")
        trunk = client.sms_trunks().find(HTTP_IN_ID, params).data
        assert [d.id for d in trunk.incoming_dids] == [DID_ID]
        assert trunk.sms_trunk_group.id == GROUP_ID
        trunk.name = "Webhook"
        assert client.sms_trunks().update(trunk).data.name == "Webhook"

    def test_read_only_relationships_cannot_be_assigned(self):
        trunk = SmsTrunk.build(HTTP_IN_ID)
        with pytest.raises(AttributeError):
            trunk.incoming_dids = [Did.build(DID_ID)]
        with pytest.raises(AttributeError):
            trunk.sender_id_verifications = []
        assert trunk.to_jsonapi(include_id=True, dirty_only=True) == {
            "id": HTTP_IN_ID,
            "type": "sms_trunks",
            "attributes": {},
        }

    def test_create_from_a_loaded_trunk_drops_read_only_relationships(self):
        trunk = SmsTrunk.from_jsonapi({
            "id": HTTP_IN_ID,
            "type": "sms_trunks",
            "attributes": {"name": "copy"},
            "relationships": {
                "sms_trunk_group": {"data": {"type": "sms_trunk_groups", "id": GROUP_ID}},
                "incoming_dids": {"data": [{"type": "dids", "id": DID_ID}]},
                "sender_id_verifications": {"data": []},
            },
        })
        assert trunk.to_jsonapi()["relationships"] == {
            "sms_trunk_group": {"data": {"type": "sms_trunk_groups", "id": GROUP_ID}},
        }

    @my_vcr.use_cassette("sms_trunks/delete.yaml")
    def test_delete(self, client):
        assert client.sms_trunks().delete(HTTP_IN_ID) is None

    @my_vcr.use_cassette("sms_trunks/delete_error.yaml")
    def test_delete_error(self, client):
        with pytest.raises(DidwwApiError) as exc_info:
            client.sms_trunks().delete(HTTP_IN_ID)
        assert exc_info.value.status_code == 422


class TestSmsTrunkAllowAnyDidAsSource:
    @my_vcr.use_cassette("sms_trunks/update_allow_any_did_as_source_clears_outgoing_dids.yaml")
    def test_clears_loaded_outgoing_dids(self, client):
        trunk = client.sms_trunks().find(HTTP_OUT_ID, QueryParams().include("outgoing_dids")).data
        assert [d.id for d in trunk.outgoing_dids] == [DID_ID]
        trunk.allow_any_did_as_source = True
        assert trunk.outgoing_dids == []
        updated = client.sms_trunks().update(trunk).data
        assert updated.allow_any_did_as_source is True

    @my_vcr.use_cassette("sms_trunks/update_allow_any_did_as_source_links_only.yaml")
    def test_does_not_clear_outgoing_dids_that_were_not_loaded(self, client):
        trunk = client.sms_trunks().find(HTTP_OUT_ID).data
        trunk.allow_any_did_as_source = True
        assert "relationships" not in trunk.to_jsonapi(include_id=True, dirty_only=True)
        assert client.sms_trunks().update(trunk).data.allow_any_did_as_source is True

    @my_vcr.use_cassette("sms_trunks/update_name_with_flag_loaded.yaml")
    def test_loaded_flag_does_not_send_outgoing_dids(self, client):
        trunk = client.sms_trunks().find(HTTP_OUT_ID).data
        assert trunk.allow_any_did_as_source is True
        trunk.name = "Outbound API"
        assert client.sms_trunks().update(trunk).data.name == "Outbound API"

    def test_clears_assigned_outgoing_dids(self):
        trunk = SmsTrunk.build(HTTP_OUT_ID)
        trunk.outgoing_dids = [Did.build(DID_ID)]
        trunk.allow_any_did_as_source = True
        assert trunk.to_jsonapi(include_id=True, dirty_only=True) == {
            "id": HTTP_OUT_ID,
            "type": "sms_trunks",
            "attributes": {"allow_any_did_as_source": True},
            "relationships": {"outgoing_dids": {"data": []}},
        }

    def test_built_trunk_sends_only_the_flag(self):
        trunk = SmsTrunk.build(HTTP_OUT_ID)
        trunk.allow_any_did_as_source = True
        assert trunk.to_jsonapi(include_id=True, dirty_only=True) == {
            "id": HTTP_OUT_ID,
            "type": "sms_trunks",
            "attributes": {"allow_any_did_as_source": True},
        }

    def test_false_keeps_outgoing_dids(self):
        trunk = SmsTrunk.build(HTTP_OUT_ID)
        trunk.outgoing_dids = [Did.build(DID_ID)]
        trunk.allow_any_did_as_source = False
        assert trunk.to_jsonapi(include_id=True, dirty_only=True)["relationships"] == {
            "outgoing_dids": {"data": [{"type": "dids", "id": DID_ID}]},
        }
