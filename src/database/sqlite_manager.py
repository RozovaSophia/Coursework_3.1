import sqlite3
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Универсальный менеджер базы данных (работает с SQLite)"""

    def __init__(self, db_path: str = "hh_vacancies.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.cur = self.conn.cursor()
        logger.info(f"✅ Подключение к SQLite базе: {db_path}")

    def create_tables(self):
        """Создание таблиц в базе данных"""
        try:
            # Таблица работодателей
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS employers (
                    employer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id INTEGER UNIQUE NOT NULL,
                    company_name TEXT NOT NULL,
                    description TEXT,
                    website TEXT,
                    open_vacancies INTEGER
                )
            """)

            # Таблица вакансий
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS vacancies (
                    vacancy_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employer_id INTEGER REFERENCES employers(employer_id) ON DELETE CASCADE,
                    vacancy_name TEXT NOT NULL,
                    salary_from INTEGER,
                    salary_to INTEGER,
                    currency TEXT,
                    salary_avg INTEGER,
                    city TEXT,
                    experience TEXT,
                    employment TEXT,
                    requirement TEXT,
                    responsibility TEXT,
                    url TEXT NOT NULL
                )
            """)

            self.conn.commit()
            logger.info("✅ Таблицы созданы успешно")
        except Exception as e:
            logger.error(f"❌ Ошибка создания таблиц: {e}")
            raise

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

            # Получаем employer_id
            self.cur.execute(
                "SELECT employer_id FROM employers WHERE company_id = ?",
                (int(company_data['id']),)
            )
            employer_id = self.cur.fetchone()[0]
            logger.info(f"✅ Добавлен работодатель: {company_data['name']} (ID: {employer_id})")
            return employer_id
        except Exception as e:
            logger.error(f"❌ Ошибка добавления работодателя: {e}")
            raise

    def insert_vacancy(self, employer_id: int, vacancy_data: dict):
        """Добавление вакансии в базу данных"""
        try:
            salary = vacancy_data.get('salary') or {}  # Защита от None
            salary_from = salary.get('from') if salary else None
            salary_to = salary.get('to') if salary else None
            currency = salary.get('currency') if salary else None

            # Расчет средней зарплаты
            salary_avg = None
            if salary_from and salary_to:
                salary_avg = (salary_from + salary_to) // 2
            elif salary_from:
                salary_avg = salary_from
            elif salary_to:
                salary_avg = salary_to

            # Защита от None в обязательных полях
            city = vacancy_data.get('area', {}).get('name', 'Не указан')
            experience = vacancy_data.get('experience', {}).get('name', 'Не указан')
            employment = vacancy_data.get('employment', {}).get('name', 'Не указан')

            self.cur.execute("""
                INSERT INTO vacancies 
                (employer_id, vacancy_name, salary_from, salary_to, currency, salary_avg, 
                 city, experience, employment, requirement, responsibility, url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                employer_id,
                vacancy_data['name'],
                salary_from,
                salary_to,
                currency,
                salary_avg,
                city,
                experience,
                employment,
                vacancy_data.get('snippet', {}).get('requirement', ''),
                vacancy_data.get('snippet', {}).get('responsibility', ''),
                vacancy_data['alternate_url']
            ))
            self.conn.commit()
        except Exception as e:
            logger.error(f"❌ Ошибка добавления вакансии: {e}")
            logger.error(f"   Данные вакансии: {vacancy_data.get('name')}")
            raise

    # Методы из задания
    def get_companies_and_vacancies_count(self) -> List[Tuple]:
        """Получает список всех компаний и количество вакансий у каждой компании"""
        self.cur.execute("""
            SELECT e.company_name, COUNT(v.vacancy_id) as vacancy_count
            FROM employers e
            LEFT JOIN vacancies v ON e.employer_id = v.employer_id
            GROUP BY e.company_name
            ORDER BY vacancy_count DESC
        """)
        return self.cur.fetchall()

    def get_all_vacancies(self) -> List[Tuple]:
        """Получает список всех вакансий с указанием названия компании, названия вакансии и зарплаты и ссылки на вакансию"""
        self.cur.execute("""
            SELECT 
                e.company_name,
                v.vacancy_name,
                COALESCE(v.salary_from, 0) as salary_from,
                COALESCE(v.salary_to, 0) as salary_to,
                v.currency,
                v.url
            FROM vacancies v
            JOIN employers e ON v.employer_id = e.employer_id
            ORDER BY e.company_name, v.vacancy_name
        """)
        return self.cur.fetchall()

    def get_avg_salary(self) -> float:
        """Получает среднюю зарплату по вакансиям"""
        self.cur.execute("""
            SELECT AVG(salary_avg) as avg_salary
            FROM vacancies
            WHERE salary_avg IS NOT NULL
        """)
        result = self.cur.fetchone()
        return round(result[0]) if result[0] else 0

    def get_vacancies_with_higher_salary(self) -> List[Tuple]:
        """Получает список всех вакансий, у которых зарплата выше средней по всем вакансиям"""
        avg_salary = self.get_avg_salary()
        self.cur.execute("""
            SELECT 
                e.company_name,
                v.vacancy_name,
                v.salary_avg,
                v.currency,
                v.url
            FROM vacancies v
            JOIN employers e ON v.employer_id = e.employer_id
            WHERE v.salary_avg > ?
            ORDER BY v.salary_avg DESC
        """, (avg_salary,))
        return self.cur.fetchall()

    def get_vacancies_with_keyword(self, keyword: str) -> List[Tuple]:
        """Получает список всех вакансий, в названии которых содержатся переданные в метод слова"""
        self.cur.execute("""
            SELECT 
                e.company_name,
                v.vacancy_name,
                v.salary_avg,
                v.currency,
                v.url
            FROM vacancies v
            JOIN employers e ON v.employer_id = e.employer_id
            WHERE LOWER(v.vacancy_name) LIKE LOWER(?)
            ORDER BY e.company_name, v.vacancy_name
        """, (f'%{keyword}%',))
        return self.cur.fetchall()

    def close(self):
        """Закрытие соединения с базой данных"""
        self.cur.close()
        self.conn.close()
        logger.info("✅ Соединение с базой данных закрыто")