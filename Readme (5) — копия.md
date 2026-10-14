# Продуктовый интернет-магазин

Учебный проект по дисциплине **«Архитектура программных систем»**. Этап: Блок 1 — проработка проектного решения.

Система позволяет клиенту выбрать продукты, оформить заказ с доставкой, оплатить его (карта / наличные / СБП) и отслеживать статус; администратору и курьеру — управлять каталогом и статусами заказов.

## Команда
| Роль | Участник (ФИО) | Что сделал |
|---|---|---|
| Студент 1 — Системный аналитик | _ФИО_ | Бизнес-требования, ТЗ |
| Студент 2 — Архитектор UML | _ФИО_ | Use Case, диаграмма классов |
| Студент 3 — Процессный инженер | _ФИО_ | Блок-схемы |
| Студент 4 — Lead Developer / Git | _ФИО_ | Репозиторий, код, SOLID |

## Структура репозитория
```
/
├── Source/                  # исходный код (Python 3.10+)
│   ├── shop/                #   models, payments, repositories, services
│   ├── tests/               #   unit-тесты
│   └── main.py              #   демо-сценарий
├── Docs/
│   ├── TZ_and_Requirements.md   # бизнес-требования и ТЗ
│   ├── Entities.md              # сущности, атрибуты, кратности
│   ├── SOLID.md                 # обоснование принципов SOLID
│   ├── Defense_Checklist.md     # подготовка к защите, команды Git
│   ├── Diagrams/                # Use Case и диаграмма классов (.png/.svg + исходники .dot)
│   └── Flowcharts/              # три блок-схемы (.png/.svg + исходники .dot)
└── Readme.md
```

## Быстрый старт
```bash
cd Source
python main.py                              # демо: каталог → корзина → заказ → оплата → доставка
python -m unittest discover -s tests -v     # 15 тестов
```

## Диаграммы
| Use Case | Диаграмма классов |
|---|---|
| ![usecase](Docs/Diagrams/usecase.png) | ![classes](Docs/Diagrams/class_diagram.png) |

Блок-схемы: [оформление и оплата](Docs/Flowcharts/flow1_checkout_payment.png) · [поиск](Docs/Flowcharts/flow2_search.png) · [список заказов](Docs/Flowcharts/flow3_orders_list.png)

## Архитектура кратко
- `IPayment` + `CardPayment` / `CashPayment` / `SBPPayment` — расширяемая оплата (OCP, LSP, DIP);
- `IProductReader` / `IProductWriter`, `IRefundable` — разделённые интерфейсы (ISP);
- сервисы с одной ответственностью (SRP): `OrderService`, `CatalogService`, `CartService`, `InventoryService`, `PriceCalculator`.

Подробнее — [Docs/SOLID.md](Docs/SOLID.md).
