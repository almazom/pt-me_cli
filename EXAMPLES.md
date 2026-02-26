# Примеры использования pt-me

## Базовое использование

```bash
# Опубликовать файл и отправить уведомление
pt-me article.md

# Опубликовать с указанием провайдера
pt-me article.md -sn          # Только Simplenote
pt-me article.md -vps         # Только VPS
pt-me article.md -sn -vps     # Оба провайдера
```

## Работа с разными типами входа

```bash
# Из файла
pt-me document.md

# Из stdin
cat document.md | pt-me -

# Из URL (если поддерживается)
pt-me https://example.com/article.md
```

## Настройка Telegram уведомления

```bash
# Без уведомления
pt-me article.md --no-notify

# С кастомным комментарием
pt-me article.md --caption "📖 Новая статья про CLI"

# С AI-суммаризацией
pt-me article.md --summary

# С выбором шаблона
pt-me article.md --template minimal    # Минимальный
pt-me article.md --template standard   # Стандартный
pt-me article.md --template detailed   # Развернутый
```

## Режимы вывода

```bash
# Обычный вывод
pt-me article.md -v

# JSON вывод (для автоматизации)
pt-me article.md -j

# Тихий режим (только ошибки)
pt-me article.md --quiet

# Dry run (без реальной публикации)
pt-me article.md -n
```

## Примеры JSON вывода

### Успешная публикация
```json
{
  "ok": true,
  "pipeline": "pt-me",
  "version": "1.0.0",
  "correlation_id": "pt-abc123",
  "stages": {
    "input": {
      "type": "text",
      "mime_type": "text/markdown",
      "size_bytes": 1024
    },
    "publish": {
      "ok": true,
      "url": "https://simp.ly/p/XYZ",
      "provider": "simplenote"
    },
    "notify": {
      "ok": true,
      "message_id": 12345,
      "target": "@almazom"
    }
  }
}
```

### Ошибка
```json
{
  "ok": false,
  "pipeline": "pt-me",
  "correlation_id": "pt-abc123",
  "stages": {
    "input": {...},
    "publish": {
      "ok": false,
      "errors": ["File not found"]
    },
    "notify": {"skipped": true}
  },
  "errors": ["File not found"]
}
```

## Сценарии использования

### 1. Публикация заметок
```bash
# Быстрая заметка
echo "# Заметка\n\nТекст заметки" | pt-me - -sn

# С уведомлением
pt-me note.md --caption "📝 Заметка" --template minimal
```

### 2. Публикация статей
```bash
# Статья с суммаризацией
pt-me article.md --summary --caption "📖 Новая статья"

# С обоими провайдерами
pt-me article.md -sn -vps --summary
```

### 3. Автоматизация (CI/CD)
```bash
# В скрипте
if pt-me release-notes.md -j --no-notify | jq -e '.ok'; then
    echo "Published successfully"
else
    echo "Publication failed"
    exit 1
fi
```

### 4. Конвейерная обработка
```bash
# Генерация и публикация
generate-report.sh | pt-me - -sn --caption "📊 Отчёт"

# С фильтрацией
cat draft.md | preprocess.sh | pt-me - -sn
```

## Выходные коды

| Код | Описание |
|-----|----------|
| 0   | Успех |
| 1   | Ошибка валидации |
| 2   | Ошибка сети |
| 3   | Неизвестная ошибка |

## Проверка здоровья

```bash
# Проверка доступности зависимостей
pt-me --health-check
```

Вывод:
```
Running health check...
  p-me: ✓
  t2me: ✓
Health check: OK
```

## Шаблоны сообщений

### standard (по умолчанию)
```
{caption}

📌 Кратко:
1️⃣ {summary_point_1}
2️⃣ {summary_point_2}
3️⃣ {summary_point_3}

🔗 {url}

#published #pt-me
```

### minimal
```
{caption}
🔗 {url}
```

### detailed
```
{caption}

📄 Источник: {source_name}
📊 Тип: {source_type}
📌 Провайдер: {provider}

📌 Кратко:
{summary_points}

🔗 {url}

#published #pt-me
```

## Переменные окружения

```bash
# Путь к проекту
export PT_ME_PROJECT_DIR=/home/pets/TOOLS/pt-me_cli

# Python бинарник
export PT_ME_PYTHON_BIN=python3
```
