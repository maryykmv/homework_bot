# Проект Telegram-бот
«Проект Telegram-бот»

## Оглавление
1. [Описание](#описание)
2. [Технологии](#технологии)
3. [Как запустить проект](#как-запустить-проект)
4. [Автор проекта](#автор-проекта)

## Описание
Telegram-бот, который обращатся к API сервиса Практикум.Домашка и узнает статус домашней работы: взята ли ваша домашка в ревью, проверена ли она, а если проверена — то принял её ревьюер или вернул на доработку.

Ключевые возможности сервиса:
- раз в 10 минут опрашивает API сервис Практикум.Домашка и проверяет статус отправленной на ревью домашней работы;
- при обновлении статуса анализирует ответ API и отправляет вам соответствующее уведомление в Telegram;
- логирует свою работу и сообщает вам о важных проблемах сообщением в Telegram.

## Технологии
- Python 3.9
- библиотека telegram

## Как запустить проект

- Клонировать репозиторий и перейти в него в командной строке:
```
git clone git@github.com:maryykmv/homework_bot.git
```
- Переходим в директорию проекта:
```
cd homework_bot
```

- Создаем и активируем виртуальное окружение:
```
python3 -m venv venv
```
* Если у вас Linux/macOS:
    ```
    source venv/bin/activate
    ```

* Если у вас windows:
    ```
    source venv/scripts/activate
    ```

- Пример заполнения конфигурационного .env файла
```
TELEGRAM_TOKEN=xxxxxx
PRACTICUM_TOKEN=xxxxxxxxx
TELEGRAM_CHAT_ID=xxxxxxxx
```
PRACTICUM_TOKEN для доступа к Домашке получаем по ссылке https://oauth.yandex.ru/authorize?response_type=token&client_id=1d0b9dd4d652455a9eb710d450ff456a
TELEGRAM_TOKEN  @BotFather зарегистрировать аккаунт бота в Telegram и получить Token
TELEGRAM_CHAT_ID  @userinfobot - узнать ID своего Telegram-аккаунта


- Обновляем менеджер пакетов pip:
```
pip install --upgrade pip
```

- Устанавливаем зависимости из файла requirements.txt:
```
pip install -r requirements.txt
```

- Запустить проект
```
python homework.py
```


## Автор проекта
_[Мария Константинова](https://github.com/maryykmv/)_, python-developer
