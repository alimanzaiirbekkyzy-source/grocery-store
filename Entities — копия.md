# Ключевые сущности и атрибуты

| Сущность | Назначение | Идентификатор | Основные атрибуты |
|---|---|---|---|
| `User` | Пользователь системы | `id` | name, email, passwordHash, role |
| `Product` | Товар каталога | `id` | name, description, price, quantity, category, unit |
| `Cart` | Корзина пользователя | `id` | userId, createdAt, items |
| `CartItem` | Позиция корзины | `id` | product, quantity, price |
| `Order` | Заказ клиента | `id` | orderDate, status, address, deliveryTime, totalAmount |
| `OrderItem` | Позиция заказа | `id` | product, quantity, price (на момент заказа) |
| `Payment` | Платёж | `id` | amount, date, status, method |

## Связи и кратности
| Связь | Тип | Кратность |
|---|---|---|
| Order — OrderItem | Композиция | 1 — 1..* |
| Cart — CartItem | Композиция | 1 — 0..* |
| Product — CartItem / OrderItem | Агрегация | 1 — 0..* |
| User — Order | Ассоциация | 1 — 0..* |
| User — Cart | Ассоциация | 1 — 0..1 |
| Order — Payment | Ассоциация | 1 — 0..1 |
| CardPayment / CashPayment / SBPPayment → IPayment | Реализация | — |

**Почему композиция, а не агрегация?** Позиция заказа не существует без заказа — удалили заказ, исчезли позиции. Товар же живёт независимо: он остаётся в каталоге, даже если корзину очистили.
