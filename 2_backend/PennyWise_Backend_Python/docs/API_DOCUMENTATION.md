# PennyWise – REST API Documentation

**Application:** PennyWise – Home Budget Management and Expense Analysis System  
**Backend Framework:** Python Flask  
**Database:** MySQL  
**Base URL:** `http://localhost:5000` (Default)  
**Content-Type:** `application/json`

---

## 1. Standard Response Formats & HTTP Status Codes

### Successful Response Format
```json
{
  "status": "success",
  "message": "Transaction added successfully",
  "data": { ... }
}
```

### Error Response Format
```json
{
  "status": "error",
  "message": "Amount must be greater than zero"
}
```

### HTTP Status Codes
| Code | Meaning | Description |
|---|---|---|
| `200 OK` | Success | The request succeeded and returned requested data. |
| `201 Created` | Created | A new resource (category, transaction, budget) was successfully created. |
| `400 Bad Request` | Validation Error | Missing required fields, invalid amount, bad date format, etc. |
| `404 Not Found` | Not Found | Requested transaction, category, or budget ID does not exist. |
| `409 Conflict` | Conflict | Duplicate entry (e.g., category already exists, budget already set for month). |
| `500 Server Error` | Internal Error | Database connection failure or unhandled exception. |

---

## 2. System Endpoints

### 2.1 Health Check
- **Endpoint:** `GET /api/health`
- **Description:** Verifies service health, MySQL connectivity, and active subsystem modules.
- **Request Headers:** None
- **Response `200 OK`:**
```json
{
  "service": "PennyWise Backend API",
  "status": "healthy",
  "timestamp": "2026-11-02T15:30:00Z",
  "database": {
    "type": "MySQL",
    "connected": true,
    "message": "Database connection is healthy"
  },
  "modules": {
    "transactions": "active",
    "categories": "active",
    "budgets": "active",
    "analytics": "active",
    "charts": "active"
  }
}
```

---

## 3. Category Management APIs

### 3.1 Get All Categories
- **Endpoint:** `GET /api/categories`
- **Query Parameters:**
  - `type` (optional): Filter by category type (`Income` or `Expense`).
- **Response `200 OK`:**
```json
{
  "status": "success",
  "message": "Retrieved 13 categories successfully",
  "data": [
    {
      "category_id": 1,
      "name": "Groceries",
      "type": "Expense",
      "description": "Household food and supplies",
      "created_at": "2026-11-01 10:00:00"
    },
    {
      "category_id": 9,
      "name": "Salary",
      "type": "Income",
      "description": "Monthly employment salary",
      "created_at": "2026-11-01 10:00:00"
    }
  ]
}
```

### 3.2 Get Category by ID
- **Endpoint:** `GET /api/categories/<id>`
- **Response `200 OK`:**
```json
{
  "status": "success",
  "message": "Category retrieved successfully",
  "data": {
    "category_id": 1,
    "name": "Groceries",
    "type": "Expense",
    "description": "Household food and supplies",
    "created_at": "2026-11-01 10:00:00"
  }
}
```
- **Response `404 Not Found`:**
```json
{
  "status": "error",
  "message": "Category with ID 999 not found"
}
```

### 3.3 Create a Category
- **Endpoint:** `POST /api/categories`
- **Request Body:**
```json
{
  "name": "Freelance Design",
  "type": "Income",
  "description": "UI/UX client design projects"
}
```
- **Validation Rules:**
  - `name`: Required, max 50 characters.
  - `type`: Required, must be `Income` or `Expense`.
  - Duplicate check: Name + Type must be unique.
- **Response `201 Created`:**
```json
{
  "status": "success",
  "message": "Category created successfully",
  "data": {
    "category_id": 14,
    "name": "Freelance Design",
    "type": "Income",
    "description": "UI/UX client design projects",
    "created_at": "2026-11-02 21:00:00"
  }
}
```
- **Response `409 Conflict`:**
```json
{
  "status": "error",
  "message": "Category 'Freelance Design' of type 'Income' already exists."
}
```

### 3.4 Update a Category
- **Endpoint:** `PUT /api/categories/<id>`
- **Request Body:**
```json
{
  "name": "Freelance & Consulting",
  "description": "Updated description"
}
```
- **Response `200 OK`:**
```json
{
  "status": "success",
  "message": "Category updated successfully",
  "data": {
    "category_id": 14,
    "name": "Freelance & Consulting",
    "type": "Income",
    "description": "Updated description",
    "created_at": "2026-11-02 21:00:00"
  }
}
```

### 3.5 Delete a Category
- **Endpoint:** `DELETE /api/categories/<id>`
- **Response `200 OK`:**
```json
{
  "status": "success",
  "message": "Category deleted successfully",
  "data": {
    "category_id": 14
  }
}
```
- **Response `409 Conflict` (Foreign Key Protection):**
```json
{
  "status": "error",
  "message": "Cannot delete category 'Groceries' because 12 transaction(s) are associated with it."
}
```

---

## 4. Transaction Management APIs

### 4.1 Get All Transactions (With Filters)
- **Endpoint:** `GET /api/transactions`
- **Query Parameters:**
  - `start_date` (optional, `YYYY-MM-DD`): Transactions from this date onwards.
  - `end_date` (optional, `YYYY-MM-DD`): Transactions up to this date.
  - `date` (optional, `YYYY-MM-DD`): Transactions on an exact single date.
  - `month` (optional, `1`-`12`): Filter transactions within calendar month.
  - `year` (optional, `YYYY`): Filter transactions within calendar year.
  - `category_id` (optional, integer): Filter by specific category ID.
  - `type` (optional, `Income` or `Expense`): Filter by transaction type.
- **Response `200 OK`:**
```json
{
  "status": "success",
  "message": "Retrieved 2 transactions successfully",
  "data": [
    {
      "transaction_id": 1,
      "transaction_date": "2026-11-01",
      "transaction_type": "Income",
      "category_id": 9,
      "category_name": "Salary",
      "category_type": "Income",
      "amount": 75000.0,
      "description": "November Monthly Salary",
      "created_at": "2026-11-01 09:30:00"
    },
    {
      "transaction_id": 2,
      "transaction_date": "2026-11-02",
      "transaction_type": "Expense",
      "category_id": 1,
      "category_name": "Groceries",
      "category_type": "Expense",
      "amount": 3450.5,
      "description": "Supermarket grocery provisions",
      "created_at": "2026-11-02 18:15:00"
    }
  ]
}
```

### 4.2 Get Transaction by ID
- **Endpoint:** `GET /api/transactions/<id>`
- **Response `200 OK`:**
```json
{
  "status": "success",
  "message": "Transaction retrieved successfully",
  "data": {
    "transaction_id": 2,
    "transaction_date": "2026-11-02",
    "transaction_type": "Expense",
    "category_id": 1,
    "category_name": "Groceries",
    "category_type": "Expense",
    "amount": 3450.5,
    "description": "Supermarket grocery provisions",
    "created_at": "2026-11-02 18:15:00"
  }
}
```
- **Response `404 Not Found`:**
```json
{
  "status": "error",
  "message": "Transaction with ID 999 not found"
}
```

### 4.3 Add a New Transaction
- **Endpoint:** `POST /api/transactions`
- **Request Body:**
```json
{
  "amount": 2500.00,
  "transaction_type": "Expense",
  "category_id": 3,
  "transaction_date": "2026-11-02",
  "description": "Monthly Metro Pass & Fuel"
}
```
- **Validation Rules:**
  - `amount`: Required, must be a number > 0.
  - `transaction_type`: Required, must be `Income` or `Expense`.
  - `category_id`: Required, must exist and category type must match `transaction_type`.
  - `transaction_date`: Required, format `YYYY-MM-DD`.
- **Response `201 Created`:**
```json
{
  "status": "success",
  "message": "Transaction added successfully",
  "data": {
    "transaction_id": 3,
    "transaction_date": "2026-11-02",
    "transaction_type": "Expense",
    "category_id": 3,
    "category_name": "Transportation",
    "category_type": "Expense",
    "amount": 2500.0,
    "description": "Monthly Metro Pass & Fuel",
    "created_at": "2026-11-02 21:05:00"
  }
}
```
- **Response `400 Bad Request`:**
```json
{
  "status": "error",
  "message": "Amount must be greater than zero."
}
```

### 4.4 Update a Transaction
- **Endpoint:** `PUT /api/transactions/<id>`
- **Request Body:**
```json
{
  "amount": 2700.00,
  "description": "Metro Pass + Uber fare"
}
```
- **Response `200 OK`:**
```json
{
  "status": "success",
  "message": "Transaction updated successfully",
  "data": {
    "transaction_id": 3,
    "transaction_date": "2026-11-02",
    "transaction_type": "Expense",
    "category_id": 3,
    "category_name": "Transportation",
    "category_type": "Expense",
    "amount": 2700.0,
    "description": "Metro Pass + Uber fare",
    "created_at": "2026-11-02 21:05:00"
  }
}
```

### 4.5 Delete a Transaction
- **Endpoint:** `DELETE /api/transactions/<id>`
- **Response `200 OK`:**
```json
{
  "status": "success",
  "message": "Transaction deleted successfully",
  "data": {
    "transaction_id": 3
  }
}
```

---

## 5. Monthly Budget Management APIs

### 5.1 Get Budgets (With Overrun Detection)
- **Endpoint:** `GET /api/budgets`
- **Query Parameters:**
  - `month` (optional, 1-12)
  - `year` (optional, YYYY)
- **Response `200 OK`:**
```json
{
  "status": "success",
  "message": "Retrieved 2 budget record(s) successfully",
  "data": [
    {
      "budget_id": 1,
      "category_id": 1,
      "category_name": "Groceries",
      "month": 11,
      "year": 2026,
      "budget_amount": 5000.0,
      "amount_spent": 5800.0,
      "remaining_budget": -800.0,
      "budget_utilization_pct": 116.0,
      "is_over_budget": true,
      "overrun_amount": 800.0,
      "created_at": "2026-11-01 08:00:00"
    },
    {
      "budget_id": 2,
      "category_id": 3,
      "category_name": "Transportation",
      "month": 11,
      "year": 2026,
      "budget_amount": 4000.0,
      "amount_spent": 2500.0,
      "remaining_budget": 1500.0,
      "budget_utilization_pct": 62.5,
      "is_over_budget": false,
      "overrun_amount": 0.0,
      "created_at": "2026-11-01 08:00:00"
    }
  ]
}
```

### 5.2 Get Budget by ID
- **Endpoint:** `GET /api/budgets/<id>`
- **Response `200 OK`:** Same structure as budget record above.
- **Response `404 Not Found`:** If budget ID does not exist.

### 5.3 Create a Monthly Budget
- **Endpoint:** `POST /api/budgets`
- **Request Body:**
```json
{
  "category_id": 1,
  "month": 11,
  "year": 2026,
  "budget_amount": 5000.00
}
```
- **Validation Rules:**
  - `category_id`: Must exist and must be an `Expense` category.
  - `month`: Integer between 1 and 12.
  - `year`: Valid integer between 2000 and 2100.
  - `budget_amount`: Number > 0.
  - Unique: Only 1 budget per (category_id, month, year).
- **Response `201 Created`:**
```json
{
  "status": "success",
  "message": "Budget created successfully",
  "data": {
    "budget_id": 1,
    "category_id": 1,
    "category_name": "Groceries",
    "month": 11,
    "year": 2026,
    "budget_amount": 5000.0,
    "amount_spent": 0.0,
    "remaining_budget": 5000.0,
    "budget_utilization_pct": 0.0,
    "is_over_budget": false,
    "overrun_amount": 0.0,
    "created_at": "2026-11-02 21:10:00"
  }
}
```
- **Response `409 Conflict`:**
```json
{
  "status": "error",
  "message": "A budget for this category already exists for 11/2026. Please update the existing budget (ID: 1) instead."
}
```

### 5.4 Update a Budget
- **Endpoint:** `PUT /api/budgets/<id>`
- **Request Body:**
```json
{
  "budget_amount": 6000.00
}
```
- **Response `200 OK`:**
```json
{
  "status": "success",
  "message": "Budget updated successfully",
  "data": {
    "budget_id": 1,
    "category_id": 1,
    "category_name": "Groceries",
    "month": 11,
    "year": 2026,
    "budget_amount": 6000.0,
    "amount_spent": 5800.0,
    "remaining_budget": 200.0,
    "budget_utilization_pct": 96.67,
    "is_over_budget": false,
    "overrun_amount": 0.0,
    "created_at": "2026-11-01 08:00:00"
  }
}
```

### 5.5 Delete a Budget
- **Endpoint:** `DELETE /api/budgets/<id>`
- **Response `200 OK`:**
```json
{
  "status": "success",
  "message": "Budget deleted successfully",
  "data": {
    "budget_id": 1
  }
}
```

---

## 6. Financial Summary & Analytics APIs

### 6.1 Financial Summary
- **Endpoint:** `GET /api/analytics/summary`
- **Query Parameters:**
  - `month` (optional, 1-12)
  - `year` (optional, YYYY)
- **Response `200 OK`:**
```json
{
  "status": "success",
  "message": "Financial summary retrieved successfully",
  "data": {
    "period": {
      "month": 11,
      "year": 2026
    },
    "income": {
      "total": 85000.0,
      "transaction_count": 2
    },
    "expense": {
      "total": 35200.0,
      "transaction_count": 18
    },
    "savings": {
      "total": 49800.0,
      "savings_rate_pct": 58.59
    },
    "budget": {
      "total_budget": 40000.0,
      "total_spent_on_budgeted": 32000.0,
      "remaining_budget": 8000.0,
      "budget_utilization_pct": 80.0,
      "over_budget_categories_count": 1,
      "total_budgeted_categories": 6
    }
  }
}
```

### 6.2 Monthly Financial Breakdown
- **Endpoint:** `GET /api/analytics/monthly`
- **Query Parameters:**
  - `year` (optional, defaults to current year)
- **Response `200 OK`:**
```json
{
  "status": "success",
  "message": "Monthly breakdown retrieved successfully",
  "data": [
    {
      "year": 2026,
      "month": 1,
      "month_name": "January",
      "income": 75000.0,
      "expense": 42000.0,
      "savings": 33000.0,
      "savings_rate_pct": 44.0,
      "budget": 45000.0,
      "budget_utilization_pct": 93.33
    },
    ...
  ]
}
```

### 6.3 Category-Wise Analytics
- **Endpoint:** `GET /api/analytics/categories`
- **Query Parameters:**
  - `month` (optional, 1-12)
  - `year` (optional, YYYY)
  - `type` (optional, `Expense` or `Income`, defaults to `Expense`)
- **Response `200 OK`:**
```json
{
  "status": "success",
  "message": "Expense category distribution retrieved successfully",
  "data": [
    {
      "category_id": 2,
      "category_name": "Rent",
      "category_type": "Expense",
      "total_amount": 20000.0,
      "transaction_count": 1,
      "percentage_of_total": 56.82
    },
    {
      "category_id": 1,
      "category_name": "Groceries",
      "category_type": "Expense",
      "total_amount": 5800.0,
      "transaction_count": 6,
      "percentage_of_total": 16.48
    }
  ]
}
```

### 6.4 Budget Status Analysis
- **Endpoint:** `GET /api/analytics/budget-status`
- **Query Parameters:**
  - `month` (optional, 1-12)
  - `year` (optional, YYYY)
- **Response `200 OK`:** Returns array of budget utilization comparisons.

---

## 7. Matplotlib Chart Endpoints

The backend generates native Matplotlib charts on demand and supports two delivery modes:
1. **Raw PNG Image Stream:** When `?format=png` is passed or when loaded via `<img src="/api/analytics/charts/...">`.
2. **Base64 JSON (Default):** When `?format=json` or standard API call is made. Returns `{"data": {"chart_name": "...", "format": "base64", "image": "data:image/png;base64,..."}}`.

### Endpoints:
1. `GET /api/analytics/charts/expense-distribution`  
   *Parameters:* `month`, `year`, `format`  
   *Chart:* Donut chart showing percentage expense distribution across categories.
2. `GET /api/analytics/charts/monthly-comparison`  
   *Parameters:* `year`, `format`  
   *Chart:* Grouped bar chart comparing Income vs. Expenses month by month.
3. `GET /api/analytics/charts/expense-trend`  
   *Parameters:* `year`, `format`  
   *Chart:* Line graph with markers tracking monthly expense fluctuations with an average line.
4. `GET /api/analytics/charts/budget-utilization`  
   *Parameters:* `month`, `year`, `format`  
   *Chart:* Comparative horizontal bar chart displaying Allocated Budget vs Actual Spent per category with overrun highlights.
