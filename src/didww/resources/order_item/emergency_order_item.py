from didww.resources.order_item.base import OrderItem


class EmergencyOrderItem(OrderItem):
    _type = "emergency_order_items"

    @property
    def qty(self):
        return self._attr("qty")

    @qty.setter
    def qty(self, value):
        self._set_attr("qty", value)

    @property
    def emergency_calling_service_id(self):
        return self._attr("emergency_calling_service_id")

    @emergency_calling_service_id.setter
    def emergency_calling_service_id(self, value):
        self._set_attr("emergency_calling_service_id", value)

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
    def billed_from(self):
        return self._attr("billed_from")

    @property
    def billed_to(self):
        return self._attr("billed_to")


OrderItem.register("emergency_order_items", EmergencyOrderItem)
