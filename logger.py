import logging
from logging.handlers import RotatingFileHandler
from os import environ

from notifiers.logging import NotificationHandler

FROM_ADRESS = environ['FROM_ADRESS']
TO_ADRESS = environ['TO_ADRESS']
SMTP_PASS = environ['SMTP_PASS']


notifier_params = {
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

console_out_hundler = logging.StreamHandler()
notification_handler = NotificationHandler('gmail', defaults=notifier_params)
rotate_file_handler = RotatingFileHandler('log.log', maxBytes=5000000, backupCount=2)  # noqa(E501)

notification_handler.setLevel(logging.ERROR)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(funcName)s: %(message)s',
    handlers=[rotate_file_handler, console_out_hundler, notification_handler]
)

logger = logging.getLogger()
