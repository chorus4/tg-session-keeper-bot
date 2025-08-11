# Telegram session keeper bot

Бот для хранения сессий в телеграмме

---

## Подготовка и запуск

```
git clone https://github.com/chorus4/tg-session-keeper-bot.git
```

**Создание виртуального окружения**

```
python -m venv .venv
```

Активация виртуального окружения

```
.\.venv\Scripts\activate
```

**Установка зависимостей**

```
pip install -r requirements.txt
```


**Конфигурация**

_Переименуйте файл .env.example на .env_

В `BOT_TOKEN` вставьте свой токен с [BotFather](https://t.me/BotFather)

В `API_ID` вставьте API_ID который нужно создать в [Telegram API Portal](https://my.telegram.org/apps)

В `API_HASH` вставьте API_HASH который нужно создать в [Telegram API Portal](https://my.telegram.org/apps)

---

**Запуск**

```
python main.py
```
