from didww.resources.order_item.base import OrderItem


class GenericOrderItem(OrderItem):
    _type = "generic_order_items"


OrderItem.register("generic_order_items", GenericOrderItem)
