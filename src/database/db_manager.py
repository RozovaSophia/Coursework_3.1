import psycopg2
from typing import List, Tuple


class DBManager:
    def __init__(self, dbname: str, user: str, password: str, host: str, port: str):
        self.conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
        self.cur = self.conn.cursor()

    def get_companies_and_vacancies_count(self) -> List[Tuple]:
        query = """
            SELECT e.company_name, COUNT(v.vacancy_id) as vacancy_count
            FROM employers e
            LEFT JOIN vacancies v ON e.employer_id = v.employer_id
            GROUP BY e.company_name
            ORDER BY vacancy_count DESC
        """
        self.cur.execute(query)
        return self.cur.fetchall()

    def get_all_vacancies(self) -> List[Tuple]:
        query = """
            SELECT 
                e.company_name,
                v.vacancy_name,
                COALESCE(v.salary_from, 0),
                COALESCE(v.salary_to, 0),
                v.currency,
                v.url
            FROM vacancies v
            JOIN employers e ON v.employer_id = e.employer_id
            ORDER BY e.company_name, v.vacancy_name
        """
        self.cur.execute(query)
        return self.cur.fetchall()

    def get_avg_salary(self) -> float:
        query = """
            SELECT AVG(salary_avg) as avg_salary
            FROM vacancies
            WHERE salary_avg IS NOT NULL
        """
        self.cur.execute(query)
        result = self.cur.fetchone()
        return round(result[0]) if result[0] else 0

    def get_vacancies_with_higher_salary(self) -> List[Tuple]:
        avg_salary = self.get_avg_salary()
        query = """
            SELECT 
                e.company_name,
                v.vacancy_name,
                v.salary_avg,
                v.currency,
                v.url
            FROM vacancies v
            JOIN employers e ON v.employer_id = e.employer_id
            WHERE v.salary_avg > %s
            ORDER BY v.salary_avg DESC
        """
        self.cur.execute(query, (avg_salary,))
        return self.cur.fetchall()

    def get_vacancies_with_keyword(self, keyword: str) -> List[Tuple]:
        query = """
            SELECT 
                e.company_name,
                v.vacancy_name,
                v.salary_avg,
                v.currency,
                v.url
            FROM vacancies v
            JOIN employers e ON v.employer_id = e.employer_id
            WHERE LOWER(v.vacancy_name) LIKE LOWER(%s)
            ORDER BY e.company_name, v.vacancy_name
        """
        self.cur.execute(query, (f'%{keyword}%',))
        return self.cur.fetchall()

    def close(self):
        self.cur.close()
        self.conn.close()