common_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate, br',
    'Content-Type': 'application/json',
    'master-token': '71ca31a0-9723-4c46-b0e4-f77d21b46f1b',
    'Origin': 'https://fias.nalog.ru',
    'Connection': 'keep-alive',
    'Referer': 'https://fias.nalog.ru/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache'
}

url_requests = {
    'region': ('https://fias-public-service.nalog.ru/api/spas/v2.0/GetAddressItems',
               '{"address_level":1}'),

    'district': ('https://fias-public-service.nalog.ru/api/spas/v2.0/GetAddressItems',
                 '{"address_levels":[3],'
                 '"address_type":2,'
                 '"path":"region_object_id"}'),

    'street': ('https://fias-public-service.nalog.ru/api/spas/v2.0/GetAddressItems',
               '{"address_levels":[8],'
               '"address_type":2,'
               '"path":"region_object_id.district_object_id"}'),

    'house': ('https://fias-public-service.nalog.ru/api/spas/v2.0/GetAddressItems',
              '{"address_levels":[10],'
              '"address_type":2,'
              '"path":"region_object_id.district_object_id.street_object_id"}'),

    'search': ('https://fias-public-service.nalog.ru/api/spas/v2.0/GetAddressItems',
               '{"address_level":11,'
               '"path":"region_object_id.district_object_id.street_object_id.house_object_id"}')
}
