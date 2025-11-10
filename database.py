import sqlite3
import datetime
from typing import List, Dict, Any

DATABASE_NAME = 'products.db'

def create_connection():
    """ Създава връзка с SQLite базата данни """
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME, check_same_thread=False)
    except sqlite3.Error as e:
        print(f"Грешка при свързване с SQLite: {e}")
    return conn

def create_table(conn):
    """ Създава таблицата за продукти, ако не съществува """
    try:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS promotions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                store TEXT NOT NULL,
                scraped_at DATE NOT NULL
            );
        """)
        conn.commit()
        print("[DB] Таблица 'promotions' е проверена/създадена.")
    except sqlite3.Error as e:
        print(f"Грешка при създаване на таблица: {e}")

def clear_old_promotions(conn, store_name: str):
    """ Изтрива ВЧЕРАШНИТЕ промоции за даден магазин, преди да добави новите """
    try:
        today = datetime.date.today()
        c = conn.cursor()
        c.execute("DELETE FROM promotions WHERE store = ? AND scraped_at != ?", (store_name, today))
        conn.commit()
        print(f"[DB] Изчистени са стари промоции за '{store_name}'.")
    except sqlite3.Error as e:
        print(f"Грешка при изчистване на стари промоции: {e}")

def add_promotions(conn, products: List[Dict[str, Any]], store_name: str):
    """ Добавя списък с продукти в базата данни """
    if not products:
        return

    print(f"[DB] Записвам {len(products)} продукта от '{store_name}' в базата данни...")

    clear_old_promotions(conn, store_name)

    try:
        today = datetime.date.today()
        c = conn.cursor()

        products_to_insert = [(p['name'], store_name, today) for p in products]

        c.executemany("INSERT INTO promotions (name, store, scraped_at) VALUES (?, ?, ?)", products_to_insert)
        conn.commit()
        print(f"[DB] Успешно добавени {len(products_to_insert)} продукта.")
    except sqlite3.Error as e:
        print(f"Грешка при добавяне на продукти: {e}")

def get_recent_promotions(conn, stores: List[str]) -> List[Dict[str, Any]]:
    """
    Взима ВСИЧКИ промоции, извлечени днес.
    Ако списъкът 'stores' НЕ е празен, филтрира само за тези магазини.
    """
    try:
        today = datetime.date.today()
        c = conn.cursor()

        sql = "SELECT name, store FROM promotions WHERE scraped_at = ?"
        params = [today]

        if stores:
            placeholders = ', '.join(['?'] * len(stores))
            sql += f" AND store IN ({placeholders})"
            params.extend(stores)

        c.execute(sql, params)

        rows = c.fetchall()
        products = [{"name": row[0], "store": row[1]} for row in rows]
        return products
    except sqlite3.Error as e:
        print(f"Грешка при извличане на промоции: {e}")
        return []