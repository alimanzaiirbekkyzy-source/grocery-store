"""Интерфейсы хранилищ и их in-memory реализации.

ISP: чтение каталога (IProductReader) и управление каталогом (IProductWriter)
разделены — клиентский код каталога не видит методов администратора.
SRP: ProductRepository отвечает только за хранение продуктов.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, List, Optional

from .models import Cart, Order, Product, User


# ---------- интерфейсы ----------
class IProductReader(ABC):
    @abstractmethod
    def get(self, product_id: int) -> Optional[Product]: ...

    @abstractmethod
    def list_all(self) -> List[Product]: ...

    @abstractmethod
    def find_by_category(self, category: str) -> List[Product]: ...

    @abstractmethod
    def search(self, name: str = "", min_price: Optional[Decimal] = None,
               max_price: Optional[Decimal] = None) -> List[Product]: ...


class IProductWriter(ABC):
    @abstractmethod
    def add(self, product: Product) -> Product: ...

    @abstractmethod
    def update_price(self, product_id: int, price: Decimal) -> None: ...

    @abstractmethod
    def write_off(self, product_id: int, quantity: Decimal) -> None: ...


class IOrderRepository(ABC):
    @abstractmethod
    def add(self, order: Order) -> Order: ...

    @abstractmethod
    def get(self, order_id: int) -> Optional[Order]: ...

    @abstractmethod
    def list_by_user(self, user_id: int) -> List[Order]: ...

    @abstractmethod
    def list_all(self) -> List[Order]: ...

    @abstractmethod
    def next_id(self) -> int: ...


class IUserRepository(ABC):
    @abstractmethod
    def add(self, user: User) -> User: ...

    @abstractmethod
    def find_by_email(self, email: str) -> Optional[User]: ...

    @abstractmethod
    def next_id(self) -> int: ...


class ICartRepository(ABC):
    @abstractmethod
    def get_or_create(self, user_id: int) -> Cart: ...


# ---------- in-memory реализации ----------
class ProductRepository(IProductReader, IProductWriter):
    def __init__(self) -> None:
        self._data: Dict[int, Product] = {}

    def get(self, product_id: int) -> Optional[Product]:
        return self._data.get(product_id)

    def list_all(self) -> List[Product]:
        return list(self._data.values())

    def find_by_category(self, category: str) -> List[Product]:
        return [p for p in self._data.values() if p.category.lower() == category.lower()]

    def search(self, name="", min_price=None, max_price=None) -> List[Product]:
        result = []
        for p in self._data.values():
            if name and name.lower() not in p.name.lower():
                continue
            if min_price is not None and p.price < min_price:
                continue
            if max_price is not None and p.price > max_price:
                continue
            result.append(p)
        return result

    def add(self, product: Product) -> Product:
        self._data[product.id] = product
        return product

    def update_price(self, product_id: int, price: Decimal) -> None:
        if price <= 0:
            raise ValueError("Цена должна быть положительной")
        self._data[product_id].price = price

    def write_off(self, product_id: int, quantity: Decimal) -> None:
        product = self._data[product_id]
        if quantity > product.quantity:
            raise ValueError("Списание превышает остаток")
        product.quantity -= quantity


class OrderRepository(IOrderRepository):
    def __init__(self) -> None:
        self._data: Dict[int, Order] = {}
        self._seq = 0

    def next_id(self) -> int:
        self._seq += 1
        return self._seq

    def add(self, order: Order) -> Order:
        self._data[order.id] = order
        return order

    def get(self, order_id: int) -> Optional[Order]:
        return self._data.get(order_id)

    def list_by_user(self, user_id: int) -> List[Order]:
        return sorted((o for o in self._data.values() if o.user_id == user_id),
                      key=lambda o: o.order_date, reverse=True)

    def list_all(self) -> List[Order]:
        return sorted(self._data.values(), key=lambda o: o.order_date, reverse=True)


class UserRepository(IUserRepository):
    def __init__(self) -> None:
        self._data: Dict[int, User] = {}
        self._seq = 0

    def next_id(self) -> int:
        self._seq += 1
        return self._seq

    def add(self, user: User) -> User:
        self._data[user.id] = user
        return user

    def find_by_email(self, email: str) -> Optional[User]:
        return next((u for u in self._data.values() if u.email.lower() == email.lower()), None)


class CartRepository(ICartRepository):
    """Корзина хранится по пользователю и переживает «перезагрузку» сессии (НФТ-3)."""
    def __init__(self) -> None:
        self._data: Dict[int, Cart] = {}

    def get_or_create(self, user_id: int) -> Cart:
        if user_id not in self._data:
            self._data[user_id] = Cart(id=len(self._data) + 1, user_id=user_id)
        return self._data[user_id]
