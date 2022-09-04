import logging
from os import environ
import time
from json import JSONDecodeError
from logging.handlers import RotatingFileHandler

import requests
from notifiers import get_notifier
from notifiers.logging import NotificationHandler
from requests.exceptions import RequestException


ADMIN_CHAT_ID = int(environ['ADMIN_CHAT_ID'])
CHAT_ID = int(environ['CHAT_ID'])
BOT_TOKEN = environ['BOT_TOKEN']
PRAKTIKUM_TOKEN = environ['PRAKTIKUM_TOKEN']
FROM_ADRESS = environ['FROM_ADRESS']
TO_ADRESS = environ['TO_ADRESS']
SMTP_PASS = environ['SMTP_PASS']
API_HW_URL = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'


rotate_file_handler = RotatingFileHandler(
    'log.log',
    maxBytes=5000000,
    backupCount=2,
)
console_out_hundler = logging.StreamHandler()
notification_handler = NotificationHandler(
    'gmail',
    defaults={
        'subject': 'Яндекс.Практикум',
        'from': FROM_ADRESS,
        'to': TO_ADRESS,
        'username': FROM_ADRESS,
        'password': SMTP_PASS,
        'host': 'smtp.gmail.com',
        'port': 587,
        'tls': True,
        'ssl': False,
        'html': False
    }
)
notification_handler.setLevel(logging.ERROR)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(funcName)s: %(message)s',
    handlers=[rotate_file_handler, console_out_hundler, notification_handler],
)

logging.debug('Start script')


gmail = get_notifier('gmail')
telegram = get_notifier('telegram')


def parse_homework_status(homework: dict):
    verdicts = {
        'approved': 'Ревьюеру всё понравилось, можно приступать к следующему уроку.',  # noqa (E501)
        'rejected': 'К сожалению в работе нашлись ошибки.',
        'reviewing': 'Работа взята в ревью.',
    }
    homework_name = homework.get('homework_name', 'Неизвестная работа')
    status = homework.get('status', 'unknown')
    verdict = verdicts.get(status, 'Статус неизвестен.')
    return f'Изменился статус работы "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp: int = 0):
    headers = {
        'Authorization': f'OAuth {PRAKTIKUM_TOKEN}',
    }
    params = {
        'from_date': current_timestamp,
    }
    homework_statuses = requests.get(
        API_HW_URL, headers=headers, params=params
    )
    homework_statuses.raise_for_status()
    return homework_statuses.json()


def send_message(chat_id: int, message: str):
    logging.info(f'Попытка отправки сообщения в Telegram. Текст: {message}')
    msg = telegram.notify(message=message, chat_id=chat_id, token=BOT_TOKEN)
    if msg.status != 'Success':
        error_message = f'Не удалось отправить сообщение:\n\n"{message}"\n\n'\
                        f'Ошибки: {", ".join(msg.errors)}'
        logging.error(error_message)
    else:
        logging.info('Сообщение отправлено.')


def main():
    current_timestamp = int(time.time())
    current_error = None
    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('current_date'):
                current_timestamp = new_homework['current_date']
            if new_homework.get('homeworks'):
                homework = new_homework['homeworks'][0]
                message = parse_homework_status(homework)
                send_message(CHAT_ID, message)
            time.sleep(300)
        except (RequestException, JSONDecodeError) as error:
            logging.warning(repr(error))
            if not type(current_error) == type(error):
                current_error = error
                send_message(ADMIN_CHAT_ID, repr(error))
            time.sleep(30)


if __name__ == '__main__':
    main()
