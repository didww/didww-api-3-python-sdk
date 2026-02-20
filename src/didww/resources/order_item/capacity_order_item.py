from didww.resources.order_item.base import OrderItem


class CapacityOrderItem(OrderItem):
    _type = "capacity_order_items"

    @property
    def capacity_pool_id(self):
        return self._attr("capacity_pool_id")

    @capacity_pool_id.setter
    def capacity_pool_id(self, value):
        self._set_attr("capacity_pool_id", value)

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


OrderItem.register("capacity_order_items", CapacityOrderItem)
