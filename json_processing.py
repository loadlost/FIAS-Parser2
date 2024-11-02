import json
import os
import re
from difflib import SequenceMatcher
import pandas as pd
from prettytable import PrettyTable
import logging

logger = logging.getLogger(__name__)


def get_object_id_by_name(response_text: str, name: str, level: int) -> str or None:
    """
    Извлекает ID объекта по его имени из текста ответа JSON,
    выбирая наилучшее совпадение по степени сходства на указанном уровне.

    :param response_text: Текст ответа JSON.
    :param name: Имя объекта для поиска.
    :param level: Уровень, на котором нужно искать (индекс в массиве hierarchy).
    :return: Идентификатор объекта или None, если объект не найден.
    """
    try:
        # Разбор JSON-ответа для извлечения информации об адресах
        response_data: dict = json.loads(response_text)
        addresses: list = response_data.get('addresses', [])

        best_match_id: str | None = None # Идентификатор с наилучшим совпадением
        best_match_ratio: float = 0 # Степень совпадения

        # Проход по всем объектам в "addresses" и поиск совпадений на указанном уровне
        for address in addresses:
            hierarchy: list = address.get('hierarchy', [])

            # Проверка, существует ли элемент с нужным индексом в "hierarchy"
            if level < len(hierarchy):
                item: dict = hierarchy[level]
                full_name: str = item.get('full_name', '')

                # Оценка степени совпадения между name и full_name
                match_ratio: float = SequenceMatcher(None, name.lower(), full_name.lower()).ratio()

                # Если совпадение лучше предыдущего, обновляем лучшее совпадение
                if match_ratio > best_match_ratio:
                    best_match_ratio: float = match_ratio
                    best_match_id: str = item.get('object_id')

        # Возвращаем идентификатор с наилучшим совпадением
        return best_match_id
    except json.JSONDecodeError as e:
        # Обработка ошибки декодирования JSON
        print(f"Error decoding JSON: {e}")
        return None


def extract_address_info(address: dict, object_type_filter: str = 'all') -> dict or None:
    """
    Извлечение информации об адресе из JSON-данных.
    Применяет фильтр по типу объекта. object_type_filter может принимать значения 'Помещение', 'Квартира', 'all'.

    :param address: Данные об адресе, содержащие иерархию и детали адреса.
    :ptype address: dict

    :param object_type_filter: Фильтр по типу объекта ('Помещение', 'Квартира', 'all').
    :ptype object_type_filter: str

    :return: Словарь с кадастровым номером, строкой адреса и типом объекта или None, если объект не прошел фильтр.
    :rtype: dict or None
    """
    logger.info('Extracting address info')
    address_details: dict = address.get("address_details", {}) # Тут берём кадастровый номер
    hierarchy: list = address.get("hierarchy", [])  # Тут берём куски адреса и тип объекта

    # Применение фильтра по типу объекта
    if not hierarchy or 'type_name' not in hierarchy[-1]:
        return None

    address_type: str = hierarchy[-1]["type_name"]

    # Применение фильтра по типу объекта
    if object_type_filter != 'all' and address_type != object_type_filter:
        logger.info(f'Object {address_details.get("cadastral_number", "")} has type {address_type} '
                    f'does not match the filter {object_type_filter}')
        return None


    # Извлечение информации кадастрового номера
    cadastral_number: str = address_details.get("cadastral_number", "")
    logger.info(f"Cadastral number: {cadastral_number}")

    # hierarchy[0] - город или область
    city: str = hierarchy[0]["full_name_short"] if "full_name_short" in hierarchy[0] else None
    logger.info(f"City: {city}")

    # hierarchy[-3] - улица, -3, потому что 3 с конца объект hierarchy
    street: str = hierarchy[-3]["full_name_short"] if "full_name_short" in hierarchy[-3] else None
    logger.info(f"Street: {street}")

    # hierarchy[-2] - номер дома, -2, потому что 2 с конца объект hierarchy
    house_number: str = hierarchy[-2]["full_name_short"] if "full_name_short" in hierarchy[-2] else None
    logger.info(f"House number: {house_number}")

    # hierarchy[-1] - номер помещения, -1, потому что последний объект hierarchy
    apartment_number: str = hierarchy[-1]["full_name_short"] if "full_name_short" in hierarchy[-1] else None
    logger.info(f"Apartment number: {apartment_number}")

    # Формирование строки адреса
    address_str: str = f"{city}, {street}, {house_number}, {apartment_number}"
    logger.info(f"Address: {address_str}")

    return {
        "Кадастровый номер": cadastral_number,
        "Адрес": address_str,
        "Тип": address_type
    }


def parse_json_to_dataframe(json_data: dict, object_type_filter: str='all'):
    """
    Преобразует JSON-данные в DataFrame и сохраняет в Excel-файл.
    Формирует имя файла из адреса, очищает недопустимые символы и сохраняет в папку "output".
    object_type_filter может принимать значения 'Помещение', 'Квартира', 'all'.
    Если фильтр не 'all', в файл будут сохранены только объекты с указанным типом.

    :param json_data: JSON-данные в виде списка словарей.
    :type json_data: list[dict]
    :param object_type_filter: Фильтр по типу объекта ('Помещение', 'Квартира', 'all').
    :type object_type_filter: str

    :return: None
    """

    logger.info('Parsing JSON to DataFrame')
    data: list = []
    file_name: str | None = None

    # Проход по списку словарей и извлечение информации
    for address in json_data.get("addresses", []):


        # Извлекаем информацию о конкретном помещении
        info: dict = extract_address_info(address, object_type_filter)

        # Если в info ничего нет, значит, объект не прошел фильтр
        if info is None:
            continue

        # Добавляем информацию в список
        data.append(info)

        # Берём объект из info, извлекаем адрес, отрезаем номер помещения
        if file_name is None:
            file_name: str = ", ".join(info["Адрес"].split(", ")[:-1])

    if not data:
        logger.error('All objects did not pass the filter, change the filter in parse_json_to_dataframe.')
        return None

    # Заменяем слеш, и на всякий пожарный, обратный слеш на "др."
    file_name: str = file_name.replace('/', 'др.').replace('\\', 'др.')

    # Заменяем недопустимые символы на "_".
    file_name: str = re.sub(r'[<>:"/\\|?*]', '_', file_name)

    # Создаем DataFrame и сохраняем в Excel-файл, в папку "output"
    df: pd.DataFrame = pd.DataFrame(data)
    os.makedirs('output', exist_ok=True)

    logger.info(f'Saving to Excel: {file_name}.xlsx')
    df.to_excel(f"output/{file_name}.xlsx", index=False)


def create_search_result_table(search_result_data: dict, object_type_filter: str='Помещение') -> PrettyTable:
    """
    Создаёт таблицу с результатами поиска и выводит ее в консоль.
    object_type_filter может принимать значения 'Помещение', 'Квартира', 'all'.
    Если фильтр не 'all', в таблицу будут добавлены только объекты с указанным типом.

    :param search_result_data: JSON-данные в виде словаря.
    :type search_result_data: dict
    :param object_type_filter: Фильтр по типу объекта ('Помещение', 'Квартира', 'all').
    :type object_type_filter: str

    :return: PrettyTable
    """

    logger.info('Creating search result table')
    # Создаём объект PrettyTable
    search_result_table: PrettyTable = PrettyTable()

    # Устанавливаем названия столбцов
    search_result_table.field_names = ["Кадастровый номер", "Адрес", "Тип"]

    # Устанавливаем выравнивание по левому краю
    search_result_table.align = 'l'
    info: dict | None= None
    for address in search_result_data.get("addresses", []):

        # Извлекаем информацию о конкретном помещении
        info: dict | None = extract_address_info(address, object_type_filter)
        if info:
            # Добавляем информацию в таблицу
            search_result_table.add_row([info["Кадастровый номер"], info["Адрес"], info["Тип"]])

    if info is None:
        logger.error('All objects did not pass the filter, change the filter in create_search_result_table.')
        return None
    else:
        print(search_result_table)

