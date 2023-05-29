from django.db.models import Q
from django.test import TestCase

from datatable_ajax_request_parser.django_extension import (
    DjangoDTRequest, get_django_datatable_query,
    get_django_dt_response
)
from datatable_ajax_request_parser.utils import assert_q_equal

from unittest import mock


class DjangoAjaxRequestTestCase(TestCase):
    def setUp(self):
        self.sample_datatable_ajax_request = 'http://somedomain/?draw=1&columns%5B0%5D%5Bdata%5D=hostname&columns' \
                                             '%5B0%5D%5Bname%5D=&columns%5B0%5D%5Bsearchable%5D=true&columns%5B0%' \
                                             '5D%5Borderable%5D=true&columns%5B0%5D%5Bsearch%5D%5Bvalue%5D=&colum' \
                                             'ns%5B0%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B1%5D%5Bdata%5D=ip_' \
                                             'address&columns%5B1%5D%5Bname%5D=&columns%5B1%5D%5Bsearchable%5D=tr' \
                                             'ue&columns%5B1%5D%5Borderable%5D=true&columns%5B1%5D%5Bsearch%5D%5B' \
                                             'value%5D=&columns%5B1%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B2%5' \
                                             'D%5Bdata%5D=username&columns%5B2%5D%5Bname%5D=&columns%5B2%5D%5Bsea' \
                                             'rchable%5D=true&columns%5B2%5D%5Borderable%5D=true&columns%5B2%5D%5' \
                                             'Bsearch%5D%5Bvalue%5D=&columns%5B2%5D%5Bsearch%5D%5Bregex%5D=false&' \
                                             'columns%5B3%5D%5Bdata%5D=type&columns%5B3%5D%5Bname%5D=&columns%5B3' \
                                             '%5D%5Bsearchable%5D=true&columns%5B3%5D%5Borderable%5D=true&columns' \
                                             '%5B3%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B3%5D%5Bsearch%5D%5Bregex%' \
                                             '5D=false&order%5B0%5D%5Bcolumn%5D=0&order%5B0%5D%5Bdir%5D=asc&start' \
                                             '=0&length=10&search%5Bvalue%5D=&search%5Bregex%5D=false&_=1672804547475'

        self.parsed_request = {
            'draw': '1',
            'columns': {
                '0': {'data': 'hostname', 'name': '', 'searchable': 'true', 'orderable': 'true',
                      'search': {'value': 'abc', 'regex': 'true'}},
                '1': {'data': 'ip_address', 'name': '', 'searchable': 'true', 'orderable': 'true',
                      'search': {'value': '', 'regex': 'false'}},
                '2': {'data': 'username', 'name': '', 'searchable': 'true', 'orderable': 'true',
                      'search': {'value': '1234', 'regex': 'true'}},
                '3': {'data': 'type', 'name': '', 'searchable': 'true', 'orderable': 'true',
                      'search': {'value': 'hshs', 'regex': 'false'}}
            },
            'order': {'0': {'column': '0', 'dir': 'asc'}},
            'start': '0', 'length': '10',
            'search': {'value': 'jjj', 'regex': 'false'},
            '_': '1672804547475'
        }

    def test_get_order_by(self):
        parsed_request = get_django_datatable_query(self.sample_datatable_ajax_request)

        result = parsed_request.get_order_by()

        self.assertEqual(result, ['hostname'])

        parsed_request.order[0].direction = 'desc'

        result = parsed_request.get_order_by()

        self.assertEqual(result, ['-hostname'])

    # @skip("Test will fail, but the function should return the expected result")
    def test_query_filter(self):
        parsed_request = DjangoDTRequest(parsed_dict=self.parsed_request)

        result = parsed_request.get_db_query_filter()

        expected_result = Q(hostname__icontains='jjj') | \
                          Q(hostname__iregex='abc') | \
                          Q(ip_address__icontains='jjj') | \
                          Q(username__icontains='jjj') | \
                          Q(username__iregex='1234') | \
                          Q(type__icontains='jjj') | \
                          Q(type__icontains='hshs')

        assert_q_equal(result, expected_result)

    def test_query_filter_get_dicts(self):
        parsed_request = DjangoDTRequest(parsed_dict=self.parsed_request)

        result = parsed_request.get_db_query_filter(return_as_list_of_dicts=True)

        expected_result = [
            {'hostname__icontains': 'jjj'}, {'hostname__iregex': 'abc'}, {'ip_address__icontains': 'jjj'},
            {'username__icontains': 'jjj'}, {'username__iregex': '1234'}, {'type__icontains': 'jjj'},
            {'type__icontains': 'hshs'}
        ]

        self.assertEqual(result, expected_result)


    def test_get_dt_response(self):
        parsed_request = get_django_datatable_query(self.sample_datatable_ajax_request)

        count_result = 12
        total_result = 120
        filter_result = [1, 2, 3, 4, 5]
        error = 'some error'

        count_mock = mock.MagicMock()
        count_mock.__getitem__.return_value = filter_result
        count_mock.count.return_value = count_result

        order_mock = mock.Mock()
        order_mock.order_by.return_value = count_mock

        filter_count_mock = mock.Mock()
        filter_count_mock.filter.return_value = order_mock
        filter_count_mock.count.return_value = total_result

        model_class_mock = mock.Mock()
        model_class_mock.objects = filter_count_mock

        result = get_django_dt_response(parsed_request, model_class_mock, lambda x: x, error)

        results_transformed = result.convert_to_dt_response_dict()

        expected_result = {
            'data': filter_result,
            'recordsTotal': total_result,
            'recordsFiltered': count_result,
            'draw': parsed_request.draw,
            'error': error
        }

        self.assertEqual(expected_result, results_transformed)
        filter_count_mock.filter.assert_called_with(parsed_request.get_db_query_filter())
        order_mock.order_by.assert_called_with(*parsed_request.get_order_by())
