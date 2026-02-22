from didww.enums import CallbackMethod, OrderStatus
from didww.resources.base import DidwwApiModel, SafeAttributeField, EnumAttributeField, Repository
from didww.resources.order_item.base import OrderItem

# Import to register types
import didww.resources.order_item.did_order_item  # noqa: F401
import didww.resources.order_item.capacity_order_item  # noqa: F401
import didww.resources.order_item.available_did_order_item  # noqa: F401
import didww.resources.order_item.reservation_did_order_item  # noqa: F401
import didww.resources.order_item.generic_order_item  # noqa: F401


class Order(DidwwApiModel):
    _writable_attrs = {"allow_back_ordering", "items", "callback_url", "callback_method"}

    amount = SafeAttributeField("amount")
    status = EnumAttributeField("status", OrderStatus)
    created_at = SafeAttributeField("created_at")
    description = SafeAttributeField("description")
    reference = SafeAttributeField("reference")
    callback_url = SafeAttributeField("callback_url")
    callback_method = EnumAttributeField("callback_method", CallbackMethod)
    allow_back_ordering = SafeAttributeField("allow_back_ordering")

    class Meta:
        type = "orders"

    @property
    def items(self):
        raw_items = self.attributes.get("items")
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
        self.attributes["items"] = serialized


class OrderRepository(Repository):
    _resource_class = Order
    _path = "orders"
