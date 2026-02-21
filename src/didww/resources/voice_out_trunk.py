from didww.resources.base import BaseResource, Repository


class VoiceOutTrunk(BaseResource):
    _type = "voice_out_trunks"
    _writable_attrs = {"name", "allowed_sip_ips", "on_cli_mismatch_action", "allowed_rtp_ips",
                       "allow_any_did_as_cli", "status", "capacity_limit", "threshold_amount",
                       "media_encryption_mode", "default_dst_action", "dst_prefixes",
                       "force_symmetric_rtp", "rtp_ping", "callback_url"}

    @property
    def name(self):
        return self._attr("name")

    @name.setter
    def name(self, value):
        self._set_attr("name", value)

    @property
    def allowed_sip_ips(self):
        return self._attr("allowed_sip_ips")

    @allowed_sip_ips.setter
    def allowed_sip_ips(self, value):
        self._set_attr("allowed_sip_ips", value)

    @property
    def on_cli_mismatch_action(self):
        return self._attr("on_cli_mismatch_action")

    @on_cli_mismatch_action.setter
    def on_cli_mismatch_action(self, value):
        self._set_attr("on_cli_mismatch_action", value)

    @property
    def allowed_rtp_ips(self):
        return self._attr("allowed_rtp_ips")

    @allowed_rtp_ips.setter
    def allowed_rtp_ips(self, value):
        self._set_attr("allowed_rtp_ips", value)

    @property
    def allow_any_did_as_cli(self):
        return self._attr("allow_any_did_as_cli")

    @allow_any_did_as_cli.setter
    def allow_any_did_as_cli(self, value):
        self._set_attr("allow_any_did_as_cli", value)

    @property
    def status(self):
        return self._attr("status")

    @status.setter
    def status(self, value):
        self._set_attr("status", value)

    @property
    def capacity_limit(self):
        return self._attr("capacity_limit")

    @capacity_limit.setter
    def capacity_limit(self, value):
        self._set_attr("capacity_limit", value)

    @property
    def threshold_amount(self):
        return self._attr("threshold_amount")

    @threshold_amount.setter
    def threshold_amount(self, value):
        self._set_attr("threshold_amount", value)

    @property
    def threshold_reached(self):
        return self._attr("threshold_reached")

    @property
    def media_encryption_mode(self):
        return self._attr("media_encryption_mode")

    @media_encryption_mode.setter
    def media_encryption_mode(self, value):
        self._set_attr("media_encryption_mode", value)

    @property
    def default_dst_action(self):
        return self._attr("default_dst_action")

    @default_dst_action.setter
    def default_dst_action(self, value):
        self._set_attr("default_dst_action", value)

    @property
    def dst_prefixes(self):
        return self._attr("dst_prefixes")

    @dst_prefixes.setter
    def dst_prefixes(self, value):
        self._set_attr("dst_prefixes", value)

    @property
    def force_symmetric_rtp(self):
        return self._attr("force_symmetric_rtp")

    @force_symmetric_rtp.setter
    def force_symmetric_rtp(self, value):
        self._set_attr("force_symmetric_rtp", value)

    @property
    def rtp_ping(self):
        return self._attr("rtp_ping")

    @rtp_ping.setter
    def rtp_ping(self, value):
        self._set_attr("rtp_ping", value)

    @property
    def callback_url(self):
        return self._attr("callback_url")

    @callback_url.setter
    def callback_url(self, value):
        self._set_attr("callback_url", value)

    @property
    def username(self):
        return self._attr("username")

    @property
    def password(self):
        return self._attr("password")

    @property
    def created_at(self):
        return self._attr("created_at")

    def set_default_did(self, did_id):
        self._set_relationship("default_did", "dids", did_id)

    def set_dids(self, did_ids):
        self._relationships["dids"] = {
            "data": [{"type": "dids", "id": did_id} for did_id in did_ids]
        }


class VoiceOutTrunkRepository(Repository):
    _resource_class = VoiceOutTrunk
    _path = "voice_out_trunks"
