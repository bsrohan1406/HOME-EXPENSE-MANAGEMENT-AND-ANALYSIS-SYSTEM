# PennyWise – Home Budget Management and Expense Analysis System
## Backend Module (Python Flask + MySQL)

PennyWise is a manual Home Budget Management and Expense Analysis System developed for an academic software engineering project. It enables households to track income and expenses, set monthly category budgets, monitor savings, detect budget overruns, and supply structured financial data for statistical analysis and Matplotlib visualizations.

---

## 1. Technology Stack

| Component | Technology | Description |
|---|---|---|
| **Programming Language** | Python 3.10+ | Core backend runtime |
| **Backend Framework** | Flask | Lightweight, modular REST API framework |
| **CORS Middleware** | Flask-CORS | Cross-origin support for frontend integration |
| **Database** | MySQL (8.0+) | Relational database for transactions and budgets |
| **Database Connector** | `mysql-connector-python` | Official Oracle MySQL driver with connection pooling |
| **Data Analysis** | Pandas | Tabular data manipulation and aggregations |
| **Numerical Calculations** | NumPy | Numeric arrays and statistical averages |
| **Visualizations** | Matplotlib | Headless server-side chart rendering (`Agg` backend) |
| **Testing** | Pytest | Unit and integration testing |

> **Academic Notice:** This backend is designed for manual financial logging. In accordance with project requirements, no external banking APIs or payment gateways are used.

---

## 2. Architecture & Project Structure

```text
PennyWise_Backend/
│
├── app.py                      # Flask Application Factory & Entry Point
├── config.py                   # Configuration class with environment variable parsing
├── database.py                 # MySQL Connection Pool & Parameterized Query Engine
├── requirements.txt            # Python dependencies
├── .env.example                # Sample environment configurations
├── .gitignore                  # Git ignore rules
├── README.md                   # Project documentation
│
├── routes/                     # REST API Blueprint Route Handlers
│   ├── __init__.py
│   ├── category_routes.py      # Categories CRUD (/api/categories)
│   ├── transaction_routes.py   # Transactions CRUD & filtering (/api/transactions)
│   ├── budget_routes.py        # Budget CRUD & overrun checks (/api/budgets)
│   └── analytics_routes.py     # Summaries, trends & Matplotlib charts (/api/analytics)
│
├── services/                   # Business Logic & Database Transactions
│   ├── category_service.py     # Category validation & management
│   ├── transaction_service.py  # Transaction integrity & queries
│   ├── budget_service.py       # Budget metrics, variance & overrun logic
│   └── analytics_service.py    # Savings rates, monthly trends & summaries
│
├── integrations/               # Teammate Integration Layer
│   ├── analysis_adapter.py     # Pandas & Matplotlib adapter for Data Analysis teammate
│   └── INTEGRATION_GUIDE.md    # Integration instructions for Frontend, DB & Analysis
│
├── utils/                      # Helper Utilities
│   └── response.py             # Standardized JSON response builders
│
├── charts/                     # Generated charts cache (.gitkeep)
│
├── tests/                      # Automated Test Suite
│   ├── conftest.py             # Pytest fixtures and mock database harness
│   ├── test_categories.py      # Category CRUD tests
│   ├── test_transactions.py    # Transaction validation & CRUD tests
│   ├── test_budgets.py         # Budget overrun and calculation tests
│   └── test_analytics.py       # Financial summary and chart tests
│
└── docs/                       # Technical Documentation
    ├── API_DOCUMENTATION.md    # Full REST API specifications
    ├── DATABASE_SCHEMA.sql     # Executable MySQL DDL script
    └── DATABASE_CONTRACT.md    # Database contract and table specifications
```

---

## 3. Installation & Setup

### 3.1 Prerequisites
- Python 3.10 or higher
- MySQL Server 8.0 or higher
- Git

### 3.2 Clone and Setup Environment
```bash
# Navigate to the backend directory
cd PennyWise_Backend

# Create a virtual environment
python -m venv venv

# Activate virtual environment
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On macOS/Linux:
source venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

### 3.3 Database Setup
1. Start your local MySQL service.
2. Log into MySQL and run the schema initialization script:
```bash
mysql -u root -p < docs/DATABASE_SCHEMA.sql
```
This creates the `pennywise_db` database and seeds default Income and Expense categories (`Groceries`, `Rent`, `Salary`, `Utilities`, etc.).

### 3.4 Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` to configure your MySQL credentials:
```ini
FLASK_DEBUG=True
PORT=5000
HOST=0.0.0.0
SECRET_KEY=pennywise-secure-secret-key

MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=your_mysql_username
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=pennywise_db
MYSQL_POOL_SIZE=5

CORS_ORIGINS=*
```

---

## 4. Running the Application

To start the Flask development server:
```bash
python app.py
```
The server will start at `http://localhost:5000`.

### Health Check Verification
Verify that the server and MySQL connection are healthy:
```bash
curl http://localhost:5000/api/health
```
Expected response:
```json
{
  "service": "PennyWise Backend API",
  "status": "healthy",
  "database": {
    "type": "MySQL",
    "connected": true,
    "message": "Database connection is healthy"
  }
}
```

---

## 5. API Overview

| Group | Method | Endpoint | Description |
|---|---|---|---|
| **System** | `GET` | `/api/health` | Service and MySQL health status |
| **Categories** | `GET` | `/api/categories` | List all categories (optional `?type=Income/Expense`) |
| | `GET` | `/api/categories/<id>` | Get single category |
| | `POST` | `/api/categories` | Create category |
| | `PUT` | `/api/categories/<id>` | Update category |
| | `DELETE` | `/api/categories/<id>` | Delete category (foreign key protected) |
| **Transactions** | `GET` | `/api/transactions` | List transactions with date, month, year, type filters |
| | `GET` | `/api/transactions/<id>` | Get single transaction |
| | `POST` | `/api/transactions` | Add Income or Expense transaction |
| | `PUT` | `/api/transactions/<id>` | Update transaction |
| | `DELETE` | `/api/transactions/<id>` | Delete transaction |
| **Budgets** | `GET` | `/api/budgets` | View monthly budgets with spent & overrun metrics |
| | `GET` | `/api/budgets/<id>` | Get single budget |
| | `POST` | `/api/budgets` | Allocate category budget for month & year |
| | `PUT` | `/api/budgets/<id>` | Update allocated budget |
| | `DELETE` | `/api/budgets/<id>` | Delete budget |
| **Analytics** | `GET` | `/api/analytics/summary` | Total income, expense, savings & savings rate |
| | `GET` | `/api/analytics/monthly` | 12-month breakdown of finances and budgets |
| | `GET` | `/api/analytics/categories` | Category-wise expense/income distribution |
| | `GET` | `/api/analytics/budget-status` | Budget utilization and overrun detection |
| **Charts** | `GET` | `/api/analytics/charts/expense-distribution` | Category expense distribution donut chart |
| | `GET` | `/api/analytics/charts/monthly-comparison` | Monthly Income vs. Expenses grouped bar chart |
| | `GET` | `/api/analytics/charts/expense-trend` | Monthly expense trend line chart with average |
| | `GET` | `/api/analytics/charts/budget-utilization` | Budget vs. Actual spending horizontal bar chart |

*For complete request payloads, parameters, and response schemas, refer to [`docs/API_DOCUMENTATION.md`](docs/API_DOCUMENTATION.md).*

---

## 6. Business Logic & Calculations

### Financial Formulas
- **Total Savings:** $\text{Total Savings} = \text{Total Income} - \text{Total Expenses}$
- **Savings Rate (%):** $\left(\frac{\text{Total Savings}}{\text{Total Income}}\right) \times 100$ *(Guarded against division by zero when Income is 0)*
- **Remaining Budget:** $\text{Remaining Budget} = \text{Budget Amount} - \text{Actual Expenses}$
- **Budget Utilization (%):** $\left(\frac{\text{Actual Expenses}}{\text{Budget Amount}}\right) \times 100$ *(Guarded against zero budget)*
- **Overrun Status:** If $\text{Actual Expenses} > \text{Budget Amount}$, $\text{Overrun Amount} = \text{Actual Expenses} - \text{Budget Amount}$.

---

## 7. Running the Test Suite

Run automated unit and integration tests using `pytest`:
```bash
pytest -v
```
All tests check validation rules, calculations, edge cases (zero income, zero budgets, invalid inputs), and REST endpoints.
