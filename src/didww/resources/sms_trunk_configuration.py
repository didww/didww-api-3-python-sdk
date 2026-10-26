import copy

from didww.enums import SmsBodyType, SmsHttpMethod, SmsServerLocation, enum_value, to_enum
from didww.mixins import RedactsSensitiveAttributes


def _plain(key):
    return property(lambda self: self._attr(key), lambda self, v: self._set_attr(key, v))


def _read_only(key):
    return property(lambda self: self._attr(key))


def _enum(key, cls):
    return property(
        lambda self: to_enum(cls, self._attr(key)),
        lambda self, v: self._set_attr(key, enum_value(v)),
    )


class SmsTrunkConfiguration(RedactsSensitiveAttributes):
    """Configuration of an SMS trunk, dispatched on its ``type``.

    A configuration is a value: after reading ``trunk.configuration``, edit
    it and assign it back to the trunk. Attributes set to ``None`` are sent
    as null (the API clears them); attributes never set are left out and
    keep their stored values on update. Read-only attributes (generated
    credentials) are readable but never sent.
    """

    _type = None
    _type_map = {}
    _read_only_attrs = frozenset()

    def __init__(self, attributes=None):
        self._attributes = dict(attributes or {})

    @property
    def type(self):
        return self._type

    def _attr(self, key):
        return self._attributes.get(key)

    def _set_attr(self, key, value):
        self._attributes[key] = value

    @classmethod
    def _keys(cls, name):
        """Union of the ``name`` key sets over the class hierarchy, so a subclass cannot drop a parent's keys."""
        return frozenset().union(*(vars(c).get(name, ()) for c in cls.__mro__))

    def _masked(self, key, value):
        return value is not None and key in type(self)._keys("_sensitive_attrs")

    def to_jsonapi(self):
        read_only = type(self)._keys("_read_only_attrs")
        return {
            "type": self.type,
            "attributes": {k: copy.deepcopy(v) for k, v in self._attributes.items() if k not in read_only},
        }

    def __repr__(self):
        parts = [f"type={self.type!r}"]
        for key, value in self._attributes.items():
            parts.append(f"{key}={'[FILTERED]' if self._masked(key, value) else repr(value)}")
        return f"{type(self).__name__}({', '.join(parts)})"

    @classmethod
    def from_jsonapi(cls, data):
        """Builds the configuration class registered for ``data["type"]``;
        an unknown type gives a ``GenericSmsTrunkConfiguration``."""
        if not isinstance(data, dict):
            return data
        type_name = data.get("type")
        attributes = copy.deepcopy(dict(data.get("attributes") or {}))
        config_cls = SmsTrunkConfiguration._type_map.get(type_name)
        if config_cls is None:
            return GenericSmsTrunkConfiguration(type_name, attributes)
        return config_cls(attributes)


class SmsToEmailConfiguration(SmsTrunkConfiguration):
    """Delivers inbound messages by email. ``send_to``, ``subject`` and ``message`` are required on create."""

    _type = "sms_to_email"

    send_to = _plain("send_to")
    subject = _plain("subject")
    message = _plain("message")


class HttpInConfiguration(SmsTrunkConfiguration):
    """Delivers inbound messages to an HTTP endpoint.

    ``url`` and ``http_method`` are required on create; ``body_type`` and
    ``body`` are required when ``http_method`` is POST or PUT and refused
    when it is GET. ``body`` is a JSON string for ``SmsBodyType.JSON``, a
    dict for the form encodings and a string for ``SmsBodyType.RAW``.
    ``headers`` values are masked in ``repr()``.
    """

    _type = "http_in"
    _sensitive_attrs = frozenset({"headers"})

    url = _plain("url")
    http_method = _enum("http_method", SmsHttpMethod)
    query_parameters = _plain("query_parameters")
    headers = _plain("headers")
    body_type = _enum("body_type", SmsBodyType)
    body = _plain("body")
    follow_redirect = _plain("follow_redirect")
    validate_https_certificate = _plain("validate_https_certificate")


class HttpOutConfiguration(SmsTrunkConfiguration):
    """Accepts outbound messages over HTTP; ``auth_name`` and ``auth_password`` are generated and read-only."""

    _type = "http_out"
    _read_only_attrs = frozenset({"auth_name", "auth_password"})
    _sensitive_attrs = frozenset({"auth_name", "auth_password"})

    callback_url = _plain("callback_url")
    allowed_ips = _plain("allowed_ips")
    auth_name = _read_only("auth_name")
    auth_password = _read_only("auth_password")


class SmppEsmeConfiguration(SmsTrunkConfiguration):
    """Accepts an SMPP bind from the customer's ESME; ``system_id`` and ``password`` are generated and read-only.

    ``server_location`` (SmsServerLocation) is required on create.
    """

    _type = "smpp_esme"
    _read_only_attrs = frozenset({"system_id", "password"})
    _sensitive_attrs = frozenset({"system_id", "password"})

    system_type = _plain("system_type")
    allowed_ips = _plain("allowed_ips")
    server_location = _enum("server_location", SmsServerLocation)
    system_id = _read_only("system_id")
    password = _read_only("password")


class SmppSmscConfiguration(SmsTrunkConfiguration):
    """DIDWW binds to the customer's SMSC; ``password`` is masked in ``repr()``.

    ``host``, ``system_id``, ``password`` and ``server_location`` (SmsServerLocation)
    are required on create; ``tx_port`` and ``rx_port`` default to 2775 and 2776.
    """

    _type = "smpp_smsc"
    _sensitive_attrs = frozenset({"password"})

    host = _plain("host")
    tx_port = _plain("tx_port")
    rx_port = _plain("rx_port")
    transceiver_mode = _plain("transceiver_mode")
    connection_timeout = _plain("connection_timeout")
    use_ssl = _plain("use_ssl")
    system_id = _plain("system_id")
    system_type = _plain("system_type")
    password = _plain("password")
    server_location = _enum("server_location", SmsServerLocation)


class GenericSmsTrunkConfiguration(SmsTrunkConfiguration):
    """A configuration of a type this SDK version does not know.

    ``attributes`` is the live dict that is sent. Every non-None value is
    masked in ``repr()``.
    """

    def __init__(self, type_name, attributes=None):
        super().__init__(attributes)
        self._type_name = type_name

    @property
    def type(self):
        return self._type_name

    @property
    def attributes(self):
        return self._attributes

    def _masked(self, key, value):
        return value is not None


SmsTrunkConfiguration._type_map.update({
    c._type: c for c in (
        SmsToEmailConfiguration,
        HttpInConfiguration,
        HttpOutConfiguration,
        SmppEsmeConfiguration,
        SmppSmscConfiguration,
    )
})
