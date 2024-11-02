# Модуль requests_config.py содержит объекты конфигурации запросов, каждый из которых представляет собой экземпляр
# класса RequestConfig.
#
# Объект RequestConfig включает следующие параметры:
# - url: URL, на который будет отправлен запрос.
# - method: HTTP-метод (GET, POST и т.д.).
# - headers: Заголовки запроса.
# - before_request_method: Метод, который выполняется перед отправкой запроса для подготовки данных.
# - after_request_method: Метод, который выполняется после получения ответа для обработки данных.
# - data: Данные для POST-запросов.
# - use_proxies: Флаг, определяющий, нужно ли использовать прокси для запроса.

from classes import RequestConfig

initial_response = RequestConfig(
    url='https://fias.nalog.ru/ExtendedSearch',
    method='GET',
    headers={
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "host": "fias.nalog.ru",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1"
    }
)

get_token_response = RequestConfig(
    url='https://fias.nalog.ru/Home/GetSpasSettings?url=https%3A%2F%2Ffias.nalog.ru%2FExtendedSearch%23',
    method='GET',
    headers={
        "accept": "application/json, text/javascript, */*; q=0.01",
        "host": "fias.nalog.ru",
        "referer": "https://fias.nalog.ru/ExtendedSearch",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "x-requested-with": "XMLHttpRequest"
    },
    after_request_method='get_token'
)

search_response = RequestConfig(
    url='https://fias-public-service.nalog.ru/api/spas/v2.0/GetAddressItems',
    method='POST',
    headers={
        "accept": "application/json, text/javascript, */*; q=0.01",
        "content-length": "19",
        "content-type": "application/json",
        "host": "fias-public-service.nalog.ru",
        "origin": "https://fias.nalog.ru",
        "referer": "https://fias.nalog.ru/",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site"
    },
    data={"address_level":1},
    before_request_method='add_token_to_headers',
    after_request_method='search_loop'
)