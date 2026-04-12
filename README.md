# Magnolia Verde Telegram Bot MVP Starter

Стартовый skeleton для MVP Telegram-бота бутика «Магнолия Верде».

## Что внутри
- Python 3.11
- aiogram 3.x
- PostgreSQL 16
- Redis 7
- Docker Compose
- polling режим для локальной разработки

## Быстрый старт
1. Скопируйте `.env.example` в `.env`
2. Заполните `BOT_TOKEN`, `ALLOWED_USER_IDS`, `DEFAULT_CHANNEL_ID`
3. Запустите:
   ```bash
   docker compose up --build
   ```
4. Напишите боту `/start`

## Что уже умеет skeleton
- `/start`
- `/new`
- `/cancel`
- Принимает фото
- Делает заглушку-"распознавание"
- Генерирует черновик подписи
- Показывает preview
- По кнопке публикует фото в канал

## Важно
- Бот должен быть администратором канала с правом публикации.
- `DEFAULT_CHANNEL_ID` для канала обычно имеет вид `-100xxxxxxxxxx`.
- `ALLOWED_USER_IDS` — Telegram user id сотрудников, которым можно пользоваться ботом.

## Следующие шаги
- заменить mock vision/text generation на реальную интеграцию
- подключить PostgreSQL/Redis в коде
- добавить черновики и FSM
- добавить логирование и аудит
