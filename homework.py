import logging
import os
import time

import requests
from dotenv import load_dotenv
from telegram import Bot

logging.basicConfig(
    level=logging.DEBUG,
    filename='my_logger.log',
    filemode='w',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)

load_dotenv()


PRAKTIKUM_TOKEN = os.getenv("PRAKTIKUM_TOKEN")
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
API_URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'


def parse_homework_status(homework):
    try:
        homework_name = homework['homework_name']
    except KeyError:
        logging.error(KeyError, exc_info=True)
        return f'Бот столкнулся с ошибкой: {KeyError}'
    else:
        try:
            homework_status = homework['status']
        except KeyError:
            logging.error(KeyError, exc_info=True)
            return f'Бот столкнулся с ошибкой: {KeyError}'
        else:
            if homework_status == 'rejected':
                verdict = 'К сожалению в работе нашлись ошибки.'
            else:
                verdict = (
                    'Ревьюеру всё понравилось, '
                    'можно приступать к следующему уроку.'
                )
            return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def send_message(message, bot_client):
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def get_homework_statuses(current_timestamp):
    headers = {
        'Authorization': f'OAuth {PRAKTIKUM_TOKEN}',
    }
    params = {
        'from_date': current_timestamp,
    }
    try:
        response = requests.get(API_URL, params=params, headers=headers)
    except Exception as error:
        logging.error(error, exc_info=True)
        return f'Бот столкнулся с ошибкой: {error}'
    else:
        homework_statuses = response
        return homework_statuses.json()


def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())  # начальное значение timestamp
    while True:
        homework = get_homework_statuses(current_timestamp)
        try:
            homeworks_list = homework['homeworks']
        except TypeError:
            send_message(f'Бот столкнулся с ошибкой: {homework}', bot)
        except KeyError:
            logging.error(KeyError, exc_info=True)
            send_message(f'Бот столкнулся с ошибкой: {KeyError}', bot)
        else:
            try:
                new_homework = homeworks_list[0]
            except IndexError:
                logging.error(IndexError, exc_info=True)
                send_message(f'Бот столкнулся с ошибкой: {IndexError}', bot)
            else:
                send_message(parse_homework_status(new_homework), bot)
            finally:
                current_timestamp = homework.get(
                    'current_date',
                    current_timestamp
                )
        finally:
            time.sleep(300)


if __name__ == '__main__':
    main()
