from didww.resources.base import BaseResource, Repository
from didww.resources.order_item.base import OrderItem

# Import to register types
import didww.resources.order_item.did_order_item  # noqa: F401
import didww.resources.order_item.capacity_order_item  # noqa: F401
import didww.resources.order_item.available_did_order_item  # noqa: F401
import didww.resources.order_item.reservation_did_order_item  # noqa: F401
import didww.resources.order_item.generic_order_item  # noqa: F401


class Order(BaseResource):
    _type = "orders"
    _writable_attrs = {"allow_back_ordering", "items", "callback_url", "callback_method"}

    @property
    def amount(self):
        return self._attr("amount")

    @property
    def status(self):
        return self._attr("status")

    @property
    def created_at(self):
        return self._attr("created_at")

    @property
    def description(self):
        return self._attr("description")

    @property
    def reference(self):
        return self._attr("reference")

    @property
    def callback_url(self):
        return self._attr("callback_url")

    @callback_url.setter
    def callback_url(self, value):
        self._set_attr("callback_url", value)

    @property
    def callback_method(self):
        return self._attr("callback_method")

    @callback_method.setter
    def callback_method(self, value):
        self._set_attr("callback_method", value)

    @property
    def allow_back_ordering(self):
        return self._attr("allow_back_ordering")

    @allow_back_ordering.setter
    def allow_back_ordering(self, value):
        self._set_attr("allow_back_ordering", value)

    @property
    def items(self):
        raw_items = self._attr("items")
        if raw_items is None:
            return []
        return [
            OrderItem.from_jsonapi(item) if isinstance(item, dict) else item
            for item in raw_items
        ]

    @items.setter
    def items(self, value):
        serialized = []
        for item in value:
            if isinstance(item, OrderItem):
                serialized.append(item.to_jsonapi())
            else:
                serialized.append(item)
        self._set_attr("items", serialized)


class OrderRepository(Repository):
    _resource_class = Order
    _path = "orders"
