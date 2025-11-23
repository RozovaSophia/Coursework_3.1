from dataclasses import dataclass
from typing import Optional

@dataclass
class Vacancy:
    vacancy_id: Optional[int] = None
    employer_id: int = None
    vacancy_name: str = None
    salary_from: Optional[int] = None
    salary_to: Optional[int] = None
    currency: Optional[str] = None
    salary_avg: Optional[int] = None
    city: str = None
    experience: str = None
    employment: str = None
    requirement: Optional[str] = None
    responsibility: Optional[str] = None
    url: str = None