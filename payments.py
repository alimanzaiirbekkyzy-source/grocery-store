"""Способы оплаты. Реализация принципов O, L, I, D из SOLID.

IPayment — абстракция, от которой зависит OrderService (D).
Новый способ оплаты = новый класс, существующий код не меняется (O).
Все реализации следуют одному контракту: бизнес-ошибка -> PaymentResult(success=False),
исключение не бросается, значит классы взаимозаменяемы (L).
Возврат средств вынесен в отдельный интерфейс IRefundable (I): наличные
через интернет-магазин «вернуть» тем же способом нельзя — им не нужен лишний метод.
"""
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class PaymentResult:
    success: bool
    message: str
    transaction_id: str = ""


class IPayment(ABC):
    method_name: str = "unknown"

    @abstractmethod
    def pay(self, amount: Decimal) -> PaymentResult:
        """Провести платёж. Не должен бросать исключения при отказе."""


class IRefundable(ABC):
    @abstractmethod
    def refund(self, transaction_id: str, amount: Decimal) -> PaymentResult:
        """Вернуть деньги по ранее проведённой транзакции."""


def _tx() -> str:
    return uuid.uuid4().hex[:12]


class CardPayment(IPayment, IRefundable):
    method_name = "Банковская карта"

    def __init__(self, card_number: str, holder: str = ""):
        self._card = card_number.replace(" ", "")
        self._holder = holder

    def pay(self, amount: Decimal) -> PaymentResult:
        if amount <= 0:
            return PaymentResult(False, "Сумма должна быть положительной")
        if not (self._card.isdigit() and len(self._card) == 16):
            return PaymentResult(False, "Неверный номер карты")
        return PaymentResult(True, "Оплата картой прошла успешно", _tx())

    def refund(self, transaction_id: str, amount: Decimal) -> PaymentResult:
        return PaymentResult(True, "Возврат на карту оформлен", transaction_id)


class CashPayment(IPayment):
    """Оплата наличными курьеру при получении."""
    method_name = "Наличные"

    def __init__(self, cash_given: Decimal):
        self._cash = Decimal(cash_given)

    def pay(self, amount: Decimal) -> PaymentResult:
        if amount <= 0:
            return PaymentResult(False, "Сумма должна быть положительной")
        if self._cash < amount:
            return PaymentResult(False, "Недостаточно наличных")
        change = self._cash - amount
        return PaymentResult(True, f"Принято наличными, сдача {change}", _tx())


class SBPPayment(IPayment, IRefundable):
    """Система быстрых платежей. Добавлена БЕЗ изменения OrderService (принцип O)."""
    method_name = "СБП"

    def __init__(self, phone: str):
        self._phone = phone

    def pay(self, amount: Decimal) -> PaymentResult:
        if amount <= 0:
            return PaymentResult(False, "Сумма должна быть положительной")
        digits = "".join(c for c in self._phone if c.isdigit())
        if len(digits) < 10:
            return PaymentResult(False, "Неверный номер телефона")
        return PaymentResult(True, "Оплата через СБП прошла успешно", _tx())

    def refund(self, transaction_id: str, amount: Decimal) -> PaymentResult:
        return PaymentResult(True, "Возврат через СБП оформлен", transaction_id)
