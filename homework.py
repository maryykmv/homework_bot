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


CHECK_VARIABLES = (f'Проверьте переменные окружения! {VARIABLES}')

CHECK_TYPES = 'В ответе API тип данных не соответствует словарю.'
CHECK_REQUEST_API = (f'Ошибка при запросе к API: '
                     f'ENDPOINT={ENDPOINT}, headers={HEADERS},')
CHECK_KEYS = 'В ответе API нет ключа `homeworks`.'
CHECK_HOMEWORK_NAME = ('В ответе функции `parse_status`'
                       'не содержится название домашней работы: ')
CHECK_HOMEWORK_STATUS = ('В ответе API не содержится статус домашней работы: ')
CHANGE_STATUS = 'Изменился статус проверки домашней работы: '
SEND_MESSAGE_OK = 'Удачная отправка сообщения в Telegram: '
SEND_MESSAGE_FAIL = 'Ошибка при отправке сообщения в Telegram: '
MESSAGE_ERROR = 'Сбой в работе программы: '
CHECK_STATUS_CODE = 'Недопустимый код ответа API 403,404,503,502...'
CHECK_CONNECT = 'Проблема с сетью (сбой DNS, отказ соединения)'


def check_tokens():
    """Проверяет доступность переменных окружения.
    Если отсутствует хотя бы одна переменная окружения выходим.
    """
    for name in VARIABLES:
        if not globals()[name]:
            logging.critical(globals()[name])
            raise ValueError(CHECK_VARIABLES)


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
        logging.debug(f'{SEND_MESSAGE_OK} {message}')
    except Exception as error:
        logging.error(f'{SEND_MESSAGE_FAIL} {message}. {error}', exc_info=True)


def get_api_answer(timestamp):
    """Делает запрос к  эндпоинту API-сервиса.
    В качестве параметра в функцию передается временная метка.
    В случае успешного запроса должна вернуть ответ API, приведя его
    из формата JSON к типам данных Python.
    """
    try:
        homework_statuses = requests.get(
            ENDPOINT, headers=HEADERS, params=timestamp
        )
    except requests.RequestException as error:
        raise ConnectionError(f'{CHECK_REQUEST_API}'
                              f'params={timestamp}. {error}.')

    if homework_statuses.status_code != 200:
        raise ValueError(f'{CHECK_REQUEST_API}'
                         f'{homework_statuses.status_code}.'
                         f'params={timestamp}')
    if ('code', 'error') in homework_statuses.json():
        raise ValueError(f'{homework_statuses.json()}')
    return homework_statuses.json()


def check_response(response):
    """Проверяет ответ API на соответствие документации.
    В качестве параметра функция получает ответ API, приведенный
    к типам данных Python.
    """
    if not isinstance(response, dict):
        raise TypeError(f"{CHECK_TYPES}"
                        f"{type(response)}")

    if 'homeworks' not in response:
        raise TypeError(CHECK_KEYS)

    if not isinstance(response['homeworks'], list):
        raise TypeError(f"{CHECK_TYPES}"
                        f"{type(response['homeworks'])}")
    return True


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
        raise ValueError(f'{CHECK_HOMEWORK_NAME}'
                         f'{homework_name}')

    if status not in HOMEWORK_VERDICTS.keys():
        raise ValueError(f'{CHECK_HOMEWORK_STATUS}'
                         f'{homework_name}')
    if HOMEWORK_VERDICTS[status]:
        return (f'Изменился статус проверки работы '
                f'"{homework_name}". '
                f'{HOMEWORK_VERDICTS[status]}')


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)

    old_status = None
    timestamp = {'from_date': 0}

    # while True:
    try:
        api_answer = get_api_answer(timestamp)

        check_response(api_answer)
        homework = api_answer.get('homeworks')[0]
        if old_status != homework['status']:
            message = parse_status(homework)
            send_message(bot, message)

        time.sleep(RETRY_PERIOD)

    except Exception as error:
        message = f'{CHECK_REQUEST_API} {error}'


if __name__ == '__main__':
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.DEBUG)

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(message)s %(funcName)s',
        handlers=[logging.FileHandler(
            __file__ + '.log',
            mode='w'
        ), stream_handler]
    )
    # если перенести while в main() зависает тест
    # tests/test_bot.py::TestHomework::test_main_send_request_to_api
    while True:
        main()
