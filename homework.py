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
# TELEGRAM_CHAT_ID = ''

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


CHECK_VARIABLES = ('Проверьте переменные окружения! PRACTICUM_TOKEN'
                   f'={PRACTICUM_TOKEN} ,'
                   f'TELEGRAM_TOKEN={TELEGRAM_TOKEN},'
                   f'TELEGRAM_CHAT_ID={TELEGRAM_CHAT_ID}')

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


def check_tokens():
    """Проверяет доступность переменных окружения.
    Если отсутствует хотя бы одна переменная окружения выходим.
    """
    # for name in ('PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID'):
    #     if globals()[name]:
    #         print(f'!!!! {globals()[name]}')
    if PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        return True
    else:
        logging.critical(CHECK_VARIABLES.format())
        raise ValueError(CHECK_VARIABLES.format())


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
        raise ConnectionError(f'{CHECK_REQUEST_API}'
                              f'{homework_statuses.status_code}.'
                              f'params={timestamp}')
    return homework_statuses.json()


def check_response(response):
    """Проверяет ответ API на соответствие документации.
    В качестве параметра функция получает ответ API, приведенный
    к типам данных Python.
    """
    if type(response) is not dict:
        raise TypeError(f"{CHECK_TYPES}"
                        f"{type(response['homeworks'])}")

    if 'homeworks' not in response:
        raise TypeError(CHECK_KEYS)
    else:
        if type(response['homeworks']) is not list:
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
    for status_key in HOMEWORK_VERDICTS.keys():
        if (status_key == status):
            return (f'Изменился статус проверки работы '
                    f'"{homework_name}". '
                    f'{HOMEWORK_VERDICTS[status_key]}')


def main():
    """Основная логика работы бота."""
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

    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)

    old_status = None

    # while True:
    try:
        # payload = {'from_date': int(time.time())}
        payload = {'from_date': 0}
        api_answer = get_api_answer(payload)

        if check_response(api_answer):
            homework = api_answer.get('homeworks')[0]
            if old_status != homework['status']:
                message = parse_status(homework)
                send_message(bot, message)

        time.sleep(RETRY_PERIOD)

    except Exception as error:
        message = f'{MESSAGE_ERROR} {error}'
        send_message(bot, message)


if __name__ == '__main__':
    # если перенести while в main() зависает тест
    # tests/test_bot.py::TestHomework::test_main_send_request_to_api
    while True:
        main()
