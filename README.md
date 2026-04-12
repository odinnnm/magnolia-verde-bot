# Magnolia Verde Telegram Bot MVP Starter

Стартовый skeleton для MVP Telegram-бота бутика «Магнолия Верде».

## Что внутри
- Python 3.11
- aiogram 3.x
- PostgreSQL 16
- Redis 7
- Docker Compose
- async SQLAlchemy 2.x
- Alembic
- Redis FSM storage
- polling для локальной разработки

## Структура проекта

```text
app/
  bot/       # инициализация бота, роутеры, клавиатуры, entrypoint
  db/        # SQLAlchemy base, engine/session, ORM models, repositories
  fsm/       # FSM states и Redis storage
  schemas/   # pydantic-схемы для анализа и черновиков
  services/  # mock-сервисы анализа, генерации текста, публикации
  utils/     # конфиг и logging
  config.py  # совместимый re-export настроек
  main.py    # совместимый entrypoint для Docker
```

## Запуск
1. Создайте `.env`:
   ```bash
   cp .env.example .env
   ```
2. Заполните `BOT_TOKEN`, `ALLOWED_USER_IDS`, `DEFAULT_CHANNEL_ID`.
3. Поднимите инфраструктуру:
   ```bash
   docker compose up -d postgres redis
   ```
4. Примените миграции:
   ```bash
   docker compose run --rm bot alembic upgrade head
   ```
5. Запустите бота:
   ```bash
   docker compose up --build bot
   ```
6. Напишите боту `/start`.

## Миграции

Приложение не использует `create_all` при старте. Схема БД и сиды поднимаются миграциями Alembic.

Применить миграции:
```bash
docker compose run --rm bot alembic upgrade head
```

Проверить текущую ревизию:
```bash
docker compose run --rm bot alembic current
```

Создать новую миграцию:
```bash
docker compose run --rm bot alembic revision -m "describe change"
```

Проверить сид словаря цветов:
```bash
docker compose exec postgres sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "select slug, display_name from flower_dictionary order by display_name;"'
```

## Что уже полностью работает в MVP
- ограничение доступа по `ALLOWED_USER_IDS`;
- создание нового сценария через `/new`;
- приём фото и mock-анализ композиции;
- создание `post` в статусе `draft`;
- генерация подписи и показ preview;
- кнопки preview: публикация, перегенерация, сокращение, premium-вариант, цена, наличие, история, ручное редактирование, сохранение черновика, отмена;
- сохранение и просмотр последних черновиков через `/drafts`;
- публикация в канал с записью `published_message_id` и `published_at`;
- seed `flower_dictionary` на 15 популярных цветов;
- базовая обработка edge cases и логирование.

## Ручной тест
1. Запустите проект по шагам из раздела «Запуск».
2. В Telegram проверьте:
   - `/start`
   - `/help`
   - `/new`
   - отправку фото
3. В preview проверьте:
   - `Сделать короче`
   - `Перегенерировать`
   - `Сделать премиальнее`
   - `Добавить цену`
   - `Добавить наличие`
   - `Добавить историю`
   - `Редактировать вручную`
   - `Сохранить в черновики`
4. Выполните `/drafts`.
5. Создайте новый пост и нажмите `Опубликовать`.
6. Проверьте записи в БД:
   ```bash
   docker compose exec postgres sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "select id, status, published_message_id, failed_reason from posts order by created_at desc limit 10;"'
   ```

## Типовые ошибки
- `У вас нет доступа к этому боту.`
  Причина: ваш `Telegram user id` не включён в `ALLOWED_USER_IDS`.
- `Сейчас нужен именно снимок.`
  Причина: на шаге ожидания фото было отправлено не изображение.
- `Текущий сценарий уже завершён или сброшен. Начните новый через /new.`
  Причина: `post_id` пропал из FSM state.
- `Черновик не найден в базе. Начните новый сценарий через /new.`
  Причина: запись `post` отсутствует в БД.
- `Не удалось опубликовать пост в канал. Черновик сохранён со статусом ошибки.`
  Причина: бот не может отправить сообщение в канал или у канала недостаточно прав.

## Важно
- Бот должен быть администратором канала с правом публикации.
- `DEFAULT_CHANNEL_ID` для канала обычно имеет вид `-100xxxxxxxxxx`.
- `ALLOWED_USER_IDS` — Telegram user id сотрудников, которым можно пользоваться ботом.
- Перед первым запуском бота примените миграции Alembic.
