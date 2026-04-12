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

## Миграции Alembic

Приложение больше не создаёт таблицы через `create_all` при старте. Схема БД поднимается миграциями.

Применить миграции в Docker:
```bash
docker compose up -d postgres redis
docker compose run --rm bot alembic upgrade head
```

Проверить текущую ревизию:
```bash
docker compose run --rm bot alembic current
```

Создать новую миграцию после изменения моделей:
```bash
docker compose run --rm bot alembic revision -m "describe change"
```

## Как поднять БД локально

Только инфраструктуру без запуска бота:
```bash
docker compose up -d postgres redis
```

Проверить, что PostgreSQL доступен:
```bash
docker compose ps
```

После этого можно накатывать миграции:
```bash
docker compose run --rm bot alembic upgrade head
```

## Что уже готово
- модульная структура без поломки существующего Docker-старта;
- чтение конфигурации из `.env`;
- Redis storage для FSM;
- async SQLAlchemy engine, Alembic и MVP data layer;
- базовые таблицы `users`, `channels`, `posts`, `post_images`, `flower_dictionary`, `post_flower_matches`, `bot_settings`, `audit_log`;
- базовые repositories для users/channels/posts;
- базовые команды `/start`, `/help`, `/new`, `/drafts`, `/settings`, `/cancel`;
- mock-анализ фото и генерация подписи;
- публикация в канал через preview-карточку.

## Важно
- Бот должен быть администратором канала с правом публикации.
- `DEFAULT_CHANNEL_ID` для канала обычно имеет вид `-100xxxxxxxxxx`.
- `ALLOWED_USER_IDS` — Telegram user id сотрудников, которым можно пользоваться ботом.
- Перед первым запуском бота примени миграции Alembic.

## Следующие шаги
- заменить mock vision/text generation на реальную интеграцию;
- расширить работу с `posts` и `post_images` до полноценного draft lifecycle;
- добавить аудит действий в `audit_log`;
- покрыть сценарии тестами.
