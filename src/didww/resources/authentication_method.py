class AuthenticationMethod:
    """Base class for polymorphic VoiceOutTrunk authentication methods."""
    _type = None
    _type_map = {}

    def __init__(self, **kwargs):
        self._attributes = kwargs

    def _attr(self, key):
        return self._attributes.get(key)

    def _set_attr(self, key, value):
        self._attributes[key] = value

    def to_jsonapi(self):
        return {
            "type": self._type,
            "attributes": dict(self._attributes),
        }

    @classmethod
    def from_jsonapi(cls, data):
        if data is None:
            return None
        auth_type = data.get("type")
        auth_cls = cls._type_map.get(auth_type)
        if auth_cls is None:
            # Forward-compat: wrap unknown types in Generic
            return GenericAuthenticationMethod(
                type_name=auth_type,
                **(data.get("attributes") or {})
            )
        return auth_cls(**(data.get("attributes") or {}))

    @classmethod
    def register(cls, type_name, auth_class):
        cls._type_map[type_name] = auth_class


def _plain(key):
    return property(lambda self: self._attr(key), lambda self, v: self._set_attr(key, v))


class IpOnlyAuthenticationMethod(AuthenticationMethod):
    """Read-only authentication method for VoiceOutTrunk.

    ip_only authentication can only be configured manually by DIDWW staff
    upon request. It cannot be set via the API on create or update.
    Trunks with ip_only authentication can still be read and their
    non-authentication attributes updated via the API.
    """
    _type = "ip_only"

    allowed_sip_ips = _plain("allowed_sip_ips")
    tech_prefix = _plain("tech_prefix")


class CredentialsAndIpAuthenticationMethod(AuthenticationMethod):
    _type = "credentials_and_ip"

    allowed_sip_ips = _plain("allowed_sip_ips")
    tech_prefix = _plain("tech_prefix")
    username = _plain("username")
    password = _plain("password")


class TwilioAuthenticationMethod(AuthenticationMethod):
    _type = "twilio"

    twilio_account_sid = _plain("twilio_account_sid")


class GenericAuthenticationMethod(AuthenticationMethod):
    """Forward-compatible wrapper for unknown authentication_method types."""

    def __init__(self, type_name=None, **kwargs):
        super().__init__(**kwargs)
        self._type = type_name


AuthenticationMethod.register("ip_only", IpOnlyAuthenticationMethod)
AuthenticationMethod.register("credentials_and_ip", CredentialsAndIpAuthenticationMethod)
AuthenticationMethod.register("twilio", TwilioAuthenticationMethod)
