import pytest
from src.models.employer import Employer
from src.models.vacancy import Vacancy


class TestEmployer:
    """Тесты для модели Employer"""

    def test_employer_creation(self):
        """Тест создания объекта Employer"""
        employer = Employer(
            employer_id=1,
            company_id=15478,
            company_name="VK",
            description="Технологическая компания",
            website="https://vk.com",
            open_vacancies=50
        )

        assert employer.employer_id == 1
        assert employer.company_id == 15478
        assert employer.company_name == "VK"
        assert employer.description == "Технологическая компания"
        assert employer.website == "https://vk.com"
        assert employer.open_vacancies == 50

    def test_employer_default_values(self):
        """Тест значений по умолчанию для Employer"""
        employer = Employer(
            company_id=15478,
            company_name="VK"
        )

        assert employer.employer_id is None
        assert employer.description is None
        assert employer.website is None
        assert employer.open_vacancies == 0


class TestVacancy:
    """Тесты для модели Vacancy"""

    def test_vacancy_creation(self):
        """Тест создания объекта Vacancy"""
        vacancy = Vacancy(
            vacancy_id=1,
            employer_id=1,
            vacancy_name="Python Developer",
            salary_from=100000,
            salary_to=200000,
            currency="RUR",
            salary_avg=150000,
            city="Москва",
            experience="от 1 года до 3 лет",
            employment="полная занятость",
            requirement="Знание Python, Django",
            responsibility="Разработка backend",
            url="https://hh.ru/vacancy/123"
        )

        assert vacancy.vacancy_id == 1
        assert vacancy.employer_id == 1
        assert vacancy.vacancy_name == "Python Developer"
        assert vacancy.salary_from == 100000
        assert vacancy.salary_to == 200000
        assert vacancy.salary_avg == 150000
        assert vacancy.currency == "RUR"
        assert vacancy.city == "Москва"
        assert vacancy.experience == "от 1 года до 3 лет"
        assert vacancy.employment == "полная занятость"
        assert vacancy.requirement == "Знание Python, Django"
        assert vacancy.responsibility == "Разработка backend"
        assert vacancy.url == "https://hh.ru/vacancy/123"

    def test_vacancy_default_values(self):
        """Тест значений по умолчанию для Vacancy"""
        vacancy = Vacancy(
            employer_id=1,
            vacancy_name="Python Developer",
            city="Москва",
            experience="от 1 года до 3 лет",
            employment="полная занятость",
            url="https://hh.ru/vacancy/123"
        )

        assert vacancy.vacancy_id is None
        assert vacancy.salary_from is None
        assert vacancy.salary_to is None
        assert vacancy.salary_avg is None
        assert vacancy.currency is None
        assert vacancy.requirement is None
        assert vacancy.responsibility is None

    def test_vacancy_salary_calculation(self):
        """Тест расчета средней зарплаты (если логика в модели)"""
        # Этот тест может потребовать адаптации под вашу реализацию
        vacancy_with_both = Vacancy(
            employer_id=1,
            vacancy_name="Developer",
            salary_from=100000,
            salary_to=200000,
            city="Москва",
            experience="от 1 года до 3 лет",
            employment="полная занятость",
            url="https://hh.ru/vacancy/123"
        )

        vacancy_with_from_only = Vacancy(
            employer_id=1,
            vacancy_name="Developer",
            salary_from=150000,
            city="Москва",
            experience="от 1 года до 3 лет",
            employment="полная занятость",
            url="https://hh.ru/vacancy/123"
        )

        # Проверяем что поля установлены корректно
        assert vacancy_with_both.salary_from == 100000
        assert vacancy_with_both.salary_to == 200000
        assert vacancy_with_from_only.salary_from == 150000
        assert vacancy_with_from_only.salary_to is None