import logging
from os import environ
import time
from email.errors import MessageError
from email.message import EmailMessage
from json import JSONDecodeError
from logging.handlers import RotatingFileHandler
from smtplib import SMTP

import requests
from requests.exceptions import RequestException


rotate_file_handler = RotatingFileHandler(
    'log.log',
    maxBytes=5000000,
    backupCount=2,
)
console_out_hundler = logging.StreamHandler()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(funcName)s: %(message)s',
    handlers=[rotate_file_handler, console_out_hundler],
)

logging.debug('Start script')


ADMIN_CHAT_ID = int(environ['ADMIN_CHAT_ID'])
CHAT_ID = int(environ['CHAT_ID'])
TELEGRAM_TOKEN = environ['TELEGRAM_TOKEN']
PRAKTIKUM_TOKEN = environ['PRAKTIKUM_TOKEN']
FROM_ADRESS = environ['FROM_ADRESS']
TO_ADRESS = environ['TO_ADRESS']
SMTP_LOGIN = environ['SMTP_LOGIN']
SMTP_PASS = environ['SMTP_PASS']
SMTP_HOST = 'smtp.gmail.com'
SMTP_PORT = 587
API_HW_URL = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'


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
    try:
        url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
        params = {
            'chat_id': chat_id,
            'text':  message,
        }
        r = requests.get(url=url, params=params)
        if r.status_code != 200:
            message = (
                'Не удалось отправить сообщение в телеграм. '
                f'Ошибка: {r.json().get("description")}'
            )
            send_mail(message)
        else:
            logging.info('Сообщение отправлено.')
    except ConnectionError as error:
        logging.error(repr(error))
        message = (
            f'Бот столкнулся с ошибкой {repr(error)} '
            f'при отправке сообщения в Telegram.\n'
            f'Текст:\n{message}'
        )
        send_mail(message)


def send_mail(message: str):
    logging.info(f'Попытка отправки сообщения на e-mail. Текст: {message}')
    try:
        smtp_client = SMTP(SMTP_HOST, SMTP_PORT)
        smtp_client.starttls()
        smtp_client.login(SMTP_LOGIN, SMTP_PASS)
        msg = EmailMessage()
        msg.set_content(message)
        msg['Subject'] = 'Яндекс.Практикум'
        smtp_client.send_message(msg, FROM_ADRESS, TO_ADRESS)
        logging.info('Сообщение отправлено.')
    except MessageError as error:
        logging.error(repr(error))


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
            logging.error(repr(error))
            if not type(current_error) == type(error):
                current_error = error
                send_message(ADMIN_CHAT_ID, repr(error))
            time.sleep(30)


if __name__ == '__main__':
    main()
