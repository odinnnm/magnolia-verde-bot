# Magnolia Verde Telegram Bot MVP Starter

Стартовый skeleton для MVP Telegram-бота бутика «Магнолия Верде».

## Что внутри
- Python 3.11
- aiogram 3.x
- PostgreSQL 16
- Redis 7
- Docker Compose
- async SQLAlchemy 2.x
- Redis FSM storage
- polling режим для локальной разработки

## Структура проекта

```text
app/
  bot/       # инициализация бота, роутеры, клавиатуры, entrypoint
  db/        # SQLAlchemy base, engine/session, ORM models, repositories
  fsm/       # FSM states и Redis storage
  schemas/   # pydantic-схемы для анализа и черновиков
  services/  # сервисы анализа, генерации текста, публикации, черновиков
  utils/     # конфиг и logging
  config.py  # совместимый re-export настроек
  main.py    # совместимый entrypoint для Docker
```

## Быстрый старт
1. Создайте `.env` на основе примера:
   ```bash
   cp .env.example .env
   ```
2. Заполните `BOT_TOKEN`, `ALLOWED_USER_IDS`, `DEFAULT_CHANNEL_ID`.
3. Запустите проект:
   ```bash
   docker compose up --build
   ```
4. Напишите боту `/start`.

## Что уже готово
- модульная структура без поломки существующего Docker-старта;
- чтение конфигурации из `.env`;
- Redis storage для FSM;
- async SQLAlchemy engine и базовая ORM-модель черновика;
- сохранение черновиков в PostgreSQL;
- базовые команды `/start`, `/help`, `/new`, `/drafts`, `/settings`, `/cancel`;
- mock-анализ фото и генерация подписи;
- публикация в канал через preview-карточку.

## Важно
- Бот должен быть администратором канала с правом публикации.
- `DEFAULT_CHANNEL_ID` для канала обычно имеет вид `-100xxxxxxxxxx`.
- `ALLOWED_USER_IDS` — Telegram user id сотрудников, которым можно пользоваться ботом.
- Таблицы MVP создаются автоматически при старте контейнера.

## Следующие шаги
- заменить mock vision/text generation на реальную интеграцию;
- добавить Alembic-миграции;
- вынести repository/service contracts для черновиков и логов действий;
- покрыть сценарии тестами.
