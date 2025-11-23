import requests
from typing import List, Dict, Optional


class HHAPI:
    def __init__(self):
        self.base_url = "https://api.hh.ru/"

    def get_employer(self, employer_id: str) -> Optional[Dict]:
        url = f"{self.base_url}employers/{employer_id}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return None

    def get_vacancies(self, employer_id: str) -> List[Dict]:
        url = f"{self.base_url}vacancies"
        params = {
            'employer_id': employer_id,
            'per_page': 100,
            'page': 0
        }
        vacancies = []

        while True:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                vacancies.extend(data['items'])

                if params['page'] >= data['pages'] - 1:
                    break
                params['page'] += 1
            else:
                break

        return vacancies