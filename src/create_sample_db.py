"""
F5 uchun namunaviy SQLite baza yaratish (bir martalik skript).
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "company.db"


def create_sample_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.executescript("""
    DROP TABLE IF EXISTS employees;
    DROP TABLE IF EXISTS sales;

    CREATE TABLE employees (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        department TEXT NOT NULL,
        hire_date TEXT NOT NULL,
        salary INTEGER NOT NULL
    );

    CREATE TABLE sales (
        id INTEGER PRIMARY KEY,
        product TEXT NOT NULL,
        region TEXT NOT NULL,
        amount INTEGER NOT NULL,
        sale_date TEXT NOT NULL
    );
    """)

    employees = [
        ("Aziz Karimov", "Sales", "2022-03-01", 4500),
        ("Dilnoza Yusupova", "Engineering", "2021-07-15", 6200),
        ("Sardor Aliyev", "Sales", "2023-01-10", 4100),
        ("Malika Tosheva", "Marketing", "2020-11-20", 5000),
        ("Jasur Nazarov", "Engineering", "2022-09-05", 5800),
        ("Nilufar Rashidova", "Support", "2023-05-18", 3600),
    ]
    cur.executemany(
        "INSERT INTO employees (name, department, hire_date, salary) VALUES (?, ?, ?, ?)",
        employees,
    )

    sales = [
        ("Pro Plan", "Tashkent", 1200, "2026-01-15"),
        ("Pro Plan", "Samarqand", 800, "2026-01-20"),
        ("Basic Plan", "Tashkent", 400, "2026-02-02"),
        ("Enterprise Plan", "Tashkent", 5000, "2026-02-10"),
        ("Pro Plan", "Buxoro", 950, "2026-02-14"),
        ("Basic Plan", "Samarqand", 300, "2026-03-01"),
        ("Enterprise Plan", "Andijon", 4700, "2026-03-05"),
        ("Pro Plan", "Tashkent", 1100, "2026-03-18"),
    ]
    cur.executemany(
        "INSERT INTO sales (product, region, amount, sale_date) VALUES (?, ?, ?, ?)",
        sales,
    )

    conn.commit()
    conn.close()
    print(f"Namunaviy baza yaratildi: {DB_PATH}")


if __name__ == "__main__":
    create_sample_db()