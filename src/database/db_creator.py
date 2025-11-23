import psycopg2
from src.models import Employer, Vacancy


class DBCreator:
    def __init__(self, dbname: str, user: str, password: str, host: str, port: str):
        self.conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
        self.cur = self.conn.cursor()

    def create_tables(self):
        """Создание таблиц в базе данных"""
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS employers (
                employer_id SERIAL PRIMARY KEY,
                company_id INTEGER UNIQUE NOT NULL,
                company_name VARCHAR(255) NOT NULL,
                description TEXT,
                website VARCHAR(255),
                open_vacancies INTEGER
            )
        """)

        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS vacancies (
                vacancy_id SERIAL PRIMARY KEY,
                employer_id INTEGER REFERENCES employers(employer_id) ON DELETE CASCADE,
                vacancy_name VARCHAR(255) NOT NULL,
                salary_from INTEGER,
                salary_to INTEGER,
                currency VARCHAR(10),
                salary_avg INTEGER,
                city VARCHAR(100),
                experience VARCHAR(100),
                employment VARCHAR(100),
                requirement TEXT,
                responsibility TEXT,
                url VARCHAR(255) NOT NULL
            )
        """)
        self.conn.commit()

    def insert_employer(self, company_data: dict) -> int:
        """Добавление работодателя в базу данных"""
        self.cur.execute("""
            INSERT INTO employers (company_id, company_name, description, website, open_vacancies)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (company_id) DO UPDATE SET
                company_name = EXCLUDED.company_name,
                description = EXCLUDED.description,
                website = EXCLUDED.website,
                open_vacancies = EXCLUDED.open_vacancies
            RETURNING employer_id
        """, (
            company_data['id'],
            company_data['name'],
            company_data.get('description', '')[:500],
            company_data.get('site_url', ''),
            company_data.get('open_vacancies', 0)
        ))
        employer_id = self.cur.fetchone()[0]
        self.conn.commit()
        return employer_id

    def insert_vacancy(self, employer_id: int, vacancy_data: dict):
        """Добавление вакансии в базу данных"""
        salary = vacancy_data.get('salary')
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

        self.cur.execute("""
            INSERT INTO vacancies 
            (employer_id, vacancy_name, salary_from, salary_to, currency, salary_avg, 
             city, experience, employment, requirement, responsibility, url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            employer_id,
            vacancy_data['name'],
            salary_from,
            salary_to,
            currency,
            salary_avg,
            vacancy_data['area']['name'],
            vacancy_data['experience']['name'],
            vacancy_data['employment']['name'],
            vacancy_data.get('snippet', {}).get('requirement', ''),
            vacancy_data.get('snippet', {}).get('responsibility', ''),
            vacancy_data['alternate_url']
        ))
        self.conn.commit()

    def close(self):
        self.cur.close()
        self.conn.close()