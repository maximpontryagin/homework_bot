from http import HTTPStatus
import requests
import os
import logging
import sys
import time

from telegram import Bot
from dotenv import load_dotenv
from exceptions import MissingKyes, ServerStatusNotOK
from logging.handlers import RotatingFileHandler


PRACTICUM_TOKEN: str = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN: str = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID: str = os.getenv('TELEGRAM_CHAT_ID')
RETRY_PERIOD: int = 600
ENDPOINT: str = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS: str = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
RESPONSE_KEY_HOMEWORKS: str = 'homeworks'
RESPONSE_KEY_CURRENT_DATA: str = 'current_date'
HOMEWORK_VERDICTS: dict = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

load_dotenv()


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler(
    'my_logger.log', maxBytes=50000000, backupCount=5)
logger.addHandler(logging.StreamHandler(sys.stdout))


def check_tokens():
    """Проверка токенов."""
    return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    try:
        logger.info('Началась отправка сообещния в telegram')
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug('Сообщение отправлено')
    except requests.RequestException as error:
        logger.error(f'Сообщение не отправлено, ошибка {error}')


def get_api_answer(timestamp):
    """Делаем GET-запрос к эндпоинту url."""
    try:
        response = requests.get(ENDPOINT, headers=HEADERS,
                                params=timestamp)
    except requests.RequestException as error:
        raise ConnectionError(f'Ошикабка {error}')
    if response.status_code is not HTTPStatus.OK:
        raise ServerStatusNotOK('API возвращает код, отличный от 200.')
    return response.json()


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    logger.info('Начата проверка ответа API на соответсвие документации')
    if ((RESPONSE_KEY_HOMEWORKS or RESPONSE_KEY_CURRENT_DATA)
        not in list(response)
        or not isinstance(response.get(RESPONSE_KEY_HOMEWORKS), list)
            or not isinstance(response.get(RESPONSE_KEY_HOMEWORKS)[0], dict)):
        raise TypeError(
            'ответ API несоотвествует документации Яндекса')
    homeworks = response.get(RESPONSE_KEY_HOMEWORKS)
    return homeworks


def parse_status(homework):
    """Извлечение статуса работы."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_name is None:
        raise KeyError(f'Отсуствует домашняя работа {homework_name}')
    elif homework_status not in list(HOMEWORK_VERDICTS):
        raise KeyError(f'Отсуствует статус домашней работы {homework_name}')
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    if check_tokens() is False:
        logger.critical('Отсутствуют обязательные переменные окружения')
        raise MissingKyes
    bot = Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    last_message = ''
    logger.debug('Успешная отправка сообщения')
    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            message = parse_status(homeworks[0])
            send_message(bot, message)
            last_message = message
            timestamp = response.get(RESPONSE_KEY_CURRENT_DATA)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            if message != last_message:
                send_message(bot, message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        filename='main.log',
        filemode='w',
        encoding='utf-8',
        format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
    )
    main()
