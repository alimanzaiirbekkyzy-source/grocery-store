# Применение принципов SOLID

*Автор раздела: Студент 4 (Lead Developer)*. Код: `Source/shop/`.

## Сводная таблица (классы, проблема, решение)
| № | Класс / интерфейс | Принцип | Какую проблему решает | Где в коде |
|---|---|---|---|---|
| 1 | `OrderService` | **S** | Класс занимается только заказами; оплата, склад и расчёт цены вынесены отдельно, поэтому изменение правил доставки не затрагивает логику заказа | `services.py` |
| 2 | `ProductRepository` | **S** | Отвечает только за хранение продуктов, без бизнес-правил | `repositories.py` |
| 3 | `InventoryService`, `PriceCalculator` | **S** | Проверка наличия и расчёт стоимости — отдельные ответственности (`<<include>>` из Use Case) | `services.py` |
| 4 | `IPayment` | **O** | Новый способ оплаты (QR, СБП) добавляется новым классом, `OrderService` не меняется. `SBPPayment` добавлен именно так | `payments.py` |
| 5 | `CardPayment`, `CashPayment`, `SBPPayment` | **L** | Все реализации следуют одному контракту (отказ → `PaymentResult(success=False)`, без исключений), поэтому взаимозаменяемы. Проверено тестом `test_all_payments_substitutable` | `payments.py` |
| 6 | `IProductReader` / `IProductWriter` | **I** | Каталог для клиента видит только чтение, администратору нужна запись; никто не зависит от лишних методов | `repositories.py` |
| 7 | `IPayment` / `IRefundable` | **I** | Возврат средств выделен: наличные не умеют «вернуть» онлайн, поэтому `CashPayment` не обязан реализовывать `refund` | `payments.py` |
| 8 | `OrderService.pay(order, IPayment)` | **D** | Высокоуровневый модуль зависит от абстракции, а не от `CardPayment`; репозитории также внедряются через конструктор | `services.py` |

## Подробно по принципам

### S — Single Responsibility
Каждый сервис имеет одну причину для изменения: `AuthService` — вход и регистрация, `CatalogService` — чтение каталога, `CartService` — корзина, `OrderService` — заказы, `ProductAdminService` — управление каталогом.

### O — Open/Closed
```python
class QRPayment(IPayment):          # новый класс — старый код не трогаем
    method_name = "QR"
    def pay(self, amount): ...
order_service.pay(order, QRPayment())
```

### L — Liskov Substitution
В любом месте, где ожидается `IPayment`, можно подставить `CardPayment`, `CashPayment` или `SBPPayment`, и поведение остаётся корректным: результат всегда `PaymentResult`.

### I — Interface Segregation
Вместо одного «толстого» интерфейса хранилища — `IProductReader`, `IProductWriter`; вместо «платёж + возврат» — `IPayment` и `IRefundable`.

### D — Dependency Inversion
`OrderService.__init__(orders: IOrderRepository, inventory, calculator)`; способ оплаты приходит параметром `IPayment`. Сборка зависимостей происходит в одном месте — `main.py` (Composition Root).
