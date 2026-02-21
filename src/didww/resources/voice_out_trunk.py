from didww.resources.base import DidwwApiModel, SafeAttributeField, RelationField, Repository


class VoiceOutTrunk(DidwwApiModel):
    _writable_attrs = {
        "name", "allowed_sip_ips", "on_cli_mismatch_action", "allowed_rtp_ips",
        "allow_any_did_as_cli", "status", "capacity_limit", "threshold_amount",
        "media_encryption_mode", "default_dst_action", "dst_prefixes",
        "force_symmetric_rtp", "rtp_ping", "callback_url",
    }

    name = SafeAttributeField("name")
    allowed_sip_ips = SafeAttributeField("allowed_sip_ips")
    on_cli_mismatch_action = SafeAttributeField("on_cli_mismatch_action")
    allowed_rtp_ips = SafeAttributeField("allowed_rtp_ips")
    allow_any_did_as_cli = SafeAttributeField("allow_any_did_as_cli")
    status = SafeAttributeField("status")
    capacity_limit = SafeAttributeField("capacity_limit")
    threshold_amount = SafeAttributeField("threshold_amount")
    threshold_reached = SafeAttributeField("threshold_reached")
    media_encryption_mode = SafeAttributeField("media_encryption_mode")
    default_dst_action = SafeAttributeField("default_dst_action")
    dst_prefixes = SafeAttributeField("dst_prefixes")
    force_symmetric_rtp = SafeAttributeField("force_symmetric_rtp")
    rtp_ping = SafeAttributeField("rtp_ping")
    callback_url = SafeAttributeField("callback_url")
    username = SafeAttributeField("username")
    password = SafeAttributeField("password")
    created_at = SafeAttributeField("created_at")

    default_did = RelationField("default_did")
    dids = RelationField("dids")

    class Meta:
        type = "voice_out_trunks"


class VoiceOutTrunkRepository(Repository):
    _resource_class = VoiceOutTrunk
    _path = "voice_out_trunks"
