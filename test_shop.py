import os
import sys
import unittest
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shop.models import OrderStatus, Product, Role
from shop.payments import CardPayment, CashPayment, IPayment, IRefundable, SBPPayment
from shop.repositories import (CartRepository, OrderRepository,
                               ProductRepository, UserRepository)
from shop.services import (AuthService, CartService, CatalogService,
                           InventoryService, OrderService, PriceCalculator,
                           ProductAdminService)


class ShopTestCase(unittest.TestCase):
    def setUp(self):
        self.products, self.users = ProductRepository(), UserRepository()
        self.auth = AuthService(self.users)
        self.admin = self.auth.register("A", "a@a.ru", "admin123", Role.ADMIN)
        self.client = self.auth.register("C", "c@c.ru", "client123")
        self.courier = self.auth.register("K", "k@k.ru", "courier1", Role.COURIER)
        ProductAdminService(self.products).add_product(
            self.admin, Product(1, "Яблоки", "", Decimal("100"), Decimal("10"), "Фрукты", "кг"))
        ProductAdminService(self.products).add_product(
            self.admin, Product(2, "Молоко", "", Decimal("80"), Decimal("5"), "Молочные продукты"))
        self.cart_svc = CartService(CartRepository(), self.products)
        self.orders = OrderService(OrderRepository(),
                                   InventoryService(self.products, self.products),
                                   PriceCalculator())


class AuthTests(ShopTestCase):
    def test_login_ok_and_fail(self):
        self.assertIsNotNone(self.auth.login("c@c.ru", "client123"))
        self.assertIsNone(self.auth.login("c@c.ru", "wrong"))

    def test_password_not_stored_plain(self):
        self.assertNotIn("client123", self.client.password_hash)

    def test_duplicate_email(self):
        with self.assertRaises(ValueError):
            self.auth.register("X", "c@c.ru", "123456")


class CatalogTests(ShopTestCase):
    def test_search_and_filter(self):
        cat = CatalogService(self.products)
        self.assertEqual([p.name for p in cat.search("мол")], ["Молоко"])
        self.assertEqual(len(cat.search(max_price=Decimal(90))), 1)
        self.assertEqual(len(cat.by_category("Фрукты")), 1)
        self.assertEqual(cat.search("нет такого"), [])

    def test_only_admin_manages_catalog(self):
        with self.assertRaises(PermissionError):
            ProductAdminService(self.products).change_price(self.client, 1, Decimal(1))


class CartTests(ShopTestCase):
    def test_cart_quantity_and_total(self):
        self.cart_svc.add(self.client, 1, Decimal("1.5"))
        cart = self.cart_svc.add(self.client, 1, Decimal("0.5"))
        self.assertEqual(cart.total, Decimal("200"))
        cart = self.cart_svc.change_quantity(self.client, 1, Decimal(0))
        self.assertEqual(cart.items, [])


class OrderTests(ShopTestCase):
    def _order(self, qty=2):
        self.cart_svc.add(self.client, 1, Decimal(qty))
        cart = self.cart_svc.get_cart(self.client)
        return self.orders.checkout(self.client, cart, "Адрес", "10:00")

    def test_checkout_reserves_stock_and_clears_cart(self):
        res = self._order(2)
        self.assertTrue(res.ok)
        self.assertEqual(self.products.get(1).quantity, Decimal(8))
        self.assertEqual(self.cart_svc.get_cart(self.client).items, [])

    def test_out_of_stock(self):
        res = self._order(999)
        self.assertFalse(res.ok)
        self.assertIn("недостаточно", res.errors[0])

    def test_empty_cart_and_no_address(self):
        cart = self.cart_svc.get_cart(self.client)
        self.assertFalse(self.orders.checkout(self.client, cart, "A", "T").ok)
        self.cart_svc.add(self.client, 1, Decimal(1))
        self.assertFalse(self.orders.checkout(self.client, cart, "", "").ok)

    def test_delivery_fee_rule(self):
        order = self._order(2).order            # 200 < 1500 -> +200
        self.assertEqual(self.orders.total_to_pay(order), Decimal(400))

    def test_payment_failure_then_retry_success(self):
        order = self._order(1).order
        self.assertEqual(self.orders.pay(order, CardPayment("12")).status.value, "Ошибка")
        self.assertEqual(order.status, OrderStatus.NEW)
        self.orders.pay(order, CashPayment(Decimal(1000)))
        self.assertEqual(order.status, OrderStatus.PAID)

    def test_status_flow_and_permissions(self):
        order = self._order(1).order
        self.orders.pay(order, SBPPayment("+996555123456"))
        with self.assertRaises(PermissionError):
            self.orders.update_status(self.client, order.id, OrderStatus.ASSEMBLING)
        with self.assertRaises(ValueError):
            self.orders.update_status(self.admin, order.id, OrderStatus.DELIVERED)
        self.orders.update_status(self.admin, order.id, OrderStatus.ASSEMBLING)
        self.assertEqual(self.orders.track(self.client, order.id), OrderStatus.ASSEMBLING)

    def test_history_client_vs_admin(self):
        self._order(1)
        other = self.auth.register("O", "o@o.ru", "other123")
        self.assertEqual(len(self.orders.history(self.client)), 1)
        self.assertEqual(len(self.orders.history(other)), 0)
        self.assertEqual(len(self.orders.history(self.admin)), 1)
        with self.assertRaises(PermissionError):
            self.orders.track(other, 1)


class PaymentLiskovTests(unittest.TestCase):
    def test_all_payments_substitutable(self):
        methods = [CardPayment("1111222233334444"), CashPayment(Decimal(500)),
                   SBPPayment("+996555123456")]
        for m in methods:
            self.assertIsInstance(m, IPayment)
            self.assertTrue(m.pay(Decimal(100)).success)
            self.assertFalse(m.pay(Decimal(0)).success)   # один и тот же контракт

    def test_cash_is_not_refundable(self):
        self.assertNotIsInstance(CashPayment(Decimal(1)), IRefundable)
        self.assertIsInstance(SBPPayment("+996555123456"), IRefundable)


if __name__ == "__main__":
    unittest.main()
