from tests.conftest import my_vcr
from didww.enums import CallbackMethod, OrderStatus
from didww.resources.order import Order
from didww.resources.order_item.did_order_item import DidOrderItem
from didww.resources.order_item.capacity_order_item import CapacityOrderItem
from didww.resources.order_item.available_did_order_item import AvailableDidOrderItem
from didww.resources.order_item.reservation_did_order_item import ReservationDidOrderItem


class TestOrder:
    @my_vcr.use_cassette("orders/show.yaml")
    def test_find_order(self, client):
        response = client.orders().find("9df11dac-9d83-448c-8866-19c998be33db")
        order = response.data
        assert order.id == "9df11dac-9d83-448c-8866-19c998be33db"
        assert order.status == OrderStatus.COMPLETED
        assert order.description == "Payment processing fee"
        assert order.reference == "SPT-474057"
        assert len(order.items) > 0

    @my_vcr.use_cassette("orders/create.yaml")
    def test_create_order(self, client):
        item1 = DidOrderItem()
        item1.sku_id = "acc46374-0b34-4912-9f67-8340339db1e5"
        item1.qty = 2

        item2 = DidOrderItem()
        item2.sku_id = "f36d2812-2195-4385-85e8-e59c3484a8bc"
        item2.qty = 1

        order = Order()
        order.allow_back_ordering = True
        order.items = [item1, item2]

        response = client.orders().create(order)
        created = response.data
        assert created.id == "5da18706-be9f-49b0-aeec-0480aacd49ad"
        assert created.status == OrderStatus.PENDING
        assert created.description == "DID"
        assert len(created.items) == 2

    @my_vcr.use_cassette("orders/create_5.yaml")
    def test_order_billing_cycles_count(self, client):
        item = DidOrderItem()
        item.sku_id = "f36d2812-2195-4385-85e8-e59c3484a8bc"
        item.qty = 1
        item.billing_cycles_count = 5

        order = Order()
        order.allow_back_ordering = True
        order.items = [item]

        response = client.orders().create(order)
        created = response.data
        assert created.id == "9b9f2121-8d9e-4aa8-9754-dbaf6f695fd6"
        assert created.status == OrderStatus.PENDING
        assert len(created.items) == 1

    @my_vcr.use_cassette("orders/create_3.yaml")
    def test_order_available_did(self, client):
        item = AvailableDidOrderItem()
        item.sku_id = "acc46374-0b34-4912-9f67-8340339db1e5"
        item.available_did_id = "c43441e3-82d4-4d84-93e2-80998576c1ce"

        order = Order()
        order.items = [item]

        response = client.orders().create(order)
        created = response.data
        assert created.id == "9b9f2121-8d9e-4aa8-9754-dbaf6f695fd6"
        assert created.status == OrderStatus.PENDING
        assert len(created.items) == 1

    @my_vcr.use_cassette("orders/create_1.yaml")
    def test_order_reservation(self, client):
        item = ReservationDidOrderItem()
        item.sku_id = "32840f64-5c3f-4278-8c8d-887fbe2f03f4"
        item.did_reservation_id = "e3ed9f97-1058-430c-9134-38f1c614ee9f"

        order = Order()
        order.items = [item]

        response = client.orders().create(order)
        created = response.data
        assert created.id == "a9a7ff2d-d634-4545-bf28-dfda92d1c723"
        assert created.status == OrderStatus.PENDING
        assert len(created.items) == 1

    @my_vcr.use_cassette("orders/create_2.yaml")
    def test_order_capacity(self, client):
        item = CapacityOrderItem()
        item.capacity_pool_id = "b7522a31-4bf3-4c23-81e8-e7a14b23663f"
        item.qty = 1

        order = Order()
        order.items = [item]

        response = client.orders().create(order)
        created = response.data
        assert created.id == "68a46dd5-d405-4283-b7a5-62503267e9f8"
        assert created.status == OrderStatus.COMPLETED
        assert created.description == "Capacity"
        assert len(created.items) == 1

    @my_vcr.use_cassette("orders/create_6.yaml")
    def test_order_nanpa_prefix(self, client):
        item = DidOrderItem()
        item.sku_id = "fe77889c-f05a-40ad-a845-96aca3c28054"
        item.nanpa_prefix_id = "eeed293b-f3d8-4ef8-91ef-1b077d174b3b"
        item.qty = 1

        order = Order()
        order.allow_back_ordering = True
        order.items = [item]

        response = client.orders().create(order)
        created = response.data
        assert created.id == "c617f0ff-f819-477f-a17b-a8d248c4443e"
        assert created.status == OrderStatus.PENDING
        assert len(created.items) == 1

    @my_vcr.use_cassette("orders_with_callback/create.yaml")
    def test_order_with_callback(self, client):
        item = DidOrderItem()
        item.sku_id = "f36d2812-2195-4385-85e8-e59c3484a8bc"
        item.qty = 1

        order = Order()
        order.allow_back_ordering = True
        order.callback_url = "https://example.com/callback"
        order.callback_method = CallbackMethod.POST
        order.items = [item]

        response = client.orders().create(order)
        created = response.data
        assert created.id == "5da18706-be9f-49b0-aeec-0480aacd49ad"
        assert created.status == OrderStatus.PENDING
        assert created.callback_url == "https://example.com/callback"
        assert created.callback_method == CallbackMethod.POST
        assert len(created.items) == 1
