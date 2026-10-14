"""Сущности предметной области (Domain Model).

Связи (см. Docs/Diagrams/class_diagram):
  * Композиция: Order *-- OrderItem, Cart *-- CartItem
    (позиции создаются внутри целого и не живут без него)
  * Агрегация:  Product o-- CartItem, Product o-- OrderItem
    (товар существует независимо от корзин и заказов)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional


class Role(Enum):
    CLIENT = "client"
    ADMIN = "admin"
    COURIER = "courier"


class OrderStatus(Enum):
    NEW = "Новый"
    PAID = "Оплачен"
    ASSEMBLING = "Собирается"
    DELIVERING = "В доставке"
    DELIVERED = "Доставлен"
    CANCELLED = "Отменён"


class PaymentStatus(Enum):
    PENDING = "Ожидает"
    SUCCESS = "Успешно"
    FAILED = "Ошибка"


# Допустимые переходы статусов заказа (BR-09)
ALLOWED_TRANSITIONS = {
    OrderStatus.NEW: {OrderStatus.PAID, OrderStatus.CANCELLED},
    OrderStatus.PAID: {OrderStatus.ASSEMBLING, OrderStatus.CANCELLED},
    OrderStatus.ASSEMBLING: {OrderStatus.DELIVERING},
    OrderStatus.DELIVERING: {OrderStatus.DELIVERED},
    OrderStatus.DELIVERED: set(),
    OrderStatus.CANCELLED: set(),
}


@dataclass
class User:
    id: int
    name: str
    email: str
    password_hash: str
    role: Role = Role.CLIENT

    def is_admin(self) -> bool:
        return self.role == Role.ADMIN


@dataclass
class Product:
    id: int
    name: str
    description: str
    price: Decimal            # цена за единицу (шт/кг)
    quantity: Decimal         # остаток на складе
    category: str = "Бакалея"
    unit: str = "шт"          # "шт" или "кг" — вес поддерживается (BR-04)

    def is_available(self, qty: Decimal) -> bool:
        return self.quantity >= qty


@dataclass
class CartItem:
    id: int
    product: Product          # агрегация
    quantity: Decimal

    @property
    def price(self) -> Decimal:
        return self.product.price

    @property
    def subtotal(self) -> Decimal:
        return self.price * self.quantity


@dataclass
class Cart:
    id: int
    user_id: int
    created_at: datetime = field(default_factory=datetime.now)
    items: List[CartItem] = field(default_factory=list)   # композиция
    _next_item_id: int = 1

    def add_product(self, product: Product, quantity: Decimal = Decimal(1)) -> CartItem:
        if quantity <= 0:
            raise ValueError("Количество должно быть положительным")
        for item in self.items:
            if item.product.id == product.id:
                item.quantity += quantity
                return item
        item = CartItem(self._next_item_id, product, quantity)
        self._next_item_id += 1
        self.items.append(item)
        return item

    def set_quantity(self, product_id: int, quantity: Decimal) -> None:
        if quantity <= 0:
            self.remove_product(product_id)
            return
        for item in self.items:
            if item.product.id == product_id:
                item.quantity = quantity
                return
        raise KeyError(f"Товара {product_id} нет в корзине")

    def remove_product(self, product_id: int) -> None:
        self.items = [i for i in self.items if i.product.id != product_id]

    def clear(self) -> None:
        self.items.clear()

    @property
    def total(self) -> Decimal:
        return sum((i.subtotal for i in self.items), Decimal(0))


@dataclass
class OrderItem:
    id: int
    product: Product          # агрегация
    quantity: Decimal
    price: Decimal            # цена на момент заказа (снимок)

    @property
    def subtotal(self) -> Decimal:
        return self.price * self.quantity


@dataclass
class Payment:
    id: int
    amount: Decimal
    date: datetime
    status: PaymentStatus
    method: str


@dataclass
class Order:
    id: int
    user_id: int
    address: str
    delivery_time: str
    order_date: datetime = field(default_factory=datetime.now)
    status: OrderStatus = OrderStatus.NEW
    items: List[OrderItem] = field(default_factory=list)  # композиция
    payment: Optional[Payment] = None                     # 0..1

    @property
    def total_amount(self) -> Decimal:
        return sum((i.subtotal for i in self.items), Decimal(0))

    def change_status(self, new_status: OrderStatus) -> None:
        if new_status not in ALLOWED_TRANSITIONS[self.status]:
            raise ValueError(
                f"Нельзя перевести заказ из «{self.status.value}» в «{new_status.value}»"
            )
        self.status = new_status
