# PennyWise Database Contract Specification

This document defines the schema contract between the **Backend Module** and the **Database Module** for the **PennyWise – Home Budget Management and Expense Analysis System**.

---

## 1. Overview & Guidelines for Database Teammate

The backend communicates with MySQL using standard parameterized SQL queries via `mysql-connector-python`.
To ensure seamless integration:
1. Table names: `categories`, `transactions`, `budgets`.
2. Primary keys are auto-incrementing integer IDs (`category_id`, `transaction_id`, `budget_id`).
3. Foreign key constraints ensure relational integrity.
4. Monetary amounts use `DECIMAL(12, 2)` to prevent floating-point rounding errors.
5. Dates use standard SQL `DATE` (`YYYY-MM-DD`).

If you adjust any table or column names, please notify the backend teammate. All SQL queries in `PennyWise_Backend` are isolated in `services/` and `database.py`, making renaming straightforward.

---

## 2. Table Specifications

### 2.1 Table: `categories`
Stores income and expense classification categories.

| Column | Data Type | Constraints | Description |
|---|---|---|---|
| `category_id` | `INT` | `PRIMARY KEY AUTO_INCREMENT` | Unique identifier for category |
| `name` | `VARCHAR(50)` | `NOT NULL` | Name of the category (e.g. 'Groceries') |
| `type` | `ENUM('Income', 'Expense')` | `NOT NULL` | Whether category is for Income or Expense |
| `description` | `VARCHAR(255)` | `NULL` | Optional description or notes |
| `created_at` | `TIMESTAMP` | `DEFAULT CURRENT_TIMESTAMP` | Creation timestamp |

**Indexes & Constraints:**
- `UNIQUE KEY (name, type)`: Prevents duplicate category names under the same type.

---

### 2.2 Table: `transactions`
Stores manual entries of income and expense transactions.

| Column | Data Type | Constraints | Description |
|---|---|---|---|
| `transaction_id` | `INT` | `PRIMARY KEY AUTO_INCREMENT` | Unique transaction identifier |
| `transaction_date` | `DATE` | `NOT NULL` | Date when transaction occurred (`YYYY-MM-DD`) |
| `transaction_type` | `ENUM('Income', 'Expense')` | `NOT NULL` | Type of transaction |
| `category_id` | `INT` | `NOT NULL`, `FOREIGN KEY` | References `categories(category_id)` |
| `amount` | `DECIMAL(12, 2)` | `NOT NULL`, `CHECK (amount > 0)` | Transaction amount |
| `description` | `VARCHAR(255)` | `NULL` | Optional memo / description |
| `created_at` | `TIMESTAMP` | `DEFAULT CURRENT_TIMESTAMP` | Record timestamp |

**Foreign Key Rule:**
- `ON UPDATE CASCADE`
- `ON DELETE RESTRICT` (Prevents deleting a category while transactions are associated with it)

---

### 2.3 Table: `budgets`
Stores monthly budget allocations for expense categories.

| Column | Data Type | Constraints | Description |
|---|---|---|---|
| `budget_id` | `INT` | `PRIMARY KEY AUTO_INCREMENT` | Unique budget entry identifier |
| `category_id` | `INT` | `NOT NULL`, `FOREIGN KEY` | References `categories(category_id)` |
| `month` | `INT` | `NOT NULL`, `CHECK (month BETWEEN 1 AND 12)` | Calendar month (1-12) |
| `year` | `INT` | `NOT NULL` | Calendar year (e.g., 2026) |
| `budget_amount` | `DECIMAL(12, 2)` | `NOT NULL`, `CHECK (budget_amount > 0)` | Allocated budget amount |
| `created_at` | `TIMESTAMP` | `DEFAULT CURRENT_TIMESTAMP` | Record timestamp |

**Indexes & Constraints:**
- `UNIQUE KEY (category_id, month, year)`: Ensures only one budget entry per category per month.
- `FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE CASCADE`.

---

## 3. SQL Schema Script
The full executable DDL script is located at:
`docs/DATABASE_SCHEMA.sql`

To execute directly in MySQL:
```bash
mysql -u root -p < docs/DATABASE_SCHEMA.sql
```
