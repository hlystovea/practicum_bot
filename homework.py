import logging
import os
import smtplib
import time
from email.message import EmailMessage
from logging.handlers import RotatingFileHandler

import requests
from dotenv import load_dotenv
from telegram import Bot

handler = RotatingFileHandler('log.log', maxBytes=5000000, backupCount=2)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(funcName)s: %(message)s',
    handlers=[handler],
)

logging.debug('Start script')

load_dotenv()


CHAT_ID = os.getenv('CHAT_ID')
FROM_ADRESS = os.getenv('FROM_ADRESS')
PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
SMTP_LOGIN = os.getenv('SMTP_LOGIN')
SMTP_PASS = os.getenv('SMTP_PASS')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TO_ADRESS = os.getenv('TO_ADRESS')
URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'


def parse_homework_status(homework):
    homework_name = homework.get('homework_name')
    if homework.get('status') == 'rejected':
        verdict = 'К сожалению в работе нашлись ошибки.'
    else:
        verdict = 'Ревьюеру всё понравилось, можно приступать к следующему уроку.'
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    headers = {
        'Authorization': f'OAuth {PRAKTIKUM_TOKEN}',
    }
    params = {
        'from_date': current_timestamp,
    }
    homework_statuses = requests.get(URL, headers=headers, params=params)
    homework_statuses.raise_for_status()
    return homework_statuses.json()


def send_message(message, bot_client):
    logging.info(f'Попытка отправки сообщения: {message}')
    return bot_client.send_message(CHAT_ID, message)


def main():
    smtp_obj = smtplib.SMTP('smtp.gmail.com', 587)
    smtp_obj.starttls()
    smtp_obj.login(SMTP_LOGIN, SMTP_PASS)

    bot_client = Bot(token=TELEGRAM_TOKEN)

    current_timestamp = int(0)

    current_error = None

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(
                    parse_homework_status(
                        new_homework.get('homeworks')[0]), bot_client)
            current_timestamp = new_homework.get('current_date', current_timestamp)
            time.sleep(300)
        except Exception as error:
            print(f'Бот столкнулся с ошибкой: {repr(error)}')
            logging.error(repr(error))
            if not current_error == str(error):
                current_error = str(error)
                try:
                    send_message(repr(error), bot_client)
                except Exception as e:
                    logging.error(repr(e))
                    msg = EmailMessage()
                    msg.set_content(f'{repr(error)}\n{repr(e)}')
                    msg['Subject'] = 'api_sp1_bot'
                    smtp_obj.send_message(msg, FROM_ADRESS, TO_ADRESS)
            time.sleep(5)


if __name__ == '__main__':
    main()
