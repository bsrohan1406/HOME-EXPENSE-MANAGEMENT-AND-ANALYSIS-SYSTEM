
"""
Unit and integration tests for Analytics APIs,
Financial Calculations, and Matplotlib Charts.
"""

import json


def test_financial_summary_calculations(client):
    """
    Verify:
    Savings = Income - Expenses
    Savings Rate = (Savings / Income) * 100
    Remaining Budget = Budget - Actual Expenses
    Budget Utilization = (Expenses / Budget) * 100
    """

    # Add income: ₹100,000
    income_response = client.post(
        "/api/transactions",
        data=json.dumps({
            "amount": 100000.0,
            "transaction_type": "Income",
            "category_id": 9,
            "transaction_date": "2026-11-01",
            "description": "Salary"
        }),
        content_type="application/json"
    )
    assert income_response.status_code == 201

    # Add expense: ₹40,000
    expense_response = client.post(
        "/api/transactions",
        data=json.dumps({
            "amount": 40000.0,
            "transaction_type": "Expense",
            "category_id": 2,
            "transaction_date": "2026-11-02",
            "description": "Rent"
        }),
        content_type="application/json"
    )
    assert expense_response.status_code == 201

    # Create budget: ₹50,000
    budget_response = client.post(
        "/api/budgets",
        data=json.dumps({
            "category_id": 2,
            "month": 11,
            "year": 2026,
            "budget_amount": 50000.0
        }),
        content_type="application/json"
    )
    assert budget_response.status_code == 201

    # Retrieve financial summary
    response = client.get(
        "/api/analytics/summary?month=11&year=2026"
    )

    assert response.status_code == 200

    data = response.get_json()["data"]

    assert data["income"]["total"] == 100000.0
    assert data["expense"]["total"] == 40000.0
    assert data["savings"]["total"] == 60000.0
    assert data["savings"]["savings_rate_pct"] == 60.0

    assert data["budget"]["total_budget"] == 50000.0
    assert data["budget"]["total_spent_on_budgeted"] == 40000.0
    assert data["budget"]["remaining_budget"] == 10000.0
    assert data["budget"]["budget_utilization_pct"] == 80.0
    assert data["budget"]["over_budget_categories_count"] == 0


def test_zero_income_scenario(client):
    """Verify savings calculation when income is zero."""

    response = client.post(
        "/api/transactions",
        data=json.dumps({
            "amount": 5000.0,
            "transaction_type": "Expense",
            "category_id": 1,
            "transaction_date": "2026-11-02",
            "description": "Food"
        }),
        content_type="application/json"
    )

    assert response.status_code == 201

    summary_response = client.get(
        "/api/analytics/summary?month=11&year=2026"
    )

    assert summary_response.status_code == 200

    data = summary_response.get_json()["data"]

    assert data["income"]["total"] == 0.0
    assert data["expense"]["total"] == 5000.0
    assert data["savings"]["total"] == -5000.0
    assert data["savings"]["savings_rate_pct"] == 0.0


def test_empty_database_scenario(client):
    """Verify analytics endpoints with no recorded transactions."""

    summary_response = client.get("/api/analytics/summary")

    assert summary_response.status_code == 200

    summary = summary_response.get_json()["data"]

    assert summary["income"]["total"] == 0.0
    assert summary["expense"]["total"] == 0.0
    assert summary["savings"]["total"] == 0.0

    monthly_response = client.get(
        "/api/analytics/monthly?year=2026"
    )

    assert monthly_response.status_code == 200
    assert len(monthly_response.get_json()["data"]) == 12

    categories_response = client.get(
        "/api/analytics/categories?type=Expense"
    )

    assert categories_response.status_code == 200
    assert isinstance(
        categories_response.get_json()["data"],
        list
    )

    budget_response = client.get(
        "/api/analytics/budget-status"
    )

    assert budget_response.status_code == 200
    assert isinstance(
        budget_response.get_json()["data"],
        list
    )


def test_system_health_endpoint(client):
    """Verify the backend health endpoint."""

    response = client.get("/api/health")

    assert response.status_code == 200

    data = response.get_json()

    assert data["service"] == "PennyWise Backend API"
    assert data["status"] == "healthy"
    assert data["database"]["type"] == "MySQL"
    assert data["database"]["connected"] is True


def test_matplotlib_chart_endpoints(client):
    """Verify all four Matplotlib chart endpoints."""

    # Add an expense transaction.
    transaction_response = client.post(
        "/api/transactions",
        data=json.dumps({
            "amount": 2000.0,
            "transaction_type": "Expense",
            "category_id": 1,
            "transaction_date": "2026-11-02",
            "description": "Groceries"
        }),
        content_type="application/json"
    )

    assert transaction_response.status_code == 201

    # Create a budget.
    budget_response = client.post(
        "/api/budgets",
        data=json.dumps({
            "category_id": 1,
            "month": 11,
            "year": 2026,
            "budget_amount": 3000.0
        }),
        content_type="application/json"
    )

    assert budget_response.status_code == 201

    # 1. Expense distribution chart - JSON
    response1 = client.get(
        "/api/analytics/charts/expense-distribution?month=11&year=2026"
    )

    assert response1.status_code == 200

    image1 = response1.get_json()["data"]["image"]
    assert image1.startswith("data:image/png;base64,")

    # 1b. Expense distribution chart - PNG
    response1_png = client.get(
        "/api/analytics/charts/expense-distribution?format=png"
    )

    assert response1_png.status_code == 200
    assert response1_png.mimetype == "image/png"
    assert len(response1_png.data) > 0

    # 2. Monthly income versus expenses chart
    response2 = client.get(
        "/api/analytics/charts/monthly-comparison?year=2026"
    )

    assert response2.status_code == 200
    assert response2.get_json()["data"]["image"].startswith(
        "data:image/png;base64,"
    )

    # 3. Monthly expense trend chart
    response3 = client.get(
        "/api/analytics/charts/expense-trend?year=2026"
    )

    assert response3.status_code == 200
    assert response3.get_json()["data"]["image"].startswith(
        "data:image/png;base64,"
    )

    # 4. Budget utilization chart
    response4 = client.get(
        "/api/analytics/charts/budget-utilization?month=11&year=2026"
    )

    assert response4.status_code == 200
    assert response4.get_json()["data"]["image"].startswith(
        "data:image/png;base64,"
    )
