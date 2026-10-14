"""Демонстрационный сценарий: от каталога до доставки.
Запуск:  python main.py   (из папки Source/)
"""
from decimal import Decimal

from shop.models import OrderStatus, Product, Role
from shop.payments import CardPayment, SBPPayment
from shop.repositories import (CartRepository, OrderRepository,
                               ProductRepository, UserRepository)
from shop.services import (AuthService, CartService, CatalogService,
                           InventoryService, OrderService, PriceCalculator,
                           ProductAdminService)


def main() -> None:
    # --- сборка зависимостей (Composition Root) ---
    products, users = ProductRepository(), UserRepository()
    carts, orders = CartRepository(), OrderRepository()
    auth = AuthService(users)
    catalog = CatalogService(products)
    admin_svc = ProductAdminService(products)
    cart_svc = CartService(carts, products)
    order_svc = OrderService(orders, InventoryService(products, products), PriceCalculator())

    admin = auth.register("Админ", "admin@shop.ru", "admin123", Role.ADMIN)
    client = auth.register("Анна", "anna@mail.ru", "secret1")
    courier = auth.register("Курьер", "courier@shop.ru", "courier1", Role.COURIER)

    for p in [
        Product(1, "Помидоры", "Свежие", Decimal("250"), Decimal("50"), "Овощи", "кг"),
        Product(2, "Молоко 3.2%", "1 л", Decimal("85"), Decimal("100"), "Молочные продукты"),
        Product(3, "Гречка", "900 г", Decimal("110"), Decimal("80"), "Бакалея"),
    ]:
        admin_svc.add_product(admin, p)

    print("Каталог 'Овощи':", [p.name for p in catalog.by_category("Овощи")])
    print("Поиск 'мол':", [p.name for p in catalog.search("мол", max_price=Decimal(100))])

    cart_svc.add(client, 1, Decimal("2.5"))
    cart_svc.add(client, 2, Decimal(3))
    cart = cart_svc.change_quantity(client, 2, Decimal(4))
    print("Сумма корзины:", cart.total)

    result = order_svc.checkout(client, cart, "ул. Чуй 1, кв. 5", "18:00-20:00")
    assert result.ok, result.errors
    order = result.order
    print("К оплате (с доставкой):", order_svc.total_to_pay(order))

    bad = order_svc.pay(order, CardPayment("1234"))
    print("Оплата неверной картой:", bad.status.value)
    good = order_svc.pay(order, SBPPayment("+996 555 123 456"))
    print("Оплата СБП:", good.status.value, "| Статус заказа:", order.status.value)

    for st in (OrderStatus.ASSEMBLING, OrderStatus.DELIVERING, OrderStatus.DELIVERED):
        order_svc.update_status(courier if st != OrderStatus.ASSEMBLING else admin, order.id, st)
    print("Клиент отслеживает заказ:", order_svc.track(client, order.id).value)
    print("История клиента:", [(o.id, o.status.value) for o in order_svc.history(client)])


if __name__ == "__main__":
    main()
