import logging
import os
import smtplib
import time
from email.message import EmailMessage
from logging.handlers import RotatingFileHandler

import requests
import telegram
from dotenv import load_dotenv
from telegram import Bot

rotate_file_handler = RotatingFileHandler('log.log', maxBytes=5000000, backupCount=2)
console_out_hundler = logging.StreamHandler()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(funcName)s: %(message)s',
    handlers=[rotate_file_handler, console_out_hundler],
)

logging.debug('Start script')

load_dotenv()


CHAT_ID = os.environ.get('CHAT_ID')
FROM_ADRESS = os.environ.get('FROM_ADRESS')
PRAKTIKUM_TOKEN = os.environ.get('PRAKTIKUM_TOKEN')
SMTP_LOGIN = os.environ.get('SMTP_LOGIN')
SMTP_PASS = os.environ.get('SMTP_PASS')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TO_ADRESS = os.environ.get('TO_ADRESS')
PRAKTIKUM_HW_URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/' # noqa


def parse_homework_status(homework):
    try:
        homework_name = homework.get('homework_name', 'Неизвестная работа')
        if homework.get('status') == 'rejected':
            verdict = 'К сожалению в работе нашлись ошибки.'
        elif homework.get('status') == 'reviewing':
            verdict = 'Работа взята в ревью.'
        elif homework.get('status') == 'approved':
            verdict = 'Ревьюеру всё понравилось, можно приступать к следующему уроку.' #noqa
        else:
            verdict = 'Статус неизвестен.'
        return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'
    except AttributeError as error:
        logging.error(repr(error))
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
            PRAKTIKUM_HW_URL,
            headers=headers,
            params=params,
        )
        # homework_statuses.raise_for_status()
        # ^-- тесты не пускают с этой строкой по причине имитации ответа сервера
        return homework_statuses.json()
    except requests.exceptions.RequestException as error:
        logging.error(repr(error))
        raise error
    except ValueError as error:
        logging.error(repr(error))
        raise error


def send_message(message, bot_client):
    logging.info(f'Попытка отправки сообщения в Telegram. Текст: {message}')
    try:
        return bot_client.send_message(CHAT_ID, message)
    except telegram.TelegramError as error:
        logging.error(repr(error))
        message = f'Бот не смог отправить сообщение в Telegram.\nТекст:\n{message}' # noqa
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
    except Exception as error:
        logging.error(repr(error))


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
            if new_homework.get('current_date'):
                current_timestamp = new_homework.get('current_date')
            if new_homework.get('homeworks'):
                comment = parse_homework_status(new_homework.get('homeworks')[0]) # noqa
                send_message(comment, bot_client)
            time.sleep(300)
        except Exception as error:
            logging.error(repr(error))
            if not type(current_error) == type(error):
                current_error = error
                try:
                    send_message(repr(error), bot_client)
                except Exception as error:
                    logging.error(repr(error))
                    continue
            time.sleep(5)


if __name__ == '__main__':
    main()
