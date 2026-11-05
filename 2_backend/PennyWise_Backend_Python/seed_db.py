"""
PennyWise Database Seeding Script.
Initializes tables and inserts realistic sample records for manual testing and demonstration.
Usage:
    python seed_db.py
"""

import sys
import logging
from datetime import datetime, date
from database import initialize_schema_if_needed, execute_query, test_connection

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed_db")


def seed_database():
    """Seed categories, sample transactions, and monthly budgets."""
    logger.info("Checking database connection...")
    healthy, msg = test_connection()
    if not healthy:
        logger.error("Failed to connect to MySQL: %s", msg)
        logger.error("Please ensure MySQL is running and .env has correct credentials.")
        sys.exit(1)

    logger.info("Connected to MySQL. Initializing schema if needed...")
    initialize_schema_if_needed()

    current_year = date.today().year
    current_month = date.today().month

    logger.info("Seeding realistic transactions and budgets for %02d/%d...", current_month, current_year)

    # 1. Fetch categories
    cats = execute_query("SELECT category_id, name, type FROM categories", fetch_all=True)
    cat_map = {c["name"]: c["category_id"] for c in cats}

    # Ensure required default categories exist
    required_cats = [
        ("Salary", "Income", "Monthly employment salary"),
        ("Freelancing", "Income", "Side freelancing contracts"),
        ("Groceries", "Expense", "Provisions and daily food items"),
        ("Rent", "Expense", "Monthly apartment rent"),
        ("Transportation", "Expense", "Fuel, public transit & cabs"),
        ("Utilities", "Expense", "Electricity, water and internet bills"),
        ("Entertainment", "Expense", "Movies, dinners and hobbies")
    ]
    for name, ctype, desc in required_cats:
        if name not in cat_map:
            cid = execute_query(
                "INSERT INTO categories (name, type, description) VALUES (%s, %s, %s)",
                (name, ctype, desc),
                commit=True
            )
            cat_map[name] = cid

    # 2. Seed Budgets
    sample_budgets = [
        (cat_map["Groceries"], current_month, current_year, 5000.00),
        (cat_map["Transportation"], current_month, current_year, 3500.00),
        (cat_map["Entertainment"], current_month, current_year, 2000.00),
        (cat_map["Rent"], current_month, current_year, 20000.00),
    ]

    for cid, m, y, amt in sample_budgets:
        execute_query(
            """
            INSERT INTO budgets (category_id, month, year, budget_amount)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE budget_amount = VALUES(budget_amount)
            """,
            (cid, m, y, amt),
            commit=True
        )

    # 3. Seed Sample Transactions
    # Clear existing transactions for this month to avoid infinite accumulation on re-seed
    execute_query(
        "DELETE FROM transactions WHERE MONTH(transaction_date) = %s AND YEAR(transaction_date) = %s",
        (current_month, current_year),
        commit=True
    )

    sample_txs = [
        (f"{current_year}-{current_month:02d}-01", "Income", cat_map["Salary"], 85000.00, "Monthly Salary"),
        (f"{current_year}-{current_month:02d}-02", "Expense", cat_map["Rent"], 20000.00, "Apartment Rent"),
        (f"{current_year}-{current_month:02d}-03", "Expense", cat_map["Groceries"], 3200.00, "Supermarket provisions"),
        (f"{current_year}-{current_month:02d}-04", "Expense", cat_map["Transportation"], 1200.00, "Fuel & Toll"),
        (f"{current_year}-{current_month:02d}-05", "Income", cat_map["Freelancing"], 15000.00, "Web design freelance contract"),
        (f"{current_year}-{current_month:02d}-06", "Expense", cat_map["Groceries"], 2600.00, "Organic store vegetables & fruits"), # Groceries now 5800 > 5000 (Over budget!)
        (f"{current_year}-{current_month:02d}-07", "Expense", cat_map["Utilities"], 2400.00, "Electricity & Internet bill"),
        (f"{current_year}-{current_month:02d}-08", "Expense", cat_map["Transportation"], 1500.00, "Monthly Metro Pass"),
        (f"{current_year}-{current_month:02d}-09", "Expense", cat_map["Entertainment"], 1400.00, "Weekend dinner & movie"),
    ]

    for tx_date, tx_type, cid, amt, desc in sample_txs:
        execute_query(
            "INSERT INTO transactions (transaction_date, transaction_type, category_id, amount, description) VALUES (%s, %s, %s, %s, %s)",
            (tx_date, tx_type, cid, amt, desc),
            commit=True
        )

    logger.info("Successfully seeded database with %d categories, %d budgets, and %d transactions!",
                len(cat_map), len(sample_budgets), len(sample_txs))
    logger.info("Note: 'Groceries' budget is intentionally set to ₹5,000 with ₹5,800 spent to demonstrate budget overrun detection.")


if __name__ == "__main__":
    seed_database()
