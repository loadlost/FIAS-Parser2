import json
import requests
from prettytable import PrettyTable
try:
    import config
except ImportError(config):
    print("Не найден модуль config. Убедитесь, что он находится в том же каталоге, что и main.py.")
    exit()


def send_request(url, data, headers=config.common_headers):
    # Отправка HTTP-запроса POST на указанный URL с данными и заголовками.
    # Аргументы:
    #   url (str): URL-адрес для отправки запроса.
    #   data (str): Данные, которые будут отправлены в теле запроса.
    #   headers (dict, optional): Заголовки HTTP-запроса. По умолчанию берутся из config.common_headers.
    # Возвращает:
    #   str or None: Текст ответа на запрос.
    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()  # Проверка наличия ошибок в ответе
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error sending request: {e}")
        return None


def get_object_id_by_name(response_text, name, strict=False):
    # Извлекает идентификатор объекта по его имени из текста ответа JSON.
    # Аргументы:
    #   response_text (str): Текст ответа JSON.
    #   name (str): Имя объекта для поиска.
    #   strict (bool, optional): Флаг строгого сравнения имен. По умолчанию False.
    # Возвращает:
    #   str or None: Идентификатор объекта или None, если объект не найден.
    try:
        # Разбор JSON-ответа для извлечения информации об адресах.
        response_data = json.loads(response_text)
        addresses = response_data.get('addresses', [])

        # Поиск объекта по имени в иерархии адресов.
        for address in addresses:
            hierarchy = address.get('hierarchy', [])
            for item in hierarchy:
                full_name = item.get('full_name', '')

                # Проверка совпадения имен с учетом строгости.
                if not strict:
                    if name.lower() in full_name.lower():
                        return item.get('object_id')
                else:
                    if item.get('object_type') == 'house' and name.lower() == full_name.lower():
                        return item.get('object_id')

        # Если объект не найден, возвращаем None.
        return None
    except json.JSONDecodeError as e:
        # Обработка ошибки декодирования JSON.
        print(f"Error decoding JSON: {e}")
        return None


def create_search_result_table(search_result_data):
    # Создание таблицы для отображения результатов поиска.
    # Аргументы:
    #   search_result_data (dict): Данные с результатами поиска.
    # Возвращает:
    #   PrettyTable: Таблица с отформатированными результатами поиска.

    search_result_table = PrettyTable()
    search_result_table.field_names = ["Кадастровый номер", "Адрес", "Тип"]
    search_result_table.align = 'l'

    # Итерация по результатам поиска и формирование строк таблицы.
    for address in search_result_data.get("addresses", []):
        address_details = address.get("address_details", {})
        hierarchy = address.get("hierarchy", [])

        # Извлечение информации об адресе из иерархии.
        city = hierarchy[0]["name"] if hierarchy and "name" in hierarchy[0] else ""
        street = hierarchy[2]["full_name"] if len(hierarchy) > 2 and "full_name" in hierarchy[2] else ""
        house_number = hierarchy[3]["full_name_short"] if len(hierarchy) > 3 and "full_name_short" in hierarchy[3] \
            else ""
        apartment_number = hierarchy[-1]["full_name_short"] if hierarchy and "full_name_short" in hierarchy[-1] else ""

        # Формирование строки адреса.
        address_str = f"{city}, {street}, {house_number}, {apartment_number}"
        address_type = hierarchy[-1]["type_name"] if len(hierarchy) > 1 else ""

        # Добавление строки в таблицу.
        search_result_table.add_row([address_details.get("cadastral_number", ""), address_str, address_type])

    return search_result_table
