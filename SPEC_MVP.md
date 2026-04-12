# Техническое задание и архитектура MVP
## Проект: Telegram-бот для публикации фото цветов и букетов в канал «Магнолия Верде»

Версия: 0.1 MVP handoff
Дата: 2026-04-12

---

## 1. Цель проекта

Создать внутреннего Telegram-бота для команды цветочного бутика «Магнолия Верде», который:
- принимает от сотрудника фото нового цветка или букета;
- анализирует изображение;
- определяет вероятные цветы, цветовую гамму и настроение композиции;
- генерирует короткую подпись для Telegram-канала;
- по запросу добавляет цену, наличие и короткую историю цветка;
- показывает предпросмотр;
- после подтверждения публикует фото и подпись в канал.

MVP должен решать задачу быстрого контент-потока для Telegram-канала и уменьшать ручную нагрузку на сотрудников.

---

## 2. Границы MVP

### Входит в MVP
- Telegram-бот для внутреннего использования сотрудниками.
- Приём одной фотографии на один пост.
- Распознавание: цветок/букет, вероятные виды цветов, палитра, стиль.
- Генерация текста поста.
- Полуавтоматический режим: только через предпросмотр и подтверждение.
- Добавление цены и статуса наличия.
- Опциональное добавление короткой истории цветка.
- Сохранение черновиков.
- Публикация в один Telegram-канал.
- Логи действий сотрудников.

### Не входит в MVP
- Автопубликация без подтверждения.
- Полноценная CRM.
- Интернет-магазин.
- Мультиканальность (Instagram/VK/сайт).
- Личный кабинет в браузере.
- Складской учёт.
- Продвинутая аналитика контента.
- Роли и права сложнее базовых editor/admin.

---

## 3. Пользовательские роли

### 3.1. Editor
Сотрудник, который:
- общается с ботом в личном чате;
- создаёт черновик;
- редактирует подпись;
- публикует пост в канал.

### 3.2. Admin
Плюс к возможностям editor:
- меняет настройки бота;
- выбирает канал публикации;
- управляет глобальными шаблонами и справочником цветов.

---

## 4. Пользовательские сценарии

### Сценарий 1. Быстрый пост
1. Пользователь запускает `/new`.
2. Бот просит отправить фото.
3. Пользователь отправляет фото.
4. Бот анализирует изображение.
5. Бот формирует подпись.
6. Бот показывает предпросмотр с кнопками.
7. Пользователь нажимает «Опубликовать».
8. Бот публикует пост в канал и сохраняет статус `published`.

### Сценарий 2. Пост с ценой
1. После предпросмотра пользователь нажимает «Добавить цену».
2. Бот просит ввести цену.
3. Пользователь отправляет, например, `4500`.
4. Бот обновляет текст и показывает новый предпросмотр.

### Сценарий 3. Добавление наличия
1. Пользователь нажимает «Добавить наличие».
2. Бот предлагает варианты:
   - В наличии
   - Под заказ
   - Ограниченное количество
3. Бот обновляет подпись.

### Сценарий 4. Добавление истории цветка
1. Пользователь нажимает «Добавить историю».
2. Если главный цветок распознан с высокой уверенностью, бот подтягивает шаблонную историю.
3. Если уверенность низкая, бот сообщает, что история недоступна, чтобы не выдумывать фактологию.

### Сценарий 5. Ручное редактирование
1. Пользователь нажимает «Редактировать вручную».
2. Бот просит отправить новый текст целиком.
3. После нового текста показывает обновлённый предпросмотр.

### Сценарий 6. Сохранение в черновики
1. Пользователь нажимает «Сохранить в черновики».
2. Бот сохраняет текущий пост со статусом `draft`.
3. Позже пользователь открывает `/drafts`, выбирает нужный черновик и публикует.

---

## 5. Команды бота

### Обязательные
- `/start` — приветствие и краткая инструкция.
- `/new` — создать новый пост.
- `/drafts` — показать черновики пользователя.
- `/help` — показать список команд и краткие пояснения.
- `/settings` — настройки бота и канала публикации.
- `/cancel` — отменить текущий сценарий.

### Inline-кнопки в карточке предпросмотра
- Опубликовать
- Перегенерировать
- Сделать короче
- Сделать более премиально
- Добавить цену
- Добавить наличие
- Добавить историю
- Редактировать вручную
- Сохранить в черновики
- Отмена

---

## 6. Нефункциональные требования

- Бот должен работать 24/7 после развёртывания на VPS.
- Для MVP допустим режим long polling.
- Архитектура должна быть контейнеризирована через Docker Compose.
- Локальная разработка должна запускаться одной командой.
- Конфигурация должна храниться в `.env`.
- Данные Postgres должны сохраняться в Docker volume.
- FSM-состояния в production должны храниться в Redis.
- Все критичные действия логируются.
- Ошибки внешних сервисов должны логироваться и не ломать весь бот.

---

## 7. Технический стек

### Backend
- Python 3.11+
- aiogram 3.x
- FastAPI (для healthcheck и внутренних endpoint'ов при необходимости)
- SQLAlchemy 2.x
- Alembic
- Pydantic v2

### Infrastructure
- Docker
- Docker Compose
- PostgreSQL 16
- Redis 7

### Дополнительно
- structlog или стандартный logging
- pytest
- black / ruff

### Почему такой стек
- Python и aiogram удобны для Telegram-бота и быстрых MVP.
- Postgres подходит для черновиков, постов, логов и справочников.
- Redis нужен для FSM и кэша.
- Docker Compose позволяет одинаково запускать проект на ноутбуке и на VPS.

---

## 8. Архитектура решения

Рекомендуется модульный монолит.

### Компоненты
1. **Telegram Bot Layer**
   - обработка сообщений и callback-кнопок;
   - FSM-сценарии;
   - валидация пользовательского ввода.

2. **Application Services**
   - обработка фото;
   - генерация подписи;
   - публикация в канал;
   - работа с черновиками;
   - работа со справочником цветов.

3. **Persistence Layer**
   - PostgreSQL;
   - repositories / ORM models.

4. **Cache / FSM Layer**
   - Redis.

5. **External Integrations**
   - Telegram Bot API;
   - модуль vision/LLM-интеграции.

### Основной поток данных
1. Сотрудник отправляет фото.
2. Бот скачивает или использует `file_id`.
3. Модуль анализа возвращает структурированный результат.
4. Модуль генерации текста создаёт подпись.
5. Черновик сохраняется в БД.
6. Бот показывает предпросмотр.
7. После подтверждения бот отправляет фото с caption в канал.
8. Статус поста обновляется на `published`.

---

## 9. Логика распознавания и генерации

### 9.1. Vision result contract
Результат анализа изображения должен быть нормализован до структуры:

```json
{
  "object_type": "bouquet",
  "flowers": [
    {"name": "роза", "confidence": 0.83},
    {"name": "эустома", "confidence": 0.71}
  ],
  "colors": ["белый", "розовый"],
  "style_tags": ["нежный", "воздушный"],
  "confidence_overall": 0.76
}
```

### 9.2. Text generation contract
На базе анализа должен формироваться объект:

```json
{
  "title": "Нежный букет в светлой палитре",
  "caption": "Нежный авторский букет в светлой палитре — для тёплого комплимента, дня рождения или особенного повода.",
  "story_text": "Эустома ценится за утончённую форму и мягкую фактуру."
}
```

### 9.3. Правила безопасности контента
- При низкой уверенности использовать формулировки `похоже на`, `вероятно`, `в композиции просматриваются`.
- Не выдумывать точные сорта, если уверенность недостаточна.
- Историю цветка добавлять только при уверенном распознавании.
- Не генерировать длинные и однотипные подписи.

---

## 10. FSM-состояния

Минимальный набор:
- `Idle`
- `WaitingForPhoto`
- `AnalyzingPhoto`
- `WaitingForTypeChoice`
- `PreviewReady`
- `WaitingForPrice`
- `WaitingForAvailability`
- `WaitingForManualEdit`
- `SavedAsDraft`

---

## 11. Структура проекта

```text
magnolia-verde-bot/
├─ .env.example
├─ .gitignore
├─ README.md
├─ docker-compose.yml
├─ Dockerfile
├─ pyproject.toml
├─ alembic.ini
├─ migrations/
├─ app/
│  ├─ main.py
│  ├─ config.py
│  ├─ logging.py
│  ├─ bot/
│  │  ├─ handlers/
│  │  │  ├─ start.py
│  │  │  ├─ new_post.py
│  │  │  ├─ drafts.py
│  │  │  ├─ settings.py
│  │  │  └─ common.py
│  │  ├─ keyboards/
│  │  │  ├─ inline.py
│  │  │  └─ reply.py
│  │  ├─ middlewares/
│  │  │  └─ auth.py
│  │  └─ fsm/
│  │     └─ states.py
│  ├─ api/
│  │  └─ health.py
│  ├─ services/
│  │  ├─ telegram_files.py
│  │  ├─ image_analysis.py
│  │  ├─ caption_generation.py
│  │  ├─ publishing.py
│  │  ├─ drafts.py
│  │  ├─ flower_story.py
│  │  └─ settings.py
│  ├─ db/
│  │  ├─ base.py
│  │  ├─ session.py
│  │  ├─ models/
│  │  │  ├─ user.py
│  │  │  ├─ channel.py
│  │  │  ├─ post.py
│  │  │  ├─ post_image.py
│  │  │  ├─ flower_dictionary.py
│  │  │  ├─ bot_settings.py
│  │  │  └─ audit_log.py
│  │  └─ repositories/
│  │     ├─ users.py
│  │     ├─ posts.py
│  │     ├─ channels.py
│  │     ├─ settings.py
│  │     └─ flowers.py
│  ├─ schemas/
│  │  ├─ vision.py
│  │  ├─ generation.py
│  │  ├─ post.py
│  │  └─ settings.py
│  └─ utils/
│     ├─ text.py
│     └─ dates.py
└─ tests/
   ├─ test_handlers.py
   ├─ test_services.py
   └─ test_repositories.py
```

---

## 12. Схема базы данных

### 12.1. users
```sql
CREATE TABLE users (
  id BIGSERIAL PRIMARY KEY,
  telegram_user_id BIGINT UNIQUE NOT NULL,
  username VARCHAR(255),
  full_name VARCHAR(255),
  role VARCHAR(50) NOT NULL DEFAULT 'editor',
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### 12.2. channels
```sql
CREATE TABLE channels (
  id BIGSERIAL PRIMARY KEY,
  telegram_chat_id BIGINT UNIQUE NOT NULL,
  title VARCHAR(255) NOT NULL,
  is_default BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### 12.3. posts
```sql
CREATE TABLE posts (
  id BIGSERIAL PRIMARY KEY,
  created_by_user_id BIGINT NOT NULL REFERENCES users(id),
  channel_id BIGINT REFERENCES channels(id),
  status VARCHAR(50) NOT NULL,
  object_type VARCHAR(50),
  source_photo_file_id VARCHAR(255) NOT NULL,
  source_photo_path VARCHAR(500),
  detected_flowers_json JSONB,
  detected_colors_json JSONB,
  style_tags_json JSONB,
  confidence_overall NUMERIC(5,2),
  title VARCHAR(255),
  caption TEXT,
  story_text TEXT,
  price_text VARCHAR(100),
  availability_text VARCHAR(255),
  manual_type_hint VARCHAR(50),
  published_message_id BIGINT,
  published_at TIMESTAMP,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### 12.4. post_images
```sql
CREATE TABLE post_images (
  id BIGSERIAL PRIMARY KEY,
  post_id BIGINT NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
  telegram_file_id VARCHAR(255) NOT NULL,
  file_path VARCHAR(500),
  sort_order INT NOT NULL DEFAULT 0,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### 12.5. flower_dictionary
```sql
CREATE TABLE flower_dictionary (
  id BIGSERIAL PRIMARY KEY,
  slug VARCHAR(100) UNIQUE NOT NULL,
  name_ru VARCHAR(255) NOT NULL,
  short_description TEXT,
  story_template TEXT,
  care_note TEXT,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### 12.6. post_flower_matches
```sql
CREATE TABLE post_flower_matches (
  id BIGSERIAL PRIMARY KEY,
  post_id BIGINT NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
  flower_dictionary_id BIGINT REFERENCES flower_dictionary(id),
  detected_name_raw VARCHAR(255),
  confidence NUMERIC(5,2),
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### 12.7. bot_settings
```sql
CREATE TABLE bot_settings (
  id BIGSERIAL PRIMARY KEY,
  default_channel_id BIGINT REFERENCES channels(id),
  default_tone VARCHAR(50),
  append_brand_signature BOOLEAN NOT NULL DEFAULT TRUE,
  brand_signature VARCHAR(255),
  default_hashtags TEXT,
  require_preview_before_publish BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### 12.8. audit_log
```sql
CREATE TABLE audit_log (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT REFERENCES users(id),
  entity_type VARCHAR(50) NOT NULL,
  entity_id BIGINT NOT NULL,
  action VARCHAR(100) NOT NULL,
  payload_json JSONB,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

---

## 13. Статусы поста

Поддерживаемые статусы:
- `draft`
- `ready`
- `published`
- `archived`
- `failed`

---

## 14. Формат подписи

### Базовый шаблон
```text
Нежный авторский букет в светлой палитре — для комплимента, дня рождения или тёплого знака внимания.

Стоимость: 4500 ₽
В наличии

Магнолия Верде
```

### Правила генерации
- До 350–500 символов для MVP.
- Без перегруза эмодзи.
- В одном тоне бренда: элегантно, современно, тепло.
- Сохранять естественный стиль, не писать слишком рекламно.

---

## 15. Бизнес-правила

1. Автопубликация без подтверждения запрещена в MVP.
2. После ручного редактирования пользовательский текст имеет приоритет над машинной генерацией.
3. История цветка добавляется только при уверенном распознавании.
4. При ошибке публикации пост не должен теряться, статус меняется на `failed`.
5. При перегенерации сохраняется исходный анализ изображения.
6. Один пост MVP содержит только одно изображение, но структура БД допускает расширение.

---

## 16. Docker и локальная разработка

### Цель
Разрабатывать на личном ноутбуке без установки Python, Postgres и Redis напрямую в систему.

### Что должно быть установлено локально
- Docker Desktop
- VS Code
- Git

### Что запускается в контейнерах
- `app`
- `postgres`
- `redis`

### Минимальный docker-compose.yml для MVP
```yaml
services:
  app:
    build: .
    container_name: magnolia_bot_app
    env_file:
      - .env
    depends_on:
      - postgres
      - redis
    volumes:
      - .:/app
    command: python -m app.main

  postgres:
    image: postgres:16
    container_name: magnolia_bot_postgres
    environment:
      POSTGRES_DB: magnolia_bot
      POSTGRES_USER: magnolia
      POSTGRES_PASSWORD: magnolia
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    container_name: magnolia_bot_redis
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

### Локальный режим запуска
Для ноутбука использовать long polling.
Webhook и nginx на этом этапе не нужны.

---

## 17. VPS для production

### Рекомендуемый стартовый VPS
- 2 vCPU
- 2–4 GB RAM
- 40–60 GB SSD
- Ubuntu 24.04 LTS

### Предпочтительный вариант
- 2 vCPU
- 4 GB RAM
- 50+ GB SSD

### На сервере должно быть
- Docker Engine
- Docker Compose plugin
- `.env` с прод-конфигурацией
- volume для Postgres
- резервное копирование БД

---

## 18. Переменные окружения

Пример `.env.example`:

```env
BOT_TOKEN=
DEFAULT_CHANNEL_ID=
DATABASE_URL=postgresql+psycopg://magnolia:magnolia@postgres:5432/magnolia_bot
REDIS_URL=redis://redis:6379/0
APP_ENV=local
LOG_LEVEL=INFO
BRAND_SIGNATURE=Магнолия Верде
DEFAULT_TONE=elegant
REQUIRE_PREVIEW_BEFORE_PUBLISH=true
```

---

## 19. Что должен сделать разработчик в первой итерации

### Sprint 1
- Поднять каркас проекта.
- Настроить Docker Compose.
- Подключить aiogram.
- Подключить Postgres и Redis.
- Реализовать `/start`, `/help`, `/new`, `/cancel`.
- Реализовать FSM: загрузка фото → предпросмотр.
- Реализовать сохранение черновика в БД.
- Реализовать публикацию в канал.

### Sprint 2
- Добавить цену и наличие.
- Добавить перегенерацию текста.
- Добавить ручное редактирование.
- Добавить `/drafts`.
- Добавить audit log.

### Sprint 3
- Подключить справочник цветов и историю цветка.
- Улучшить обработку ошибок.
- Добавить базовые тесты.
- Подготовить production-compose и deploy notes.

---

## 20. Критерии приёмки MVP

MVP считается готовым, если:
1. Бот запускается локально через Docker Compose.
2. Сотрудник может создать пост из фото менее чем за 1 минуту.
3. Бот показывает предпросмотр перед публикацией.
4. Пользователь может добавить цену и наличие.
5. Пользователь может вручную отредактировать текст.
6. Пост успешно публикуется в Telegram-канал.
7. Черновик сохраняется и доступен через `/drafts`.
8. После рестарта контейнеров данные Postgres не теряются.
9. Ошибки логируются.

---

## 21. Что делать владельцу проекта прямо сейчас

### Шаг 1. Создать рабочую папку
```bash
mkdir magnolia-verde-bot
cd magnolia-verde-bot
```

### Шаг 2. Инициализировать git-репозиторий
```bash
git init
```

### Шаг 3. Открыть папку в VS Code
```bash
code .
```

### Шаг 4. Создать базовые файлы
- `README.md`
- `.gitignore`
- `.env.example`
- `docker-compose.yml`
- `Dockerfile`
- `app/`

### Шаг 5. Создать бота в Telegram через BotFather
Нужно получить:
- `BOT_TOKEN`
- username бота

### Шаг 6. Добавить бота в канал администратором
Нужно дать право публиковать сообщения.

### Шаг 7. Подготовить для Codex
Передать этот документ как основной handoff-файл для реализации.

---

## 22. Рекомендации для Codex / разработчика

### Важно
- Не делать webhook в первой версии.
- Не делать микросервисы.
- Не ставить зависимости напрямую на машину пользователя, всё — в Docker.
- Писать код так, чтобы можно было позже заменить mock vision/text service на реальную интеграцию.
- Сразу предусмотреть clean repository structure и миграции.

### Приоритет качества
1. Стабильный happy path.
2. Простота запуска.
3. Чистая архитектура.
4. Расширяемость.
5. Только потом — дополнительные функции.

---

## 23. Желаемый результат первой реализации

После первой реализации должно получиться приложение, которое локально поднимается командой:

```bash
docker compose up --build
```

И позволяет:
- написать боту `/new`;
- отправить фото;
- получить сгенерированный предпросмотр;
- добавить цену;
- опубликовать пост в канал.

Это и есть целевой MVP.
