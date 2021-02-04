import logging
import os
import time

import requests
from telegram import Bot
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    filename='my_logger.log',
    filemode='w',
    format='%(asctime)s, %(levelname)s, %(funcName)s, %(message)s, %(name)s'
)


PRAKTIKUM_TOKEN = os.getenv("PRAKTIKUM_TOKEN")
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
API_URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
HOMEWORK_STATUSES = {
    'rejected': 'К сожалению в работе нашлись ошибки.',
    'approved': (
        'Ревьюеру всё понравилось, '
        'можно приступать к следующему уроку.'
    ),
    'reviewing': 'Работа взята в ревью.',
}


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
    try:
        return (
            f'У вас проверили работу "{homework_name}"!\n\n'
            f'{HOMEWORK_STATUSES[homework_status]}'
        )
    except KeyError:
        logging.error(
            f'{KeyError}: неизвестный статус проверки '
            f'"{homework_status}"', exc_info=True
        )
        return (
            f'Бот столкнулся с ошибкой: {KeyError}: '
            f'неизвестный статус проверки "{homework_status}"'
        )


def send_message(message, bot_client):
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def get_homework_statuses(current_timestamp):
    headers = {
        'Authorization': f'OAuth {PRAKTIKUM_TOKEN}',
    }
    params = {
        'from_date': current_timestamp,
    }
    max_retry = 5
    trial_num = 1
    error = requests.RequestException
    while trial_num <= max_retry:
        try:
            homework_statuses = requests.get(
                API_URL,
                params=params,
                headers=headers,
                timeout=100
            )
        except error:
            logging.error(
                f'{error}: headers={headers} params={params}',
                exc_info=True
            )
            trial_num += 1
        else:
            return homework_statuses.json()
        time.sleep(300)
    else:
        return {'error': error}


def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        homework = get_homework_statuses(current_timestamp)
        try:
            raise homework['error']
        except KeyError:
            try:
                homeworks_list = homework['homeworks']
                new_homework = homeworks_list[0]
            except (TypeError, KeyError) as error:
                logging.error(error, exc_info=True)
                send_message(f'Бот столкнулся с ошибкой: {error}', bot)
            # нет новых домашних работ
            except IndexError:
                logging.error(IndexError, exc_info=True)
            else:
                send_message(parse_homework_status(new_homework), bot)
            finally:
                current_timestamp = homework.get(
                    'current_date',
                    current_timestamp
                )
        # homework_statuses.json() содержит 'errors'
        except TypeError:
            send_message(
                f'Бот столкнулся с ошибкой: {homework["error"]}',
                bot
            )
        # Exception из get_homework_statuses
        except homework['error'] as error:
            send_message(
                f'Бот столкнулся с ошибкой: {error}. '
                f'Бот вынужден отключится. '
                f'После восстановления работы API потребуется перезапуск.',
                bot
            )
            break
        except Exception as error:
            logging.error(f'Internal error: {error}', exc_info=True)
            send_message(
                f'Бот столкнулся с ошибкой: Internal error: {error}',
                bot
            )
        finally:
            time.sleep(300)


if __name__ == '__main__':
    main()
