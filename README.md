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

Вместо `YOUR TOKEN` вставьте свой токен с [BotFather](https://t.me/BotFather)

Также создайте в корне проекта папку `media`

---

**Запуск**

```
python main.py
```
