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


CHECK_VARIABLES = 'Проверьте переменные окружения! {name}.'
SEND_MESSAGE_OK = 'Удачная отправка сообщения в Telegram: {value}'
SEND_MESSAGE_FAIL = 'Ошибка при отправке сообщения в Telegram: {value}.{error}'
CHECK_REQUEST_API = ('Ошибка при запросе к API: {url}, {headers}, {value}'
                     '. {params}. {error}')
CHECK_CODE_REQUEST_API = ('Код ошибки при запросе к API: {url}, {headers}'
                          ', {value}. {params}.')
CHECK_RESPONSE_API = ('Ошибка в ответе API: {url}, {headers}, {name}: '
                      ' {value}. {params}.')
CHECK_TYPE_DICT = ('В ответе API тип данных  {type} {value}'
                   'не соответствует словарю (dict).')
CHECK_TYPE_LIST = ('В ответе API тип данных {type} {value}'
                   'не соответствует списку list().')
CHECK_KEYS = 'В ответе API нет ключа {value}.'
CHECK_HOMEWORK_STATUS = ('В ответе API не содержится статус домашней работы:'
                         '{value}.')
CHECK_HOMEWORK_NAME = ('В ответе функции `parse_status`'
                       'не содержится название домашней работы.')
CHANGE_STATUS = 'Изменился статус проверки работы "{name}". {value}'
MESSAGE_ERRORS = 'Произошел сбой: {error}'


def check_tokens():
    """Проверяет доступность переменных окружения.
    Если отсутствует хотя бы одна переменная окружения выходим.
    """
    results = [name for name in VARIABLES if not globals()[name]]
    if results:
        logging.critical(CHECK_VARIABLES.format(name=results))
        raise ValueError(CHECK_VARIABLES.format(name=results))


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
        return True
    except Exception as error:
        logging.exception(SEND_MESSAGE_FAIL.format(
            value=message, error=error))
        return False


def get_api_answer(timestamp):
    """Делает запрос к  эндпоинту API-сервиса.
    В качестве параметра в функцию передается временная метка.
    В случае успешного запроса должна вернуть ответ API, приведя его
    из формата JSON к типам данных Python.
    """
    request_parameters = dict(
        url=ENDPOINT, headers=HEADERS, params={'from_date': timestamp})
    try:
        homework_statuses = requests.get(**request_parameters)
    except requests.RequestException as error:
        raise ConnectionError(CHECK_REQUEST_API.format(
            **request_parameters, error=error))
    if homework_statuses.status_code != 200:
        raise ValueError(CHECK_CODE_REQUEST_API.format(
            **request_parameters, value=homework_statuses.status_code))
    result = homework_statuses.json()
    for key in ['code', 'error']:
        if key in result:
            raise ValueError(CHECK_RESPONSE_API.format(
                **request_parameters, name=key, value=result[key]))
    return result


def check_response(response):
    """Проверяет ответ API на соответствие документации.
    В качестве параметра функция получает ответ API, приведенный
    к типам данных Python.
    """
    if not isinstance(response, dict):
        raise TypeError(CHECK_TYPE_DICT.format(
            type=type(response), value=response))
    if 'homeworks' not in response:
        raise TypeError(CHECK_KEYS.format(value='homeworks'))
    data = response['homeworks']
    if not isinstance(data, list):
        raise TypeError(CHECK_TYPE_LIST.format(
            type=type(data), value=data))


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
        raise KeyError(CHECK_HOMEWORK_NAME)
    if status not in HOMEWORK_VERDICTS:
        raise ValueError(CHECK_HOMEWORK_STATUS.format(value=status))
    return CHANGE_STATUS.format(
        name=homework_name, value=HOMEWORK_VERDICTS[status])


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)

    old_status = None
    old_message = None
    timestamp = int(time.time())
    while True:
        try:
            api_answer = get_api_answer(timestamp)
            check_response(api_answer)
            homeworks = api_answer.get('homeworks')
            new_timestamp = api_answer.get('current_date', timestamp)
            if homeworks:
                homework = homeworks[0]
                if (old_status != homework['status']
                   and send_message(bot, parse_status(homework))):
                    old_status = homeworks[0]['status']
                    timestamp = new_timestamp
        except Exception as error:
            message = MESSAGE_ERRORS.format(error=error)
            logging.exception(message)
            if old_message != message and send_message(bot, message):
                old_message = message
        time.sleep(RETRY_PERIOD)


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
