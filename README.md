# pt-me CLI

Publish + Telegram Notify — комбинированный инструмент для публикации контента и отправки уведомлений.

## Установка

```bash
pip install -e .
```

## Использование

```bash
# Базовый: опубликовать файл + отправить уведомление
pt-me article.md

# С указанием провайдера
pt-me article.md -sn          # Simplenote
pt-me article.md -vps         # VPS
pt-me article.md -sn -vps     # Оба

# С кастомным комментарием
pt-me article.md --caption "📖 Новая статья"

# Без уведомления
pt-me article.md --no-notify

# Из stdin
cat article.md | pt-me -

# Dry run
pt-me article.md -n -v

# JSON вывод
pt-me article.md -j
```

## Выходные коды

- `0` — успех
- `1` — ошибка валидации
- `2` — ошибка сети
- `3` — неизвестная ошибка

## Архитектура

```
pt-me → input → processor → notifier
         ↓        ↓           ↓
       файл    p-me        t2me
       URL     (publish)   (send)
       stdin
```

## Ценности (Colony Values)

- **simplicity** — одна команда для публикации + уведомления
- **observability** — полные логи с correlation_id
- **ai_first** — JSON вывод для автоматизации
- **graceful_degradation** — работает при частичных сбоях
