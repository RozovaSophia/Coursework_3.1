import pytest
import requests
from unittest.mock import Mock, patch
from src.api.hh_api import HHAPI


class TestHHAPI:
    """Тесты для HH API клиента"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.api = HHAPI()

    def test_api_initialization(self):
        """Тест инициализации API клиента"""
        assert self.api.base_url == "https://api.hh.ru/"

    @patch('src.api.hh_api.requests.get')
    def test_get_employer_success(self, mock_get):
        """Тест успешного получения данных работодателя"""
        # Мокаем ответ API
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': '15478',
            'name': 'VK',
            'description': 'Технологическая компания',
            'site_url': 'https://vk.com',
            'open_vacancies': 50
        }
        mock_get.return_value = mock_response

        result = self.api.get_employer('15478')

        assert result is not None
        assert result['id'] == '15478'
        assert result['name'] == 'VK'
        assert result['description'] == 'Технологическая компания'
        mock_get.assert_called_once_with('https://api.hh.ru/employers/15478')

    @patch('src.api.hh_api.requests.get')
    def test_get_employer_not_found(self, mock_get):
        """Тест случая когда работодатель не найден"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = self.api.get_employer('99999')

        assert result is None
        mock_get.assert_called_once_with('https://api.hh.ru/employers/99999')

    @patch('src.api.hh_api.requests.get')
    def test_get_employer_api_error(self, mock_get):
        """Тест обработки ошибки API"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        result = self.api.get_employer('15478')

        assert result is None

    @patch('src.api.hh_api.requests.get')
    def test_get_vacancies_success(self, mock_get):
        """Тест успешного получения вакансий"""
        # Мокаем ответ с одной страницей
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'items': [
                {
                    'id': '1',
                    'name': 'Python Developer',
                    'salary': {'from': 100000, 'to': 200000, 'currency': 'RUR'},
                    'area': {'name': 'Москва'},
                    'experience': {'name': 'от 1 года до 3 лет'},
                    'employment': {'name': 'полная занятость'},
                    'snippet': {'requirement': 'Знание Python', 'responsibility': 'Разработка'},
                    'alternate_url': 'https://hh.ru/vacancy/1'
                }
            ],
            'pages': 1,
            'page': 0
        }
        mock_get.return_value = mock_response

        vacancies = self.api.get_vacancies('15478')

        assert len(vacancies) == 1
        assert vacancies[0]['name'] == 'Python Developer'
        assert vacancies[0]['salary']['from'] == 100000
        mock_get.assert_called_once()

    @patch('src.api.hh_api.requests.get')
    def test_get_vacancies_multiple_pages(self, mock_get):
        """Тест получения вакансий с нескольких страниц"""
        # Мокаем ответы для двух страниц
        mock_response_page1 = Mock()
        mock_response_page1.status_code = 200
        mock_response_page1.json.return_value = {
            'items': [{'id': '1', 'name': 'Vacancy 1'}],
            'pages': 2,
            'page': 0
        }

        mock_response_page2 = Mock()
        mock_response_page2.status_code = 200
        mock_response_page2.json.return_value = {
            'items': [{'id': '2', 'name': 'Vacancy 2'}],
            'pages': 2,
            'page': 1
        }

        mock_get.side_effect = [mock_response_page1, mock_response_page2]

        vacancies = self.api.get_vacancies('15478')

        assert len(vacancies) == 2
        assert vacancies[0]['name'] == 'Vacancy 1'
        assert vacancies[1]['name'] == 'Vacancy 2'
        assert mock_get.call_count == 2

    @patch('src.api.hh_api.requests.get')
    def test_get_vacancies_api_error(self, mock_get):
        """Тест обработки ошибки при получении вакансий"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        vacancies = self.api.get_vacancies('15478')

        assert vacancies == []
        mock_get.assert_called_once()

    @patch('src.api.hh_api.requests.get')
    def test_get_vacancies_without_salary(self, mock_get):
        """Тест получения вакансий без указания зарплаты"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'items': [
                {
                    'id': '1',
                    'name': 'Python Developer',
                    'salary': None,
                    'area': {'name': 'Москва'},
                    'experience': {'name': 'от 1 года до 3 лет'},
                    'employment': {'name': 'полная занятость'},
                    'snippet': {'requirement': 'Знание Python', 'responsibility': 'Разработка'},
                    'alternate_url': 'https://hh.ru/vacancy/1'
                }
            ],
            'pages': 1,
            'page': 0
        }
        mock_get.return_value = mock_response

        vacancies = self.api.get_vacancies('15478')

        assert len(vacancies) == 1
        assert vacancies[0]['salary'] is None