import json
from decimal import Decimal

import pytest

from didww import _json
from didww.enums import SmsBodyType, SmsHttpMethod, SmsServerLocation
from didww.resources.sms_trunk import SmsTrunk
from didww.resources.sms_trunk_configuration import (
    GenericSmsTrunkConfiguration,
    HttpInConfiguration,
    HttpOutConfiguration,
    SmppEsmeConfiguration,
    SmppSmscConfiguration,
    SmsToEmailConfiguration,
    SmsTrunkConfiguration,
)

SECRET = "s3cret-value"  # NOSONAR python:S2068 -- test fixture


class TestDispatch:
    @pytest.mark.parametrize("type_name, config_cls", [
        ("sms_to_email", SmsToEmailConfiguration),
        ("http_in", HttpInConfiguration),
        ("http_out", HttpOutConfiguration),
        ("smpp_esme", SmppEsmeConfiguration),
        ("smpp_smsc", SmppSmscConfiguration),
    ])
    def test_known_types(self, type_name, config_cls):
        config = SmsTrunkConfiguration.from_jsonapi({"type": type_name, "attributes": {}})
        assert type(config) is config_cls
        assert config.type == type_name
        assert config.to_jsonapi() == {"type": type_name, "attributes": {}}

    def test_unknown_type_is_generic(self):
        config = SmsTrunkConfiguration.from_jsonapi({"type": "future_transport", "attributes": {"retries": 3}})
        assert type(config) is GenericSmsTrunkConfiguration
        assert config.type == "future_transport"
        assert config.attributes == {"retries": 3}
        config.attributes["retries"] = 4
        assert config.to_jsonapi() == {"type": "future_transport", "attributes": {"retries": 4}}

    def test_non_dict_passes_through(self):
        assert SmsTrunkConfiguration.from_jsonapi(None) is None
        trunk = SmsTrunk.build("t1")
        trunk.configuration = None
        assert trunk.configuration is None
        assert trunk.to_jsonapi(include_id=True, dirty_only=True)["attributes"] == {"configuration": None}

    def test_from_jsonapi_copies_the_attributes(self):
        raw = {"type": "http_in", "attributes": {"headers": {"X-A": "1"}}}
        config = SmsTrunkConfiguration.from_jsonapi(raw)
        config.headers["X-A"] = "2"
        assert raw["attributes"]["headers"] == {"X-A": "1"}

    def test_assignment_takes_a_snapshot(self):
        config = HttpInConfiguration()
        config.url = "https://example.com/sms"
        config.headers = {"X-Token": "old"}
        config.body = {"fields": ["text"]}
        trunk = SmsTrunk.build("t")
        trunk.configuration = config
        config.url = "https://example.com/other"
        config.headers["X-Token"] = "new"
        config.body["fields"].append("from")
        sent = trunk.to_jsonapi(include_id=True, dirty_only=True)["attributes"]["configuration"]["attributes"]
        assert sent == {"url": "https://example.com/sms", "headers": {"X-Token": "old"}, "body": {"fields": ["text"]}}

    def test_to_jsonapi_returns_a_copy(self):
        config = HttpInConfiguration()
        config.headers = {"X-Token": "old"}
        config.to_jsonapi()["attributes"]["headers"]["X-Token"] = "new"
        assert config.headers == {"X-Token": "old"}


class TestTypedAttributes:
    def test_http_in_enums(self):
        config = HttpInConfiguration()
        config.http_method = SmsHttpMethod.PUT
        config.body_type = SmsBodyType.HTML_URL_ENCODED
        config.body = {"text": "{SMS_TEXT}"}
        assert config.to_jsonapi()["attributes"] == {
            "http_method": "put",
            "body_type": "html_url_encoded",
            "body": {"text": "{SMS_TEXT}"},
        }
        assert config.http_method == SmsHttpMethod.PUT
        assert config.body_type == SmsBodyType.HTML_URL_ENCODED

    def test_unknown_enum_value_reads_as_raw_string(self):
        config = HttpInConfiguration({"http_method": "patch", "body_type": "xml"})
        assert config.http_method == "patch"
        assert config.body_type == "xml"

    def test_explicit_none_is_sent_and_unset_is_left_out(self):
        config = HttpOutConfiguration()
        config.callback_url = None
        config.allowed_ips = None
        assert config.to_jsonapi() == {"type": "http_out", "attributes": {"callback_url": None, "allowed_ips": None}}
        esme = SmppEsmeConfiguration()
        esme.system_type = None
        assert esme.to_jsonapi() == {"type": "smpp_esme", "attributes": {"system_type": None}}

    def test_smpp_server_location(self):
        esme = SmppEsmeConfiguration()
        esme.server_location = SmsServerLocation.AMS
        smsc = SmppSmscConfiguration()
        smsc.server_location = SmsServerLocation.NYC
        assert esme.to_jsonapi()["attributes"] == {"server_location": "ams"}
        assert smsc.to_jsonapi()["attributes"] == {"server_location": "nyc"}
        assert esme.server_location == SmsServerLocation.AMS

    def test_smpp_smsc_credentials_are_writable(self):
        smsc = SmppSmscConfiguration()
        smsc.system_id = "didww"
        smsc.password = SECRET
        assert smsc.to_jsonapi()["attributes"] == {"system_id": "didww", "password": SECRET}

    @pytest.mark.parametrize("config_cls, keys", [
        (HttpOutConfiguration, ("auth_name", "auth_password")),
        (SmppEsmeConfiguration, ("system_id", "password")),
    ])
    def test_generated_credentials_are_read_only(self, config_cls, keys):
        config = config_cls({k: SECRET for k in keys})
        for key in keys:
            assert getattr(config, key) == SECRET
            with pytest.raises(AttributeError):
                setattr(config, key, "other")
        assert config.to_jsonapi()["attributes"] == {}


class TestSubclasses:
    def test_subclass_cannot_drop_read_only_or_sensitive_keys(self):
        class MyHttpOut(HttpOutConfiguration):
            _read_only_attrs = frozenset()
            _sensitive_attrs = frozenset()

        config = MyHttpOut({"callback_url": "https://example.com/cb", "auth_name": SECRET, "auth_password": SECRET})
        assert config.to_jsonapi() == {"type": "http_out", "attributes": {"callback_url": "https://example.com/cb"}}
        assert SECRET not in repr(config)

    def test_subclass_assigned_to_trunk_is_stripped(self):
        class MyEsme(SmppEsmeConfiguration):
            _read_only_attrs = frozenset({"extra"})

        config = MyEsme({"password": SECRET, "extra": 1, "allowed_ips": ["203.0.113.10"]})
        assert config.to_jsonapi()["attributes"] == {"allowed_ips": ["203.0.113.10"]}
        trunk = SmsTrunk.build("t1")
        trunk.configuration = config
        assert trunk.to_jsonapi(include_id=True, dirty_only=True)["attributes"]["configuration"] == {
            "type": "smpp_esme",
            "attributes": {"allowed_ips": ["203.0.113.10"]},
        }

    def test_generic_with_a_known_type_is_stripped_on_the_trunk(self):
        trunk = SmsTrunk.build("t1")
        trunk.configuration = GenericSmsTrunkConfiguration("http_out", {"auth_password": SECRET, "callback_url": None})
        assert trunk.to_jsonapi(include_id=True, dirty_only=True)["attributes"]["configuration"] == {
            "type": "http_out",
            "attributes": {"callback_url": None},
        }


class TestRepr:
    @pytest.mark.parametrize("config_cls, attributes, hidden", [
        (HttpInConfiguration, {"url": "https://example.com/sms", "headers": {"Authorization": SECRET}}, ("headers",)),
        (HttpOutConfiguration, {"callback_url": "https://example.com/cb", "auth_name": SECRET, "auth_password": SECRET},
         ("auth_name", "auth_password")),
        (SmppEsmeConfiguration, {"allowed_ips": ["203.0.113.10"], "system_id": SECRET, "password": SECRET},
         ("system_id", "password")),
        (SmppSmscConfiguration, {"host": "smsc.example.com", "system_id": "didww", "password": SECRET}, ("password",)),
    ])
    def test_sensitive_values_are_masked(self, config_cls, attributes, hidden):
        config = config_cls(attributes)
        for text in (repr(config), str(config)):
            assert SECRET not in text
            for key in hidden:
                assert f"{key}=[FILTERED]" in text
        visible = [k for k in attributes if k not in hidden]
        for key in visible:
            assert repr(attributes[key]) in repr(config)
        assert config.to_jsonapi()["attributes"] == {
            k: v for k, v in attributes.items() if k not in config_cls._read_only_attrs
        }

    def test_none_is_not_masked(self):
        assert "auth_password=None" in repr(HttpOutConfiguration({"auth_password": None}))

    def test_generic_masks_every_value(self):
        config = GenericSmsTrunkConfiguration("future_transport", {"token": SECRET, "port": 2775, "cleared": None})
        text = repr(config)
        assert SECRET not in text
        assert "2775" not in text
        assert "token=[FILTERED]" in text
        assert "port=[FILTERED]" in text
        assert "cleared=None" in text
        assert "future_transport" in text
        assert config.to_jsonapi()["attributes"]["token"] == SECRET


class TestExactNumbers:
    def test_round_trip_keeps_decimal_and_large_integers(self):
        text = (
            '{"id":"t1","type":"sms_trunks","attributes":{"configuration":{"type":"future_transport",'
            '"attributes":{"ratio":1.10,"sequence":9007199254740993,'
            '"nested":{"ids":[123456789012345678901234567890],"cleared":null}}}}}'
        )
        trunk = SmsTrunk.from_jsonapi(_json.loads(text))
        config = trunk.configuration
        assert config.attributes["ratio"] == Decimal("1.10")
        assert str(config.attributes["ratio"]) == "1.10"
        trunk.configuration = config
        body = _json.dumps({"data": trunk.to_jsonapi(include_id=True, dirty_only=True)}).decode("utf-8")
        assert '"ratio":1.10' in body
        assert '"sequence":9007199254740993' in body
        assert '"ids":[123456789012345678901234567890]' in body
        assert '"cleared":null' in body
        sent = json.loads(body, parse_float=Decimal)["data"]["attributes"]["configuration"]["attributes"]
        assert sent["ratio"] == Decimal("1.10")
        assert sent["sequence"] == 9007199254740993
