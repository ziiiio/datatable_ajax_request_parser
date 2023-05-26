# See https://datatables.net/manual/server-side for datatable server-side processing
from urllib.parse import parse_qs, urlparse

from .dataclasses import DTColumn, DTOrder, DTRequest
from .utils import transform_to_bool


def get_columns(columns_dictionary: dict):
    columns = []

    for _, column in sorted(columns_dictionary.items()):
        data_dict = {
            'data': column.get('data', None),
            'name': column.get('name', None),
            'searchable': transform_to_bool(column.get('searchable', False)),
            'orderable': transform_to_bool(column.get('orderable', False)),
            'search_value': column.get('search', {}).get('value', None),
            'search_is_regex': transform_to_bool(column.get('search', {}).get('regex', None))
        }

        column_object = DTColumn(**data_dict)
        columns.append(column_object)

    return columns


def get_orders(order_dictionary):
    orders = []

    for index, order in sorted(order_dictionary.items()):
        data_dict = {
            'index': index,
            'column': order.get('column', None),
            'direction': order.get('dir', None),
        }
        orders.append(DTOrder(**data_dict))

    return orders


def parse_datatable_raw_request_query(raw_request: str, as_dt_request=True):
    parse_result = urlparse(raw_request)
    print(parse_result.query)
    datatable_query = parse_qs(parse_result.query, keep_blank_values=True)

    parsed_dict: dict[str, str | list[str] | dict] = {}

    for key, value in datatable_query.items():
        print(key, value)
        key_list = key.replace('][', ';').replace('[', ';').replace(']', '').split(';')

        if len(key_list) == 0:
            continue

        if len(key_list) == 1:
            parsed_dict[key] = value[0] if len(value) == 1 else value
            continue

        temp_dict = parsed_dict
        for inner_key in key_list[:-1]:
            if inner_key not in temp_dict:
                temp_dict.update({inner_key: {}})
            temp_dict = temp_dict[inner_key]
        temp_dict[key_list[-1]] = value[0] if len(value) == 1 else value

    if not as_dt_request:
        return parsed_dict

    import json
    print(json.dumps(parsed_dict))

    data_dict = {
        'draw': int(parsed_dict.get('draw', None)),
        'start': int(parsed_dict.get('start', None)),
        'length': int(parsed_dict.get('length', None)),
        'search_value': parsed_dict.get('search', {}).get('value', None),
        'search_regex': transform_to_bool(parsed_dict.get('search', {}).get('regex', False)),
        'columns': get_columns(parsed_dict.get('columns', None)),
        'orders': get_orders(parsed_dict.get('order', None)),
    }

    return DTRequest(**data_dict)
