import logging
import os
import time

import requests
from telegram import Bot


logging.basicConfig(
    level=logging.DEBUG,
    filename='my_logger.log',
    filemode='w',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)


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
    try:
        homework_status = homework['status']
    except KeyError:
        logging.error(KeyError, exc_info=True)
        return f'Бот столкнулся с ошибкой: {KeyError}'
    if homework_status == 'rejected':
        verdict = 'К сожалению в работе нашлись ошибки.'
    elif homework_status == 'approved':
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
        'from_date': 0,
    }
    try:
        response = requests.get(API_URL, params=params, headers=headers)
    except requests.RequestException as error:
        logging.error(error, exc_info=True)
        return {'error': error}
    else:
        homework_statuses = response
        return homework_statuses.json()


def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())  # начальное значение timestamp
    while True:
        homework = get_homework_statuses(current_timestamp)
        try:
            error = homework['error']
        except KeyError:
            try:
                homeworks_list = homework['homeworks']
            except TypeError:
                logging.error(KeyError, exc_info=True)
                send_message(f'Бот столкнулся с ошибкой: {TypeError}', bot)
            except KeyError:
                logging.error(KeyError, exc_info=True)
                send_message(f'Бот столкнулся с ошибкой: {KeyError}', bot)
            else:
                try:
                    new_homework = homeworks_list[0]
                except IndexError:          # нет новых домашних работ
                    logging.error(IndexError, exc_info=True)
                else:
                    send_message(parse_homework_status(new_homework), bot)
                finally:
                    current_timestamp = homework.get(
                        'current_date',
                        current_timestamp
                    )
        else:
            send_message(f'Бот столкнулся с ошибкой: {error}', bot)
        finally:
            time.sleep(300)


if __name__ == '__main__':
    main()
