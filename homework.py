import logging
import os
import time
import sys

from dotenv import load_dotenv
import requests
import telegram

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# TELEGRAM_TOKEN = ''
# TELEGRAM_CHAT_ID = ''

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

VARIABLES = ('PRACTICUM_TOKEN',
             'TELEGRAM_TOKEN',
             'TELEGRAM_CHAT_ID')

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


CHECK_VARIABLES = 'Проверьте переменные окружения! {name}.'
SEND_MESSAGE_OK = 'Удачная отправка сообщения в Telegram: {value}'
SEND_MESSAGE_FAIL = 'Ошибка при отправке сообщения в Telegram: {value}.{error}'
CHECK_REQUEST_API = ('Ошибка при запросе к API: {endpoint}, {headers}, {name},'
                     ' {value}. {dt}. {error}')
CHECK_TYPES = 'В ответе API тип данных {type} не соответствует {value}.'
CHECK_KEYS = 'В ответе API нет ключа {value}.'
CHECK_HOMEWORK_STATUS = ('В ответе API не содержится статус домашней работы:'
                         '{value}.')
CHECK_HOMEWORK_NAME = ('В ответе функции `parse_status`'
                       'не содержится название домашней работы.')
CHANGE_STATUS = 'Изменился статус проверки работы "{name}". {value}'


def check_tokens():
    """Проверяет доступность переменных окружения.
    Если отсутствует хотя бы одна переменная окружения выходим.
    """
    for name in VARIABLES:
        if not globals()[name]:
            logging.critical(CHECK_VARIABLES.format(name=name))
            raise ValueError(CHECK_VARIABLES.format(name=name))


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат TELEGRAM_CHAT_ID.
    Принимает на вход два параметра: экземпляр класса
    Bot и строку с текстом сообщения.
    """
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message
        )
        logging.debug(SEND_MESSAGE_OK.format(value=message))
    except Exception as error:
        logging.error(SEND_MESSAGE_FAIL.format(
            value=message, error=error), exc_info=True)


def get_api_answer(timestamp):
    """Делает запрос к  эндпоинту API-сервиса.
    В качестве параметра в функцию передается временная метка.
    В случае успешного запроса должна вернуть ответ API, приведя его
    из формата JSON к типам данных Python.
    """
    timestamp = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(
            ENDPOINT, headers=HEADERS, params=timestamp
        )

    except requests.RequestException as error:
        raise ConnectionError(CHECK_REQUEST_API.format(
            endpoint=ENDPOINT, headers=HEADERS, value=timestamp, error=error))

    if homework_statuses.status_code != 200:
        raise ValueError(CHECK_REQUEST_API.format(
            endpoint=ENDPOINT, name='', value='',
            error=homework_statuses.status_code,
            headers=HEADERS, dt=timestamp))
    result = homework_statuses.json()
    print(f'!!!!!!!!!!{result}')
    if result.get('code') or result.get('error'):
        raise ValueError(CHECK_REQUEST_API.format(
            endpoint=ENDPOINT, name='result',
            value='result', headers=HEADERS, dt=timestamp))
    return result


def check_response(response):
    """Проверяет ответ API на соответствие документации.
    В качестве параметра функция получает ответ API, приведенный
    к типам данных Python.
    """
    if not isinstance(response, dict):
        raise TypeError(CHECK_TYPES.format(type=type(response), value='dict'))

    if 'homeworks' not in response:
        raise TypeError(CHECK_KEYS.format(value='homeworks'))

    if not isinstance(response['homeworks'], list):
        raise TypeError(CHECK_TYPES.format(
            type=type(response['homeworks']), value='list'))


def parse_status(homework):
    """Извлекает из информации о конкретной домашней работе статус этой работы.
    В качестве параметра функция получает только один элемент из списка
    домашних работ. В случае успеха, функция возвращает подготовленную
    для отправки в Telegram строку, содержащую один из вердиктов
    словаря HOMEWORK_VERDICTS.
    """
    homework_name = homework.get('homework_name')
    status = homework.get('status')

    if not homework_name:
        raise ValueError(CHECK_HOMEWORK_NAME)

    if status not in HOMEWORK_VERDICTS:
        raise ValueError(CHECK_HOMEWORK_STATUS.format(value=status))

    return (CHANGE_STATUS.format(
            name=homework_name, value=HOMEWORK_VERDICTS[status]))


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)

    old_status = None
    timestamp = 0
    # timestamp = {'from_date': int(time.time())}

    while True:
        try:
            api_answer = get_api_answer(timestamp)

            check_response(api_answer)
            if api_answer.get('homeworks'):
                homework = api_answer.get('homeworks')[0]
                if old_status != homework['status']:
                    message = parse_status(homework)
                    send_message(bot, message)

            time.sleep(RETRY_PERIOD)

        except Exception as error:
            message = CHECK_REQUEST_API.format(
                endpoint=ENDPOINT, name='', value='', headers=HEADERS,
                dt=timestamp, error=error)
            logging.error(message)
            time.sleep(RETRY_PERIOD)
            send_message(bot, message)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(funcName)s %(message)s',
        handlers=[logging.FileHandler(
            __file__ + '.log',
            mode='w'
        ), logging.StreamHandler(sys.stdout)]
    )
    main()
