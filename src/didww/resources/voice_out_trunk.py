from didww.enums import (
    DefaultDstAction,
    IceMode,
    MediaEncryptionMode,
    OnCliMismatchAction,
    RtcpFeedbackMode,
    RtcpMuxMode,
    VoiceOutCodec,
    VoiceOutTrunkStatus,
)
from didww.resources.base import (
    DatetimeAttributeField,
    DidwwApiModel,
    EnumAttributeField,
    EnumListAttributeField,
    RelationField,
    Repository,
    SafeAttributeField,
)
from didww.resources.authentication_method import AuthenticationMethod


class VoiceOutTrunk(DidwwApiModel):
    """Voice OUT trunk resource.

    ``codecs`` lists ``VoiceOutCodec`` names in priority order, the first
    with the highest priority; a change to the list read, such as
    ``trunk.codecs.insert(0, VoiceOutCodec.OPUS)``, is sent on update.
    ``ice_mode``, ``rtcp_mux_mode`` and
    ``rtcp_feedback_mode`` take ``disabled``, ``accept`` or ``initiate``.
    """

    _writable_attrs = {
        "name", "on_cli_mismatch_action",
        "allow_any_did_as_cli", "status", "capacity_limit", "threshold_amount",
        "media_encryption_mode", "default_dst_action", "dst_prefixes",
        "force_symmetric_rtp", "rtp_ping", "callback_url",
        "authentication_method", "allowed_rtp_ips", "external_reference_id",
        "emergency_enable_all", "rtp_timeout",
        "codecs", "ice_mode", "rtcp_mux_mode", "rtcp_feedback_mode",
    }

    name = SafeAttributeField("name")
    on_cli_mismatch_action = EnumAttributeField("on_cli_mismatch_action", OnCliMismatchAction)
    allowed_rtp_ips = SafeAttributeField("allowed_rtp_ips")
    allow_any_did_as_cli = SafeAttributeField("allow_any_did_as_cli")
    status = EnumAttributeField("status", VoiceOutTrunkStatus)
    capacity_limit = SafeAttributeField("capacity_limit")
    threshold_amount = SafeAttributeField("threshold_amount")
    threshold_reached = SafeAttributeField("threshold_reached")
    media_encryption_mode = EnumAttributeField("media_encryption_mode", MediaEncryptionMode)
    default_dst_action = EnumAttributeField("default_dst_action", DefaultDstAction)
    dst_prefixes = SafeAttributeField("dst_prefixes")
    force_symmetric_rtp = SafeAttributeField("force_symmetric_rtp")
    rtp_ping = SafeAttributeField("rtp_ping")
    callback_url = SafeAttributeField("callback_url")
    created_at = DatetimeAttributeField("created_at")
    external_reference_id = SafeAttributeField("external_reference_id")
    emergency_enable_all = SafeAttributeField("emergency_enable_all")
    rtp_timeout = SafeAttributeField("rtp_timeout")
    codecs = EnumListAttributeField("codecs", VoiceOutCodec)
    ice_mode = EnumAttributeField("ice_mode", IceMode)
    rtcp_mux_mode = EnumAttributeField("rtcp_mux_mode", RtcpMuxMode)
    rtcp_feedback_mode = EnumAttributeField("rtcp_feedback_mode", RtcpFeedbackMode)

    default_did = RelationField("default_did")
    dids = RelationField("dids")
    emergency_dids = RelationField("emergency_dids")

    class Meta:
        type = "voice_out_trunks"

    @property
    def is_active(self):
        return self.status == VoiceOutTrunkStatus.ACTIVE

    @property
    def is_blocked(self):
        return self.status == VoiceOutTrunkStatus.BLOCKED

    @property
    def authentication_method(self):
        data = self.attributes.get("authentication_method")
        if data and isinstance(data, dict):
            return AuthenticationMethod.from_jsonapi(data)
        return data

    @authentication_method.setter
    def authentication_method(self, value):
        if isinstance(value, AuthenticationMethod):
            self.attributes["authentication_method"] = value.to_jsonapi()
        else:
            self.attributes["authentication_method"] = value


class VoiceOutTrunkRepository(Repository):
    _resource_class = VoiceOutTrunk
    _path = "voice_out_trunks"
