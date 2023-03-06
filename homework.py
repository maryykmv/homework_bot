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


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


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
        logging.critical(f'Проверьте переменные окружения! PRACTICUM_TOKEN'
                         f'={PRACTICUM_TOKEN} ,'
                         f'TELEGRAM_TOKEN={TELEGRAM_TOKEN},'
                         f'TELEGRAM_CHAT_ID={TELEGRAM_CHAT_ID}')
        raise ValueError('Проверьте переменные окружения! PRACTICUM_TOKEN,'
                         'TELEGRAM_TOKEN, TELEGRAM_CHAT_ID')


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
        logging.debug(f'Удачная отправка сообщения в Telegram: {message}')
    except Exception as error:
        logging.error(f'Ошибка при отправке сообщения в Telegram: '
                      f'{message}. {error}', exc_info=True)


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

        if homework_statuses.status_code != 200:
            raise ConnectionError(f'Код ошибки при запросе к API: '
                                  f'{homework_statuses.status_code}.'
                                  f'ENDPOINT={ENDPOINT}, headers={HEADERS},'
                                  f'params={timestamp}')
        return homework_statuses.json()
    except requests.RequestException as error:
        raise ConnectionError(f'Ошибка при запросе к API: {error}.'
                              f'ENDPOINT={ENDPOINT}, headers={HEADERS},'
                              f'params={timestamp}')


def check_response(response):
    """Проверяет ответ API на соответствие документации.
    В качестве параметра функция получает ответ API, приведенный
    к типам данных Python.
    """

    if 'homeworks' not in response:
        raise TypeError('В ответе API домашки нет ключа `homeworks`.')
    else:
        if type(response['homeworks']) is not list:
            raise TypeError(f"В ответе API тип данных не"
                            f"соответствует словарю. "
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

    try:
        for status_key in HOMEWORK_VERDICTS.keys():
            print(status_key)
            if not type(status_key) is str:
                logging.error(f'Функция `parse_status` возвращает не строку: '
                              f'{type(status_key)}')
                raise TypeError(f'Функция `parse_status` возвращает '
                                f'не строку: {type(status_key)}')

            if not homework_name:
                raise ValueError(f'В ответе функции `parse_status` '
                                 f'не содержится название домашней работы: '
                                 f'{homework_name}')

            if status not in HOMEWORK_VERDICTS.keys():
                raise ValueError(f'В ответе API не содержится '
                                 f'статуса домашней работы = '
                                 f'{homework_name}')

            if (status_key == status):
                return (f'Изменился статус проверки работы '
                        f'"{homework_name}". '
                        f'{HOMEWORK_VERDICTS[status_key]}')
    except KeyError as error:
        logging.error(f'Неожиданный статус домашней работы, в ответе API: '
                      f'{error}')


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
    old_message = None

    while True:
        try:
            # payload = {'from_date': int(time.time())}
            payload = {'from_date': 0}
            api_answer = get_api_answer(payload)

            if check_response(api_answer):
                if api_answer.get('homeworks')[0]['homework_name'] == 'wildcat3333__homework_bot.zip':
                    homework = api_answer.get('homeworks')[0]

                    if old_status is None:
                        print(old_status)
                        print(parse_status(homework))
                        message = parse_status(homework)
                        send_message(bot, message)
                        old_status = homework['status']

                    if old_status != homework['status']:
                        message = parse_status(homework)
                        send_message(bot, message)

            time.sleep(RETRY_PERIOD)

        except requests.RequestException as error:
            message = f'Сбой в работе программы: {error}'

            if old_message is None:
                send_message(bot, message)
                old_message = message

            if old_message != message:
                old_message = message
                send_message(bot, message)


if __name__ == '__main__':
    main()
