from dotenv import load_dotenv
import os
import requests
import time
from telegram import Bot



load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
PAYLOAD = {'from_date': 0}
HOMEWORK = 'wildcat3333__hw05_final.zip'


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверяет доступность переменных окружения.
    Если отсутствует хотя бы одна переменная окружения выходим."""
    if PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        return True


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат, определяемый переменной окружения
    TELEGRAM_CHAT_ID. Принимает на вход два параметра: экземпляр класса
    Bot и строку с текстом сообщения."""
    bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text=message
    )


def get_api_answer(timestamp):
    """Делает запрос к  эндпоинту API-сервиса. В качестве параметра в функцию
    передается временная метка.
    В случае успешного запроса должна вернуть ответ API, приведя его
    из формата JSON к типам данных Python."""
    homework_statuses = requests.get(
        ENDPOINT, headers=HEADERS, params=timestamp
    )
    return homework_statuses.json()


def check_response(response):
    """Проверяет ответ API на соответствие документации. В качестве параметра
    функция получает ответ API, приведенный к типам данных Python."""
    if response.get('homeworks') and response.get('homeworks'):
        return True


def parse_status(homework):
    """Извлекает из информации о конкретной домашней работе статус этой работы.
    В качестве параметра функция получает только один элемент из списка
    домашних работ. В случае успеха, функция возвращает подготовленную
    для отправки в Telegram строку, содержащую один из вердиктов
    словаря HOMEWORK_VERDICTS."""
    homework_name = homework.get('homework_name')
    status = homework.get('status')
    for key in HOMEWORK_VERDICTS:
        if key == status:
            verdict = HOMEWORK_VERDICTS[key]
            return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if check_tokens():
        asnwer_api = get_api_answer(PAYLOAD)
        # print(asnwer_api)

        check_resp = check_response(asnwer_api)
        # print(check_resp)

        # print(asnwer_api.get('homeworks')[0]['homework_name'])

        if asnwer_api.get('homeworks')[0]['homework_name'] == HOMEWORK:
            homework = asnwer_api.get('homeworks')[0]

        # print(homework)
        # parser_st = parse_status(homework)
        # print(parser_st)

        bot = Bot(token=TELEGRAM_TOKEN)
        message = parse_status(homework)
        send_message(bot, message)

        # timestamp = int(time.time())

    #     ...

    #     while True:
    #         try:

    #             ...

    #         except Exception as error:
    #             message = f'Сбой в работе программы: {error}'
    #             ...
    #         ...


if __name__ == '__main__':
    main()
