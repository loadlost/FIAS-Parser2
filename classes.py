import json
from typing import Callable


import requests
import logging

from json_processing import get_object_id_by_name, parse_json_to_dataframe, create_search_result_table

logger = logging.getLogger(__name__)


class RequestConfig:
    """
    Класс для конфигурирования и выполнения HTTP-запросов.

    Attributes:
    address List[str]: Адрес, разбитый на элементы.
    token str: Токен для аутентификации на сервере ФИАС.

    Methods:
        execute(session: requests.Session) -> requests.Response:
        Выполняет запрос на основе конфигурации объекта RequestConfig, используя указанную сессию
    """
    address = None  # Заполняется в main
    token = None  # Заполняется в get_token

    def __init__(self, url: str = None, method: str = 'GET', headers: dict = None, data: dict = None,
                 use_proxies: bool = True,
                 before_request_method: str = None, after_request_method: str = None):

        """
        Инициализирует объект RequestConfig для выполнения HTTP-запросов.

        :param url: URL запроса. Если не указан, используется None.
        :type url: Optional[str]

        :param method: Метод запроса ('GET' или 'POST'). По умолчанию 'GET'.
        :type method: str

        :param headers: Заголовки для запроса. Если не указаны, создается пустой словарь.
        :type headers: Optional[Dict[str, str]]

        :param data: Данные для POST-запросов. Если не указаны, используется None.
        :type data: Optional[Dict]

        :param use_proxies: Указывает, нужно ли использовать прокси для запроса. По умолчанию True.
        :type use_proxies: bool

        :param before_request_method: Имя метода, который будет выполнен перед отправкой запроса. Может быть None.
        :type before_request_method: Optional[str]

        :param after_request_method: Имя метода, который будет выполнен после получения ответа. Может быть None.
        :type after_request_method: Optional[str]
        """

        # URL запроса
        self.url = url

        # Строка состоящая из ID объектов.
        # Пример: 807356.96228493.862378.864576.10847998.159610445
        self.path = None

        # Метод (GET или POST)
        self.method = method

        # Заголовки запроса, если не переданы — создается пустой словарь
        self.headers = headers if headers else {}

        # Данные для POST-запросов, могут быть None
        self.data = data

        # Указывает, использовать ли прокси для запросов. Если False, то прокси не будет использован для всех запросов.
        # Если True, то прокси будет использован для всех запросов. Если use_proxies, то значение берётся из
        # конфигурации запроса. (из объектов RequestConfig в requests_config.py)
        self.use_proxies = use_proxies

        # Метод, который будет выполнен перед отправкой запроса (может быть None)
        self.before_request_method = before_request_method

        # Метод, который будет выполнен после получения ответа (может быть None)
        self.after_request_method = after_request_method

        # Сессия, используемая для выполнения запроса, инициализируется позже (requests.Session)
        self.session = None

    def execute(self, session: requests.Session) -> requests.Response:
        """
        Выполняет запрос, используя requests.Session и конфигурацию объекта RequestConfig.

        Метод поддерживает выполнение GET и POST запросов. Если указан метод before_request_method,
        он будет выполнен перед отправкой запроса. Аналогично, after_request_method выполняется
        после получения ответа, и, если он возвращает новый ответ, то этот новый ответ будет возвращён.

        :param session: Активная сессия requests.Session для выполнения запроса.
        :type session: requests.Session
        :return: Ответ от сервера в виде объекта requests.Response. Если метод after_request_method возвращает
                 новый response, то именно он будет возвращён.
        :rtype: requests.Response
        :raises ValueError: Если указан неподдерживаемый HTTP-метод (не GET и не POST).
        """

        logger.info(f'Executing {self.method} request to {self.url}')

        self.session: requests.Session = session  # Сохраняет текущую сессию для использования в других методах

        if self.before_request_method:
            # Если указан метод, который должен выполняться перед запросом,
            # получает ссылку на этот метод и вызывает его, если он существует и может быть вызван.
            method_to_call: Callable = getattr(self, self.before_request_method, None)
            if callable(method_to_call):
                method_to_call()  # Вызывает метод для подготовки данных перед выполнением запроса

        proxies: dict = session.proxies if self.use_proxies else {"http": "", "https": ""}
        # Если флаг self.use_proxies True (по умолчанию), используется прокси из сессии.
        # Если False, прокси не используется.

        if self.method.upper() == 'GET':
            # Выполняет GET запрос с указанными параметрами.
            response: requests.Response = session.get(self.url, headers=self.headers, proxies=proxies)
        elif self.method.upper() == 'POST':
            # Выполняет POST запрос с указанными параметрами и данными.
            response: requests.Response = session.post(self.url, headers=self.headers, json=self.data, proxies=proxies)
        else:
            # Выбрасывает исключение, если метод не поддерживается.
            raise ValueError(f"Unsupported method: {self.method}")

        if self.after_request_method:
            # Если указан метод для обработки ответа, вызывает его.
            method_to_call: Callable = getattr(self, self.after_request_method, None)
            if callable(method_to_call):
                new_response = method_to_call(response)
                # Если метод возвращает новый ответ, то возвращает его.
                if new_response:
                    logger.info(f'Received new response from after request method: {self.after_request_method}')
                    return new_response
        return response

    @staticmethod
    def get_token(response: requests.Response) -> None:
        """
        Парсит JSON-ответ и сохраняет в RequestConfig.token.
        Вызывается после выполнения запроса get_token_response.

        :param response: Ответ от сервера в виде объекта requests.Response
        :type response: requests.Response
        :return: None
        """
        logger.info('Getting token from response')
        json_data: dict = response.json()
        RequestConfig.token = json_data.get("Token")

    def add_token_to_headers(self) -> None:
        """
        Добавляет заголовок "master-token" со значением RequestConfig.token в текущие заголовки запроса.
        Вызывается перед выполнением запроса search_response.
        :return: None
        """
        logger.info('Adding token to headers')
        self.headers.update({"master-token": f"{RequestConfig.token}"})

    def search_loop(self, response: requests.Response) -> None:

        logger.info('Starting search loop')
        for level, item in enumerate(RequestConfig.address):
            # Используя уровень и кусок адреса (город, район, улица, дом, квартира) ищем ID объекта
            logger.info(f'Searching {item} on level {level}')

            # Получаем ID объекта из get_object_id_by_name
            new_path: str = get_object_id_by_name(response.text, item, level)

            # Дополняем path найденным ранее ID
            self.path: str | None = f"{self.path}.{new_path}" if self.path else new_path
            logger.info(f'New path: {self.path}')

            # Подставляем path в POST-запрос
            self.data: dict = {"address_levels": [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 17], "address_type": 2,
                         "path": f"{self.path}"}
            logger.info(f'New data: {self.data}')

            # Выполняем POST-запрос, чтобы получить список объектов для следующий итерации поиска
            logger.info('Executing search request for level ' + str(level))
            response: requests.Response = self.session.post(self.url, headers=self.headers, json=self.data)

        # Сбрасываем path и data к значениям по умолчанию для следующего поиска
        self.path, self.data = None, {"address_level": 1}

        # Парсим результат поиска
        search_result_data: dict = json.loads(response.text)

        # Создаем dataframe с результатами поиска
        parse_json_to_dataframe(search_result_data)

        # Создаем таблицу с результатами для вывода на экран
        create_search_result_table(search_result_data)

        logger.info('Search loop finished')

