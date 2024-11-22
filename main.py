import logging
from typing import List
import msvcrt
import requests

from credentials import proxy_url
from common_headers import session_headers
from requests_config import *

# Настройка форматтера для логов
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s',
                              datefmt='%d-%m-%Y %H:%M:%S')

handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.INFO)


def get_session() -> requests.Session:
    """
    Инициализирует и возвращает сессию с обновленными заголовками и прокси.

    Функция создает экземпляр requests.Session, обновляет его заголовки
    и прокси, после чего возвращает готовую сессию.

    Заголовки берутся из глобальной переменной session_headers (определена в модуле common_headers).
    Прокси устанавливаются на основе глобальной переменной proxy_url (определена в модуле credentials).


    :return:  Сессия с обновленными заголовками и прокси
    :rtype: requests.Session
    :raises: None
    """
    # Инициализация сессии
    with requests.Session() as session:
        # Обновляем заголовки сессии из common_headers
        session.headers.update(session_headers)

        # Настраиваем прокси из credentials
        session.proxies.update({
            'http': proxy_url,
            'https': proxy_url
        })

        return session


def get_token(session: requests.Session) -> None:
    """
    Функция для получения токена. Инициализирует последовательность запросов get_token_sequence и передаёт их в
    функцию send_requests.

    :param session: Активная сессия для выполнения запроса. :type session: requests.Session :return: None :rtype:
    None :raises requests.exceptions.RequestException: Возникает при неудачном выполнении одного из запросов из
    get_token_sequence
    """

    logger.info('Token request started')

    # Список с объектами класса RequestConfig, которые содержат параметры запросов
    # Объекты RequestConfig определены в модуле requests_config

    get_token_sequence: List[RequestConfig] = [
        initial_response,
        get_token_response
    ]

    try:
        # Выполнение последовательности запросов
        send_requests(session, get_token_sequence)
        logger.info('Token received')
    except requests.exceptions.RequestException as e:
        raise requests.exceptions.RequestException('Token request failed with error: ' + str(e))


def search_objects(session: requests.Session, task_list: List[List[str]]) -> None:
    """
    Функция для поиска. Отправляет запрос используя метод execute класса RequestConfig.

    :param task_list: Список задач, где каждая задача представлена списком строк. :type task_list: list :param
    :param session: Активная сессия для выполнения запроса. :type session: requests.Session :return: None :rtype: None
    :raises requests.exceptions.RequestException: Возникает при неудачном выполнении одного из запросов из
    search_sequence

    """

    logger.info('Search process started')

    for task in task_list:
        logger.info(f'Processing address: {task}')
        # Устанавливаем текущий адрес для RequestConfig
        RequestConfig.address = task
        try:
            search_response.execute(session)
            logger.info(f'Successfully parsed address: {RequestConfig.address}')
        except (requests.exceptions.RequestException, Exception) as e:
            # Поднимаем исключение с сообщением об ошибке
            raise requests.exceptions.RequestException('Parse process failed with error: ' + str(e))
        else:
            # Если запрос успешен, ждем перед следующим заказом
            logger.info('Parse process completed successfully')


def send_requests(session: requests.Session, request_list: List[RequestConfig], max_url_length: int = 100,
                  url: str = 'Unknown URL') -> None:
    """
    Выполняет последовательность HTTP-запросов, используя requests.Session.

    Функция проходит по списку запросов, выполняя их через сессию.
    Логирует успешные и неуспешные запросы, ограничивает длину URL до max_url_length.
    При возникновении ошибки запросов вызывает исключение и перезапускает скрипт.

    :param session: Активная сессия для выполнения запросов.
    :type session: requests.Session
    :param request_list: Список объектов RequestConfig с конфигурациями запросов.
    :type request_list: List[RequestConfig]
    :param max_url_length: Максимальная длина отображаемого URL для логирования (по умолчанию 100).
    :type max_url_length: int
    :param url: URL для логирования в случае отсутствия URL в запросе.
    :type url: str
    :return: None
    :rtype: None
    :raises requests.exceptions.RequestException: Поднимает исключение в случае ошибки запроса.
    """

    for request_config in request_list:
        try:
            # Выполняем запрос используя параметры запросов из объектов класса RequestConfig и метод
            # RequestConfig.execute
            response: requests.Response = request_config.execute(session)
            # Проверяем наличие URL в конфигурации запроса. Используется в логах.
            url: str = request_config.url if hasattr(request_config, 'url') else 'Unknown URL'

            # Ограничиваем длину URL для логирования
            if len(url) > max_url_length:
                url: str = url[:max_url_length] + '...'

            # Проверяем, является ли статус-код успешным
            if response.status_code == 200:
                logger.info(f'{response.status_code} Request successful {url}')
            else:
                # Логируем и вызываем исключение, если запрос неуспешен
                response_text: str = response.text if hasattr(response, 'text') else 'No response text'
                logger.error(f'{response.status_code} Request failed {url} TEXT: {response_text}')

                raise requests.exceptions.RequestException(
                    'Request failed with status code: ' + str(response.status_code))

        except requests.exceptions.RequestException as e:
            # Логируем ошибку и поднимаем исключение с дополнительной информацией
            logger.error(f"Request failed {url} with error: {e}")

            main()  # Перезапускаем скрипт


def read_tasks() -> List[List[str]] | None:
    """
    Читает файл, где каждая строка представляет адрес, разделенный запятыми,
    и возвращает список списков с элементами адреса.

    :return: Список задач, где каждая задача представлена списком строк.
    """
    logger.info('Reading tasks from file')
    tasks: List[List[str]] = []
    try:
        with open('tasks.txt', 'r', encoding='utf-8') as file:
            for line in file:  # Читаем каждую строку
                # Разбиваем строку на элементы, разделитель - запятая
                task: List[str] = [element.strip() for element in line.strip().split(',')]
                tasks.append(task)
    except FileNotFoundError:
        logger.error("File 'tasks.txt' not found.")
        return None

    if not tasks:
        logger.error("File 'tasks.txt' is empty.")
        return None
    else:
        logger.info(f"{len(tasks)} tasks read from file")
        return tasks


def main() -> None:
    """ Запускает скрипт. Позволяет пользователю выбрать обработку задач из файла или ввод адреса вручную.

    :return: None
    """
    while True:
        print("Нажмите любую кнопку для обработки задач из файла или Escape для ввода адреса вручную.")
        key: bytes = msvcrt.getch() # Возвращает один символ, считанный с клавиатуры, в виде байтового объекта
        if key == b'\x1b':  # Если нажата клавиша Escape, то пользователь может ввести адрес вручную
            tasks: List[List[str]] = []
            user_input: str = input("Введите адрес: ")
            if user_input == '':  # Если ввод пустой строки, возвращаемся к началу цикла.
                logger.error("Input is empty.")
                continue

            # Разбиваем строку на элементы, разделитель - запятая
            task = [element.strip() for element in user_input.strip().split(',')]
            tasks.append(task)  # Добавляем задачу в список задач
            start(tasks)  # Запускаем обработку задач
        else:  # Если нажата какая-то другая клавиша, то обрабатываем задачи из файла
            tasks: List[List[str]] = read_tasks()  # Читаем задачи из файла
            if tasks is None:  # Если список задач пустой, возвращаемся к началу цикла.
                continue
            else:
                start(tasks)  # Запускаем обработку задач


def start(tasks: List[List[str]]) -> None:
    """ Запускает обработку задач.

    :param tasks: Список задач, где каждая задача представлена списком строк.
    :type tasks: list
    :return: None
    """

    session = get_session()  # Получаем активную сессию
    get_token(session)  # Получаем токен
    search_objects(session, tasks)  # Обрабатываем задачи


if __name__ == '__main__':
    main()
