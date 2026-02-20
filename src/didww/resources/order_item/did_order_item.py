from didww.resources.order_item.base import OrderItem


class DidOrderItem(OrderItem):
    _type = "did_order_items"

    @property
    def sku_id(self):
        return self._attr("sku_id")

    @sku_id.setter
    def sku_id(self, value):
        self._set_attr("sku_id", value)

    @property
    def qty(self):
        return self._attr("qty")

    @qty.setter
    def qty(self, value):
        self._set_attr("qty", value)

    @property
    def nrc(self):
        return self._attr("nrc")

    @property
    def mrc(self):
        return self._attr("mrc")

    @property
    def prorated_mrc(self):
        return self._attr("prorated_mrc")

    @property
    def billing_cycles_count(self):
        return self._attr("billing_cycles_count")

    @billing_cycles_count.setter
    def billing_cycles_count(self, value):
        self._set_attr("billing_cycles_count", value)

    @property
    def nanpa_prefix_id(self):
        return self._attr("nanpa_prefix_id")

    @nanpa_prefix_id.setter
    def nanpa_prefix_id(self, value):
        self._set_attr("nanpa_prefix_id", value)

    @property
    def available_did_id(self):
        return self._attr("available_did_id")

    @available_did_id.setter
    def available_did_id(self, value):
        self._set_attr("available_did_id", value)

    @property
    def did_reservation_id(self):
        return self._attr("did_reservation_id")

    @did_reservation_id.setter
    def did_reservation_id(self, value):
        self._set_attr("did_reservation_id", value)

    @property
    def did_group_id(self):
        return self._attr("did_group_id")


OrderItem.register("did_order_items", DidOrderItem)
