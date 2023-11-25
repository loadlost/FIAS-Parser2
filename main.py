# Модуль main отвечает за основной поток выполнения программы.
# Здесь происходит взаимодействие с пользователем, отправка запросов,
# обработка ответов и вывод результатов.

# Импорт функций для обработки адресов и отправки запросов.
from address_processing import process_region, process_district, process_street, process_house, process_search_result
from utils import send_request

try:
    import config
except ImportError(config):
    print("Не найден модуль config. Убедитесь, что он находится в том же каталоге, что и main.py.")
    exit()

# Получение URL-адресов для отправки запросов из config.
# config.url_requests содержит URL и payload.
url_requests = config.url_requests


def get_input(prompt):  # Функция для получения ввода от пользователя. prompt - подсказка.
    while True:
        user_input = input(prompt)
        if user_input.lower() == 'exit':
            return None
        elif user_input.strip():
            return user_input


def main():  # Основной цикл
    while True:
        # Тут получаем запрос от пользователя, по которому будем искать
        region_name_to_search = get_input("Введите название региона (или 'exit' для выхода): ")
        # Если нет - выход из цикла
        if region_name_to_search is None:
            break

        # Отправляем запросы по всем URL из config.url_requests и сохраняем результаты в responses.
        # Ключи responses - имена запросов, значения - результаты отправки запроса.
        responses = {key: send_request(url, data) for key, (url, data) in url_requests.items()}

        # Вызываем process_region для обработки результата поиска региона.
        # Передаем название региона (region_name_to_search) и словарь (responses).
        # Получаем идентификатор объекта региона (region_object_id) или None, если регион не найден.
        region_object_id = process_region(region_name_to_search, responses)

        # Проверяем, был ли найден регион в responses.
        if region_object_id is not None:
            # Получаем от пользователя следующий запрос (район).
            district_name_to_search = get_input("Введите название района/округа: ")

            # Обрабатываем запрос для поиска идентификатора района по его названию.
            # Передаем идентификатор региона (region_object_id), название района (district_name_to_search)
            # и конфигурацию запросов (url_requests).
            # Получаем идентификатор района или None.
            district_object_id = process_district(region_object_id, district_name_to_search, url_requests)

            if district_object_id is not None:
                # Получаем от пользователя следующий запрос (улица).
                street_name_to_search = get_input("Введите часть названия улицы: ")

                # Обрабатываем запрос для поиска идентификатора улицы по ее названию.
                # Передаем идентификаторы региона (region_object_id) и района (district_object_id),
                # название улицы и конфигурацию запросов (url_requests).
                # Получаем идентификатор улицы (street_object_id) или None.
                street_object_id = process_street(region_object_id, district_object_id, street_name_to_search,
                                                  url_requests)

                if street_object_id is not None:
                    # Получаем от пользователя номер дома.
                    house_number_to_search = get_input("Введите номер дома: ")

                    # Обрабатываем запрос для поиска дома по номеру.
                    # Передаем идентификаторы региона (region_object_id), района (district_object_id)
                    # и улицы (street_object_id), номер дома (house_number_to_search)
                    # и конфигурацию запросов (url_requests).
                    # Получаем идентификатор дома (house_object_id) или None.
                    house_object_id = process_house(region_object_id, district_object_id, street_object_id,
                                                    house_number_to_search, url_requests)

                    if house_object_id is not None:
                        # Обрабатываем результаты поиска и выводим информацию.
                        # Передаем идентификаторы региона (region_object_id), района (district_object_id),
                        # улицы (street_object_id) и дома (house_object_id),
                        # а также конфигурацию запросов (url_requests).
                        process_search_result(region_object_id, district_object_id, street_object_id, house_object_id,
                                              url_requests)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Произошла ошибка: {e}")
