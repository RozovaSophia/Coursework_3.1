from config.database import DBConfig, COMPANIES
from src.api.hh_api import HHAPI
from src.database.sqlite_manager import DatabaseManager
import logging
import time

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(message)s')


def main():
    config = DBConfig()

    try:
        # Используем SQLite
        db = DatabaseManager(config.dbname)
        db.create_tables()

        api = HHAPI()

        print("🚀 Начинаем сбор данных с hh.ru...")

        total_vacancies = 0
        successful_companies = 0

        for i, company_id in enumerate(COMPANIES, 1):
            print(f"\n[{i}/{len(COMPANIES)}] 🔄 Обрабатываем компанию {company_id}...")

            company_data = api.get_employer(company_id)

            if company_data:
                employer_id = db.insert_employer(company_data)
                vacancies = api.get_vacancies(company_id)

                if vacancies:
                    successful_vacancies = 0
                    for vacancy in vacancies:
                        try:
                            db.insert_vacancy(employer_id, vacancy)
                            successful_vacancies += 1
                        except Exception as e:
                            print(f"   ⚠️ Пропущена вакансия: {vacancy.get('name', 'Unknown')} - {e}")

                    total_vacancies += successful_vacancies
                    print(f"   ✅ Добавлено {successful_vacancies}/{len(vacancies)} вакансий для {company_data['name']}")
                    successful_companies += 1
                else:
                    print(f"   ℹ️ Нет вакансий для {company_data['name']}")
            else:
                print(f"   ❌ Не удалось получить данные для компании {company_id}")

            # Небольшая пауза чтобы не нагружать API
            time.sleep(0.5)

        # Показываем результаты
        print("\n" + "=" * 50)
        print("📊 ФИНАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
        print("=" * 50)

        print(f"\n✅ Успешно обработано: {successful_companies}/{len(COMPANIES)} компаний")
        print(f"📁 Всего вакансий собрано: {total_vacancies}")

        if successful_companies > 0:
            print("\n🏢 КОМПАНИИ И КОЛИЧЕСТВО ВАКАНСИЙ:")
            companies_data = db.get_companies_and_vacancies_count()
            for company, count in companies_data:
                print(f"  {company}: {count} вакансий")

            avg_salary = db.get_avg_salary()
            print(f"\n💰 СРЕДНЯЯ ЗАРПЛАТА: {avg_salary} RUB")

            print(f"\n📈 ВАКАНСИИ С ЗАРПЛАТОЙ ВЫШЕ СРЕДНЕЙ ({avg_salary} RUB):")
            high_salary_vacancies = db.get_vacancies_with_higher_salary()
            for company, vacancy, salary, currency, url in high_salary_vacancies[:5]:
                print(f"  {company} - {vacancy}: {salary} {currency}")

            print(f"\n🐍 ВАКАНСИИ С 'PYTHON' В НАЗВАНИИ:")
            python_vacancies = db.get_vacancies_with_keyword('python')
            for company, vacancy, salary, currency, url in python_vacancies[:3]:
                print(f"  {company} - {vacancy}: {salary} {currency}")
        else:
            print("\n😞 Не удалось собрать данные ни по одной компании")

        db.close()
        print(f"\n🎉 Готово! Данные сохранены в файл: {config.dbname}")

    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()