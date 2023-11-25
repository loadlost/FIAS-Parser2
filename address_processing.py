# Модуль address_processing отвечает за обработку адресов и взаимодействие с API для поиска объектов по названию.

import json
from utils import send_request, get_object_id_by_name, create_search_result_table


def handle_response(result, name_to_search, entity_type):
    # Обработка ответа от API при поиске объекта.
    # Аргументы:
    #   result (str or None): Идентификатор объекта или None, если объект не найден.
    #   name_to_search (str): Название объекта, по которому велся поиск.
    #   entity_type (str): Тип объекта (например, "Region" или "Entity").

    if result is not None:
        print(f"The object_id for {name_to_search} is: {result}")
        return result
    else:
        print(f"{entity_type} '{name_to_search}' not found in the response.")
        return None


def get_object_id(data, level, url, name_to_search, strict=False):
    # Получение идентификатора объекта по его названию и уровню в иерархии адресов.
    # Аргументы:
    #   data (dict): Данные для запроса к API.
    #   level (int): Уровень в иерархии адресов.
    #   url (str): URL-адрес для отправки запроса.
    #   name_to_search (str): Название объекта для поиска.
    #   strict (bool, optional): Флаг строгого сравнения имен. По умолчанию False.

    # Возвращает:
    #   str or None: Идентификатор объекта или None, если объект не найден.

    data["address_levels"] = [level]
    response = send_request(url, json.dumps(data))
    result_object_id = get_object_id_by_name(response, name_to_search, strict=strict)
    return handle_response(result_object_id, name_to_search, "Entity")


def process_region(region_name_to_search, responses):
    # Обработка результата поиска региона.
    # Аргументы:
    #   region_name_to_search (str): Название региона для поиска.
    #   responses (dict): Словарь с результатами запросов.

    # Возвращает:
    #   str or None: Идентификатор объекта региона или None, если регион не найден.

    return handle_response(get_object_id_by_name(responses['first'], region_name_to_search), region_name_to_search,
                           "Region")


def process_district(region_object_id, district_name_to_search, url_requests):
    # Обработка результата поиска района.
    # Аргументы:
    #   region_object_id (str): Идентификатор региона.
    #   district_name_to_search (str): Название района для поиска.
    #   url_requests (dict): Конфигурация URL-адресов для запросов.

    # Возвращает:
    #   str or None: Идентификатор объекта района или None, если район не найден.

    return get_object_id({"path": str(region_object_id)}, 3, url_requests['second'][0], district_name_to_search)


def process_street(region_object_id, district_object_id, street_name_to_search, url_requests):
    # Обработка результата поиска улицы.
    # Аргументы:
    #   region_object_id (str): Идентификатор региона.
    #   district_object_id (str): Идентификатор района.
    #   street_name_to_search (str): Название улицы для поиска.
    #   url_requests (dict): Конфигурация URL-адресов для запросов.

    # Возвращает:
    #   str or None: Идентификатор объекта улицы или None, если улица не найдена.

    return get_object_id({"path": f"{region_object_id}.{district_object_id}"}, 8, url_requests['third'][0], street_name_to_search)


def process_house(region_object_id, district_object_id, street_object_id, house_number_to_search, url_requests):
    # Обработка результата поиска дома.
    # Аргументы:
    #   region_object_id (str): Идентификатор региона.
    #   district_object_id (str): Идентификатор района.
    #   street_object_id (str): Идентификатор улицы.
    #   house_number_to_search (str): Номер дома для поиска.
    #   url_requests (dict): Конфигурация URL-адресов для запросов.

    # Возвращает:
    #   str or None: Идентификатор объекта дома или None, если дом не найден.

    return get_object_id({"path": f"{region_object_id}.{district_object_id}.{street_object_id}"}, 10,
                         url_requests['fourth'][0], f"дом {house_number_to_search}", strict=True)


def process_search_result(region_object_id, district_object_id, street_object_id, house_object_id, url_requests):
    # Обработка результатов поиска и вывод информации.
    # Аргументы:
    #   region_object_id (str): Идентификатор региона.
    #   district_object_id (str): Идентификатор района.
    #   street_object_id (str): Идентификатор улицы.
    #   house_object_id (str): Идентификатор дома.
    #   url_requests (dict): Конфигурация URL-адресов для запросов.

    search_query_data = {
        "address_level": 11,
        "path": f"{region_object_id}.{district_object_id}.{street_object_id}.{house_object_id}"
    }
    search_query_response = send_request(url_requests['fifth'][0], json.dumps(search_query_data))

    try:
        search_result_data = json.loads(search_query_response)
        search_result_table = create_search_result_table(search_result_data)
        print(search_result_table)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
