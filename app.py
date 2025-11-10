import os
from flask import Flask, render_template, request
from apscheduler.schedulers.background import BackgroundScheduler

from logic import get_recipes_for_user, get_kaufland_promotions, get_lidl_promotions
import database as db

app = Flask(__name__)
db_conn = db.create_connection()
db.create_table(db_conn)


@app.route('/', methods=['GET', 'POST'])
def home():
    # "УМНА" ЛОГИКА ЗА ПРОВЕРКА НА DB
    current_products = db.get_recent_promotions(db_conn, [])

    if not current_products:
        print("⚠️ [App] Базата данни е празна! Стартирам принудително извличане на данни СЕГА...")
        daily_scrape_job()
    else:
        print("✅ [App] Базата данни е пълна (съдържа данни от днес). Продължавам.")

    if request.method == 'POST':
        try:
            print("🧠 [App] Получена POST заявка. Започвам генериране...")

            people = request.form.get('people', '2')
            budget_level = request.form.get('budget', 'Няма значение')

            preferences = [f"Бюджетно ниво: {budget_level}"]

            if request.form.get('veg') == 'yes':
                preferences.append('вегетарианско')
            if request.form.get('healthy') == 'yes':
                preferences.append('здравословно')

            other_prefs = request.form.getlist('preferences')
            preferences.extend(other_prefs)

            print(f"[App] Събрани предпочитания: {preferences}")

            selected_stores = request.form.getlist('stores')
            print(f"[App] Избрани магазини от потребителя: {selected_stores}")
            fridge_items = request.form.get('fridge_items', '')
            print(f"[App] Продукти в хладилника: {fridge_items or 'Няма'}")

            recipe_data = get_recipes_for_user(db_conn, people, preferences, selected_stores, fridge_items)

            print("✅ [App] Връщам JSON обект към HTML.")
            return render_template('index.html', recipe_data=recipe_data)

        except Exception as e:
            print(f"❌ [App] Грешка в POST заявката: {e}")
            return render_template('index.html', error=str(e))

    print("✅ [App] GET заявка. Показвам празната страница.")
    return render_template('index.html')


def daily_scrape_job():
    """ Задачата, която scheduler-ът ще изпълнява """
    print("⏰ [Scheduler] СТАРТ: Започвам ежедневното извличане на данни...")
    try:
        job_db_conn = db.create_connection()
        get_kaufland_promotions(job_db_conn)
        get_lidl_promotions(job_db_conn)
        job_db_conn.close()
        print("⏰ [Scheduler] ЗАВЪРШЕНО: Ежедневното извличане приключи.")
    except Exception as e:
        print(f"❌❌❌ [Scheduler] КРИТИЧНА ГРЕШКА В DAILY JOB: {e}")


if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(daily_scrape_job, 'cron', hour=3, minute=0)
    scheduler.start()
    print("⏰ [Scheduler] Scheduler-ът е стартиран. Задачата е насрочена за 3:00 сутринта.")

    # Връщаме липсващата функция, за да се напълни DB при първи старт.
    print("🚀 [App] Стартирам еднократно извличане на данни СЕГА...")
    daily_scrape_job()

    # Добавяме use_reloader=False, за да не се стартира всичко ДВА пъти
    app.run(debug=True, port=5000, use_reloader=False)