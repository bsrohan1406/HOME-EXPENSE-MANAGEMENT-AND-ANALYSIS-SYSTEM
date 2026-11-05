# PennyWise – Teammate Integration Guide

This guide provides clear instructions for the three project teammates:
1. **Frontend Teammate** (HTML5, CSS3, Vanilla JS / Lovable)
2. **Database Teammate** (MySQL Database Design & Scripts)
3. **Data Analysis Teammate** (Pandas, NumPy, Matplotlib)

---

## 1. Frontend Teammate Integration (Lovable / HTML5, CSS3, Vanilla JS)

### 1.1 Base Configuration
- **Backend API Base URL:** `http://localhost:5000/api`
- **CORS Support:** CORS is enabled on all `/api/*` endpoints. If running on a specific port (e.g. `http://localhost:3000` or `http://localhost:5173`), set `CORS_ORIGINS` in `.env`.

### 1.2 Calling Endpoints from Vanilla JS / Lovable
All responses return structured JSON:
```javascript
// Fetch all categories
async function fetchCategories(type = '') {
  const url = type ? `http://localhost:5000/api/categories?type=${type}` : 'http://localhost:5000/api/categories';
  const response = await fetch(url);
  const result = await response.json();
  if (result.status === 'success') {
    return result.data; // Array of categories
  } else {
    alert(result.message);
  }
}

// Add an Expense transaction
async function addExpenseTransaction(amount, categoryId, date, description) {
  const response = await fetch('http://localhost:5000/api/transactions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      amount: parseFloat(amount),
      transaction_type: 'Expense',
      category_id: parseInt(categoryId),
      transaction_date: date, // YYYY-MM-DD
      description: description
    })
  });
  return await response.json();
}
```

### 1.3 Rendering Server-Generated Matplotlib Charts
You do **not** need complex client-side charting libraries. Two simple options:

**Option A (Direct Image Stream in `<img>` tags):**
```html
<img src="http://localhost:5000/api/analytics/charts/expense-distribution?format=png" alt="Expense Distribution" />
<img src="http://localhost:5000/api/analytics/charts/monthly-comparison?year=2026&format=png" alt="Income vs Expense" />
```

**Option B (Base64 JSON via `fetch`):**
```javascript
const res = await fetch('http://localhost:5000/api/analytics/charts/budget-utilization');
const json = await res.json();
document.getElementById('chart-container').innerHTML = `<img src="${json.data.image}" class="img-fluid" />`;
```

---

## 2. Database Teammate Integration (MySQL)

### 2.1 Schema Verification
The backend expects three core tables: `categories`, `transactions`, and `budgets`.
The complete SQL schema definition is located at:
`docs/DATABASE_SCHEMA.sql`

To import into MySQL:
```bash
mysql -u root -p < docs/DATABASE_SCHEMA.sql
```

### 2.2 Connection Parameters
Set your local credentials in `.env`:
```ini
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=your_mysql_username
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=pennywise_db
```

### 2.3 Field Name Adaptability
If you name a column differently (for example `cat_id` instead of `category_id`), simply update the corresponding SQL queries in:
- `services/category_service.py`
- `services/transaction_service.py`
- `services/budget_service.py`
- `services/analytics_service.py`
The backend isolates all SQL statements in these four service files and `database.py`.

---

## 3. Data Analysis Teammate Integration (Pandas, NumPy, Matplotlib)

### 3.1 Interface Adapter
The backend provides a dedicated adapter located at:
`integrations/analysis_adapter.py`

This adapter:
1. Queries MySQL and builds Pandas DataFrames for you:
   - `AnalysisAdapter.get_transactions_dataframe(month=None, year=None, transaction_type=None)`
   - `AnalysisAdapter.get_budgets_dataframe(month=None, year=None)`
2. Provides functions for all 4 required charts:
   - `generate_expense_distribution_chart(month, year)`
   - `generate_monthly_income_vs_expense_chart(year)`
   - `generate_monthly_expense_trend_chart(year)`
   - `generate_budget_utilization_chart(month, year)`

### 3.2 If You Develop a Custom Module
If you write an independent file (e.g. `integrations/custom_analyzer.py`), you can import your functions directly into `integrations/analysis_adapter.py`.
The function signatures expect:
```python
def generate_chart(df: pd.DataFrame, ...) -> Tuple[bytes, str]:
    # Use Matplotlib to plot
    # Return (png_bytes, base64_data_url)
```
Ensure you use `matplotlib.use('Agg')` before importing `pyplot` so charts render properly on the headless web server.
