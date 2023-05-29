from dataclasses import dataclass, asdict

from django.db.models import Q, Model, QuerySet

from datatable_ajax_request_parser.dataclasses import DTRequest, DTResponse
from datatable_ajax_request_parser.parser import add_typings_to_dict, parse_datatable_raw_request_query

from typing import Callable, Type


@dataclass
class DjangoDTRequest(DTRequest):

    def __init__(self, *args, **kwargs):
        raw_request = kwargs.pop('raw_request', None)
        if raw_request:
            parsed_dict = parse_datatable_raw_request_query(raw_request, return_dt_request=False)
            kwargs.update(add_typings_to_dict(parsed_dict))

        parsed_dict = kwargs.pop('parsed_dict', None)
        if parsed_dict:
            kwargs.update(add_typings_to_dict(parsed_dict))

        super().__init__(*args, **kwargs)

    # pass mapping dict in if you are not ordering based on the model
    # example: annotations, aggregations
    def get_order_by(self, mapping_dict: dict = None):
        order_list = []

        for order in self.order:
            order_index = order.column

            if 0 > order_index or order_index >= len(self.columns):
                continue

            db_column = self.columns[order_index].data
            if mapping_dict and mapping_dict.get(db_column):
                db_column = mapping_dict.get(db_column)

            if order.direction == 'desc':
                db_column = '-' + db_column

            order_list.append(db_column)

        return order_list

    def get_db_query_filter(self, mapping_dict: dict = None):
        filters = []

        for column in self.columns:
            query_filter = Q()

            if not column.searchable or (mapping_dict and column.data not in mapping_dict):
                continue

            col_name = column.data

            if self.search_regex:
                query_filter |= Q(**{col_name + '__iregex': fr"{self.search_value}"})
            elif self.search_value:
                query_filter |= Q(**{col_name + '__icontains': self.search_value})

            if not column.search_value:
                filters.append(query_filter)
                continue

            column_key = col_name + '__iregex' if column.search_is_regex else col_name + '__icontains'

            query_filter |= Q(**{column_key: column.search_value})

            filters.append(query_filter)

        final_query = Q()
        for _filter in filters:
            final_query |= _filter

        return final_query


@dataclass
class DjangoDTResponse(DTResponse):

    def convert_to_dt_response_dict(self):
        return {
            "data": self.data,
            "recordsTotal": self.records_total,
            "recordsFiltered": self.records_filtered,
            "draw": self.draw,
            "error": self.error
        }


def get_django_datatable_query(raw_request: str = None) -> DjangoDTRequest:
    return DjangoDTRequest(raw_request=raw_request)


def get_django_dt_response(parsed_dt_query: DjangoDTRequest,
                           model_class: Type[Model],
                           data_function: Callable[[QuerySet], DTResponse],
                           error: str = None) -> DjangoDTResponse:
    draw = parsed_dt_query.draw
    offset = parsed_dt_query.start
    limit = parsed_dt_query.length
    order_by = parsed_dt_query.get_order_by()
    search = parsed_dt_query.get_db_query_filter()

    query_set = model_class.objects.filter(search).order_by(*order_by)

    query_set_count = query_set.count()

    filtered_set = query_set[offset:offset + limit]

    result = {
        "data": data_function(filtered_set),
        "records_total": query_set_count,
        "records_filtered": query_set_count,
        "draw": draw,
        "error": error
    }
    return DjangoDTResponse(**result)
