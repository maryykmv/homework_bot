from dotenv import load_dotenv
import logging
import os
import requests
import time
import telegram
from threading import Timer


load_dotenv()
# Глобальная конфигурация для всех
logging.basicConfig(
    level=logging.DEBUG,
    filename='program.log',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)

# # А тут установлены настройки логгера для текущего файла - example_for_log.py
# logger = logging.getLogger(__name__)
# # Устанавливаем уровень, с которого логи будут сохраняться в файл
# logger.setLevel(logging.INFO)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
TELEGRAM_CHAT_ID = '463435736'

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
    else:
        logging.critical('Проверьте переменные окружения! PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID')


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат, определяемый переменной окружения
    TELEGRAM_CHAT_ID. Принимает на вход два параметра: экземпляр класса
    Bot и строку с текстом сообщения."""

    try:
        result = bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message
        )
        logging.debug(f'Удачная отправка сообщения в Telegram: {result}')
    except Exception as error:
        logging.error(f'Ошибка при отправке сообщения в Telegram: {error}')


def get_api_answer(timestamp):
    """Делает запрос к  эндпоинту API-сервиса. В качестве параметра в функцию
    передается временная метка.
    В случае успешного запроса должна вернуть ответ API, приведя его
    из формата JSON к типам данных Python."""
    try:
        homework_statuses = requests.get(
            ENDPOINT, headers=HEADERS, params=timestamp
        )
        
        if homework_statuses.status_code != 200:
            raise Exception(f'Код ошибки при запросе к API: {homework_statuses.status_code}')
        return homework_statuses.json()
    except requests.RequestException as error:
        logging.error(f'Ошибка при запросе к API: {error}')


def check_response(response):
    """Проверяет ответ API на соответствие документации. В качестве параметра
    функция получает ответ API, приведенный к типам данных Python."""
    try:
        if 'homeworks' not in response:
            logging.error(f'В ответе API домашки нет ключа `homeworks`.')
            raise TypeError(f'В ответе API домашки нет ключа `homeworks`.')

        if type(response['homeworks']) is not list:
            logging.error(f'В ответе API тип данных не соответствует ожиданиям.')
            raise TypeError(f'В ответе API тип данных не соответствует ожиданиям.')

        if 'homeworks' in response:
            return True

    except KeyError as error:
        # print(error)
        logging.error(f'Отсутствует ключ homeworks в ответе API: {error}')


def parse_status(homework):
    """Извлекает из информации о конкретной домашней работе статус этой работы.
    В качестве параметра функция получает только один элемент из списка
    домашних работ. В случае успеха, функция возвращает подготовленную
    для отправки в Telegram строку, содержащую один из вердиктов
    словаря HOMEWORK_VERDICTS."""
    homework_name = homework.get('homework_name')
    status = homework.get('status')
    # old_status = status

    try:
        for status_key in HOMEWORK_VERDICTS.keys():
            # old_status = status
            if not type(status_key) is str:
                raise logging.error(f'Функция `parse_status` возвращает не строку: {type(status_key)}')

            if not homework_name:
                raise logging.error(f'В ответе функции `parse_status` не содержится название домашней работы: {homework_name}')

            if status not in HOMEWORK_VERDICTS.keys():
                raise logging.error(f'В ответе функции `parse_status` не содержится название домашней работы: {homework_name}')

            if (status_key == status):# and (old_status != status) and (old_status in HOMEWORK_VERDICTS.keys()):
                verdict = HOMEWORK_VERDICTS[status_key]
                message = f'Изменился статус проверки работы "{homework_name}". {verdict}'
                return message
    except KeyError as error:
        logging.error(f'Неожиданный статус домашней работы, в ответе API: {error}')


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    try:
        if check_tokens():
            # timestamp = int(time.time())
            # PAYLOAD = {'from_date': timestamp}
            # print(timestamp)
            api_answer = get_api_answer(PAYLOAD)
            # print(api_answer)
            # print(type(api_answer))
            # print(list(api_answer))

            if check_response(list(api_answer)):
                if api_answer.get('homeworks')[0]['homework_name'] == HOMEWORK:
                    homework = api_answer.get('homeworks')[0]

                    print(homework)

                    message = parse_status(homework)
                    # send_message(bot, message)

                time.sleep(RETRY_PERIOD)
    except Exception as error:
        message = f'Сбой в работе программы: {error}'
        logging.critical(error)
    # while True:
    #     try:

    #        ...

    #     except Exception as error:
    #         message = f'Сбой в работе программы: {error}'
    #         ...
    #     ...


if __name__ == '__main__':
    main()
