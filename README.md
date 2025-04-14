# 🟣 WBAuthTray — Wildberries Auth Tray App for macOS

Приложение в системный трей (macOS), которое автоматически получает и копирует коды подтверждения из личного кабинета Wildberries.

---

## 🚀 Возможности

- 🔄 Фоновый опрос Wildberries API на предмет новых сообщений
- 🔔 Системные уведомления при получении кода
- 📋 Автоматическое копирование кода в буфер обмена

---

## 📦 Установка

```bash
uv sync
touch .venv/lib/python3.13/site-packages/rubicon/__init__.py
uv run python setup.py py2app
```