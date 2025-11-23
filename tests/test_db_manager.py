import pytest
import sqlite3
import os
from src.database.sqlite_manager import DatabaseManager
from src.models.employer import Employer
from src.models.vacancy import Vacancy


class TestDatabaseManager:
    """Тесты для менеджера базы данных"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.test_db_path = "test_vacancies.db"
        self.db = DatabaseManager(self.test_db_path)
        self.db.create_tables()

    def teardown_method(self):
        """Очистка после каждого теста"""
        self.db.close()
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def test_database_connection(self):
        """Тест подключения к базе данных"""
        assert self.db.conn is not None
        assert self.db.cur is not None

    def test_create_tables(self):
        """Тест создания таблиц"""
        # Проверяем что таблицы созданы
        self.db.cur.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN ('employers', 'vacancies')
        """)
        tables = self.db.cur.fetchall()

        assert len(tables) == 2
        table_names = [table[0] for table in tables]
        assert 'employers' in table_names
        assert 'vacancies' in table_names

    def insert_employer(self, company_data: dict) -> int:
        """Добавление работодателя в базу данных"""
        try:
            self.cur.execute("""
                INSERT OR REPLACE INTO employers 
                (company_id, company_name, description, website, open_vacancies)
                VALUES (?, ?, ?, ?, ?)
            """, (
                int(company_data['id']),
                company_data['name'],
                company_data.get('description', '')[:500],
                company_data.get('site_url', ''),
                company_data.get('open_vacancies', 0)
            ))
            self.conn.commit()

            # Всегда получаем актуальный employer_id
            self.cur.execute(
                "SELECT employer_id FROM employers WHERE company_id = ?",
                (int(company_data['id']),)
            )
            result = self.cur.fetchone()
            employer_id = result[0] if result else None

            if employer_id is None:
                raise ValueError("Failed to get employer_id after insert")

            logger.info(f"✅ Добавлен/обновлен работодатель: {company_data['name']} (ID: {employer_id})")
            return employer_id
        except Exception as e:
            logger.error(f"❌ Ошибка добавления работодателя: {e}")
            raise

    def test_insert_employer_duplicate(self):
        """Тест добавления дублирующегося работодателя"""
        company_data = {
            'id': '15478',
            'name': 'VK',
            'description': 'Старое описание',
            'site_url': 'https://old.vk.com',
            'open_vacancies': 10
        }

        # Первое добавление
        employer_id1 = self.db.insert_employer(company_data)

        # Обновленные данные (тот же company_id)
        updated_company_data = {
            'id': '15478',
            'name': 'VK Updated',
            'description': 'Новое описание',
            'site_url': 'https://new.vk.com',
            'open_vacancies': 50
        }

        # Второе добавление с тем же company_id
        employer_id2 = self.db.insert_employer(updated_company_data)

        # В SQLite с AUTOINCREMENT при REPLACE может создаться новый ID
        # Поэтому проверяем что в базе только одна запись с этим company_id
        self.db.cur.execute("SELECT COUNT(*) FROM employers WHERE company_id = ?", (15478,))
        count = self.db.cur.fetchone()[0]
        assert count == 1, f"Ожидалась 1 запись, но найдено {count}"

        # Проверяем что данные обновились (берем актуальную запись)
        self.db.cur.execute("SELECT * FROM employers WHERE company_id = ?", (15478,))
        result = self.db.cur.fetchone()

        assert result is not None
        assert result['company_name'] == 'VK Updated'
        assert result['description'] == 'Новое описание'
        assert result['website'] == 'https://new.vk.com'
        assert result['open_vacancies'] == 50

        # Логируем для отладки
        print(f"employer_id1: {employer_id1}, employer_id2: {employer_id2}")

    def test_insert_vacancy(self):
        """Тест добавления вакансии"""
        # Сначала добавляем работодателя
        company_data = {
            'id': '15478',
            'name': 'VK',
            'description': 'Технологическая компания',
            'site_url': 'https://vk.com',
            'open_vacancies': 50
        }
        employer_id = self.db.insert_employer(company_data)

        # Данные вакансии
        vacancy_data = {
            'name': 'Python Developer',
            'salary': {'from': 100000, 'to': 200000, 'currency': 'RUR'},
            'area': {'name': 'Москва'},
            'experience': {'name': 'от 1 года до 3 лет'},
            'employment': {'name': 'полная занятость'},
            'snippet': {
                'requirement': 'Знание Python, Django',
                'responsibility': 'Разработка backend'
            },
            'alternate_url': 'https://hh.ru/vacancy/123'
        }

        self.db.insert_vacancy(employer_id, vacancy_data)

        # Проверяем что вакансия добавлена
        self.db.cur.execute("SELECT * FROM vacancies WHERE employer_id = ?", (employer_id,))
        result = self.db.cur.fetchone()

        assert result is not None
        assert result['vacancy_name'] == 'Python Developer'
        assert result['salary_from'] == 100000
        assert result['salary_to'] == 200000
        assert result['salary_avg'] == 150000
        assert result['currency'] == 'RUR'
        assert result['city'] == 'Москва'
        assert result['experience'] == 'от 1 года до 3 лет'
        assert result['employment'] == 'полная занятость'
        assert result['requirement'] == 'Знание Python, Django'
        assert result['responsibility'] == 'Разработка backend'
        assert result['url'] == 'https://hh.ru/vacancy/123'

    def test_insert_vacancy_without_salary(self):
        """Тест добавления вакансии без зарплаты"""
        company_data = {
            'id': '15478',
            'name': 'VK',
            'description': 'Технологическая компания',
            'site_url': 'https://vk.com',
            'open_vacancies': 50
        }
        employer_id = self.db.insert_employer(company_data)

        vacancy_data = {
            'name': 'Python Developer',
            'salary': None,
            'area': {'name': 'Москва'},
            'experience': {'name': 'от 1 года до 3 лет'},
            'employment': {'name': 'полная занятость'},
            'snippet': {'requirement': '', 'responsibility': ''},
            'alternate_url': 'https://hh.ru/vacancy/123'
        }

        self.db.insert_vacancy(employer_id, vacancy_data)

        # Проверяем что вакансия добавлена с NULL зарплатой
        self.db.cur.execute("SELECT * FROM vacancies WHERE employer_id = ?", (employer_id,))
        result = self.db.cur.fetchone()

        assert result is not None
        assert result['vacancy_name'] == 'Python Developer'
        assert result['salary_from'] is None
        assert result['salary_to'] is None
        assert result['salary_avg'] is None
        assert result['currency'] is None

    def test_get_companies_and_vacancies_count(self):
        """Тест получения компаний и количества вакансий"""
        # Добавляем тестовые данные
        company1_data = {'id': '1', 'name': 'Company 1', 'open_vacancies': 5}
        company2_data = {'id': '2', 'name': 'Company 2', 'open_vacancies': 3}

        employer_id1 = self.db.insert_employer(company1_data)
        employer_id2 = self.db.insert_employer(company2_data)

        # Добавляем вакансии
        vacancy_data = {
            'name': 'Developer',
            'salary': {'from': 100000, 'to': 200000, 'currency': 'RUR'},
            'area': {'name': 'Москва'},
            'experience': {'name': 'от 1 года до 3 лет'},
            'employment': {'name': 'полная занятость'},
            'snippet': {'requirement': '', 'responsibility': ''},
            'alternate_url': 'https://hh.ru/vacancy/1'
        }

        # 2 вакансии для компании 1, 1 вакансия для компании 2
        self.db.insert_vacancy(employer_id1, vacancy_data)
        self.db.insert_vacancy(employer_id1, vacancy_data)
        self.db.insert_vacancy(employer_id2, vacancy_data)

        result = self.db.get_companies_and_vacancies_count()

        assert len(result) == 2
        # Проверяем что компании отсортированы по количеству вакансий
        assert result[0][1] == 2  # Company 1: 2 вакансии
        assert result[1][1] == 1  # Company 2: 1 вакансия

    def test_get_all_vacancies(self):
        """Тест получения всех вакансий"""
        company_data = {'id': '1', 'name': 'Company 1', 'open_vacancies': 5}
        employer_id = self.db.insert_employer(company_data)

        vacancy_data = {
            'name': 'Python Developer',
            'salary': {'from': 100000, 'to': 200000, 'currency': 'RUR'},
            'area': {'name': 'Москва'},
            'experience': {'name': 'от 1 года до 3 лет'},
            'employment': {'name': 'полная занятость'},
            'snippet': {'requirement': '', 'responsibility': ''},
            'alternate_url': 'https://hh.ru/vacancy/1'
        }

        self.db.insert_vacancy(employer_id, vacancy_data)

        vacancies = self.db.get_all_vacancies()

        assert len(vacancies) == 1
        vacancy = vacancies[0]
        assert vacancy[0] == 'Company 1'  # company_name
        assert vacancy[1] == 'Python Developer'  # vacancy_name
        assert vacancy[2] == 100000  # salary_from
        assert vacancy[3] == 200000  # salary_to
        assert vacancy[4] == 'RUR'  # currency
        assert 'hh.ru/vacancy/1' in vacancy[5]  # url

    def test_get_avg_salary(self):
        """Тест расчета средней зарплаты"""
        company_data = {'id': '1', 'name': 'Company 1', 'open_vacancies': 5}
        employer_id = self.db.insert_employer(company_data)

        vacancy_data1 = {
            'name': 'Developer 1',
            'salary': {'from': 100000, 'to': 200000, 'currency': 'RUR'},
            'area': {'name': 'Москва'},
            'experience': {'name': 'от 1 года до 3 лет'},
            'employment': {'name': 'полная занятость'},
            'snippet': {'requirement': '', 'responsibility': ''},
            'alternate_url': 'https://hh.ru/vacancy/1'
        }

        vacancy_data2 = {
            'name': 'Developer 2',
            'salary': {'from': 150000, 'to': 250000, 'currency': 'RUR'},
            'area': {'name': 'Москва'},
            'experience': {'name': 'от 1 года до 3 лет'},
            'employment': {'name': 'полная занятость'},
            'snippet': {'requirement': '', 'responsibility': ''},
            'alternate_url': 'https://hh.ru/vacancy/2'
        }

        self.db.insert_vacancy(employer_id, vacancy_data1)
        self.db.insert_vacancy(employer_id, vacancy_data2)

        avg_salary = self.db.get_avg_salary()

        # (150000 + 200000) / 2 = 175000
        expected_avg = (150000 + 200000) // 2
        assert avg_salary == expected_avg

    def test_get_vacancies_with_higher_salary(self):
        """Тест получения вакансий с зарплатой выше средней"""
        company_data = {'id': '1', 'name': 'Company 1', 'open_vacancies': 5}
        employer_id = self.db.insert_employer(company_data)

        # Вакансии с разными зарплатами
        vacancies_data = [
            {'name': 'Low Salary', 'salary': {'from': 50000, 'to': 80000, 'currency': 'RUR'}},
            {'name': 'Medium Salary', 'salary': {'from': 100000, 'to': 150000, 'currency': 'RUR'}},
            {'name': 'High Salary', 'salary': {'from': 200000, 'to': 300000, 'currency': 'RUR'}}
        ]

        base_vacancy = {
            'area': {'name': 'Москва'},
            'experience': {'name': 'от 1 года до 3 лет'},
            'employment': {'name': 'полная занятость'},
            'snippet': {'requirement': '', 'responsibility': ''},
            'alternate_url': 'https://hh.ru/vacancy/'
        }

        for i, salary_data in enumerate(vacancies_data):
            vacancy = base_vacancy.copy()
            vacancy.update(salary_data)
            vacancy['alternate_url'] += str(i)
            self.db.insert_vacancy(employer_id, vacancy)

        high_salary_vacancies = self.db.get_vacancies_with_higher_salary()

        # Средняя зарплата примерно 141666, поэтому только последняя вакансия должна быть выше
        assert len(high_salary_vacancies) == 1
        assert high_salary_vacancies[0][1] == 'High Salary'  # vacancy_name

    def test_get_vacancies_with_keyword(self):
        """Тест поиска вакансий по ключевому слову"""
        company_data = {'id': '1', 'name': 'Company 1', 'open_vacancies': 5}
        employer_id = self.db.insert_employer(company_data)

        vacancies_data = [
            {'name': 'Python Developer', 'salary': {'from': 100000, 'to': 200000, 'currency': 'RUR'}},
            {'name': 'Java Developer', 'salary': {'from': 100000, 'to': 200000, 'currency': 'RUR'}},
            {'name': 'Senior Python Engineer', 'salary': {'from': 200000, 'to': 300000, 'currency': 'RUR'}}
        ]

        base_vacancy = {
            'area': {'name': 'Москва'},
            'experience': {'name': 'от 1 года до 3 лет'},
            'employment': {'name': 'полная занятость'},
            'snippet': {'requirement': '', 'responsibility': ''},
            'alternate_url': 'https://hh.ru/vacancy/'
        }

        for i, vacancy_data in enumerate(vacancies_data):
            vacancy = base_vacancy.copy()
            vacancy.update(vacancy_data)
            vacancy['alternate_url'] += str(i)
            self.db.insert_vacancy(employer_id, vacancy)

        python_vacancies = self.db.get_vacancies_with_keyword('python')

        assert len(python_vacancies) == 2
        vacancy_names = [vacancy[1] for vacancy in python_vacancies]
        assert 'Python Developer' in vacancy_names
        assert 'Senior Python Engineer' in vacancy_names
        assert 'Java Developer' not in vacancy_names

    def test_get_vacancies_with_keyword_case_insensitive(self):
        """Тест поиска вакансий без учета регистра"""
        company_data = {'id': '1', 'name': 'Company 1', 'open_vacancies': 5}
        employer_id = self.db.insert_employer(company_data)

        vacancy_data = {
            'name': 'PYTHON Developer',
            'salary': {'from': 100000, 'to': 200000, 'currency': 'RUR'},
            'area': {'name': 'Москва'},
            'experience': {'name': 'от 1 года до 3 лет'},
            'employment': {'name': 'полная занятость'},
            'snippet': {'requirement': '', 'responsibility': ''},
            'alternate_url': 'https://hh.ru/vacancy/1'
        }

        self.db.insert_vacancy(employer_id, vacancy_data)

        # Поиск в нижнем регистре
        vacancies_lower = self.db.get_vacancies_with_keyword('python')
        # Поиск в верхнем регистре
        vacancies_upper = self.db.get_vacancies_with_keyword('PYTHON')

        assert len(vacancies_lower) == 1
        assert len(vacancies_upper) == 1
        assert vacancies_lower[0][1] == 'PYTHON Developer'
        assert vacancies_upper[0][1] == 'PYTHON Developer'