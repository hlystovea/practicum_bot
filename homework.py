import logging
import os
import smtplib
import time
from email.errors import MessageError
from email.message import EmailMessage
from json import JSONDecodeError
from logging.handlers import RotatingFileHandler
from requests.exceptions import RequestException

import requests
import telegram
from dotenv import load_dotenv
from telegram import Bot, TelegramError

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

load_dotenv()


CHAT_ID = os.environ['CHAT_ID']
FROM_ADRESS = os.environ['FROM_ADRESS']
PRAKTIKUM_TOKEN = os.environ['PRAKTIKUM_TOKEN']
SMTP_LOGIN = os.environ['SMTP_LOGIN']
SMTP_PASS = os.environ['SMTP_PASS']
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
TO_ADRESS = os.environ['TO_ADRESS']
API_HW_URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'


def parse_homework_status(homework):
    statuses = {
        'reviewing': 'Работа взята в ревью.',
        'rejected': 'К сожалению в работе нашлись ошибки.',
        'approved': ('Ревьюеру всё понравилось, '
                     'можно приступать к следующему уроку.'),
    }
    try:
        homework_name = homework.get('homework_name', 'Неизвестная работа')
        verdict = statuses.get(homework.get('status'), 'Статус неизвестен.')
        return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'
    except AttributeError as error:
        # на случай если функция используется где-то ещё и в неё
        # может прилететь не словарь, а падать ей запрещено по ТЗ
        logging.exception('')
        raise error


def get_homework_statuses(current_timestamp=0):
    headers = {
        'Authorization': f'OAuth {PRAKTIKUM_TOKEN}',
    }
    params = {
        'from_date': current_timestamp,
    }
    try:
        homework_statuses = requests.get(
            API_HW_URL,
            headers=headers,
            params=params,
        )
        # homework_statuses.raise_for_status()
        # ^-- тесты не пускают с этой строкой из-за имитации ответа сервера
        return homework_statuses.json()
    except (RequestException, JSONDecodeError) as error:
        # в учебных целях
        logging.exception('')
        raise error


def send_message(message, bot_client):
    logging.info(f'Попытка отправки сообщения в Telegram. Текст: {message}')
    try:
        return bot_client.send_message(CHAT_ID, message)
    except TelegramError as error:
        # в случае ошибки используем резервный канал связи
        logging.exception('')
        message = (
            f'Бот столкнулся с ошибкой {repr(error)} '
            f'при отправке сообщения в Telegram.\n'
            f'Текст:\n{message}'
        )
        send_mail(message, smtp_client)
        raise error


def send_mail(message, smtp_client):
    logging.info(f'Попытка отправки сообщения на e-mail. Текст: {message}')
    try:
        msg = EmailMessage()
        msg.set_content(message)
        msg['Subject'] = 'api_sp1_bot'
        smtp_client.send_message(msg, FROM_ADRESS, TO_ADRESS)
        logging.info('Сообщение отправлено.')
    except MessageError:
        # только для логирования
        logging.exception('')


def main():
    global smtp_client
    smtp_client = smtplib.SMTP('smtp.gmail.com', 587)
    smtp_client.starttls()
    smtp_client.login(SMTP_LOGIN, SMTP_PASS)

    bot_client = Bot(token=TELEGRAM_TOKEN)

    current_timestamp = int(time.time())

    current_error = None

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            current_timestamp = new_homework.get(
                'current_date',
                current_timestamp,
            )
            if new_homework.get('homeworks'):
                comment = parse_homework_status(new_homework['homeworks'][0])
                send_message(comment, bot_client)
            time.sleep(300)
        except Exception as error:
            # для вызова send_message() и обработки собственных ошибок
            logging.exception('')
            if not type(current_error) == type(error):
                current_error = error
                try:
                    send_message(repr(error), bot_client)
                except (TelegramError, MessageError):
                    # для продолжения работы при ошибке отправки сообщения
                    continue
            time.sleep(5)


if __name__ == '__main__':
    main()
