from didww.resources.order_item.base import OrderItem


class AvailableDidOrderItem(OrderItem):
    _type = "did_order_items"

    @property
    def sku_id(self):
        return self._attr("sku_id")

    @sku_id.setter
    def sku_id(self, value):
        self._set_attr("sku_id", value)

    @property
    def available_did_id(self):
        return self._attr("available_did_id")

    @available_did_id.setter
    def available_did_id(self, value):
        self._set_attr("available_did_id", value)


OrderItem.register("available_did_order_items", AvailableDidOrderItem)
