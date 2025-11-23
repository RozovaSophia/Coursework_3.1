from dataclasses import dataclass
from typing import Optional

@dataclass
class Employer:
    employer_id: Optional[int] = None
    company_id: int = None
    company_name: str = None
    description: Optional[str] = None
    website: Optional[str] = None
    open_vacancies: int = 0