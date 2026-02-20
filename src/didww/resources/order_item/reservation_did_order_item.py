from didww.resources.order_item.base import OrderItem


class ReservationDidOrderItem(OrderItem):
    _type = "did_order_items"

    @property
    def sku_id(self):
        return self._attr("sku_id")

    @sku_id.setter
    def sku_id(self, value):
        self._set_attr("sku_id", value)

    @property
    def did_reservation_id(self):
        return self._attr("did_reservation_id")

    @did_reservation_id.setter
    def did_reservation_id(self, value):
        self._set_attr("did_reservation_id", value)


OrderItem.register("reservation_did_order_items", ReservationDidOrderItem)
