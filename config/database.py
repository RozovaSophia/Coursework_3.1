from dataclasses import dataclass


@dataclass
class DBConfig:
    db_type: str = "sqlite"
    dbname: str = "hh_vacancies.db"

    user: str = ""
    password: str = ""
    host: str = ""
    port: int = 0


COMPANIES = [
    '15478',  # VK
    '1740',  # Яндекс
    '1122462',  # Сбер
    '78638',  # Тинькофф
    '3529',  # СБИС
    '3776',  # МТС
    '4181',  # Банк ВТБ
    '907345',  # Ozon
    '4934',  # Билайн
    '1057',  # Касперский
    '87021',  # Wildberries
    '39305'  # Газпром нефть
]