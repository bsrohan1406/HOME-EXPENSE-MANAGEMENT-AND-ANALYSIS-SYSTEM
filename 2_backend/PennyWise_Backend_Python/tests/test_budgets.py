
"""
Unit and integration tests for Monthly Budget Management APIs
and BudgetService.

Tests use the existing API request and response format.
The backend stores the budget month internally as YYYY-MM.
"""

import json


def test_create_budget_success(client):
    """Test creating a valid monthly budget."""

    payload = {
        "category_id": 1,
        "month": 11,
        "year": 2026,
        "budget_amount": 5000.00
    }

    response = client.post(
        "/api/budgets",
        data=json.dumps(payload),
        content_type="application/json"
    )

    assert response.status_code == 201

    data = response.get_json()

    assert data["status"] == "success"
    assert data["data"]["budget_amount"] == 5000.0
    assert data["data"]["category_name"] == "Groceries"
    assert data["data"]["month"] == 11
    assert data["data"]["year"] == 2026
    assert data["data"]["is_over_budget"] is False


def test_budget_on_income_category_rejected(client):
    """Test that budgets cannot be created for income categories."""

    payload = {
        "category_id": 9,
        "month": 11,
        "year": 2026,
        "budget_amount": 10000.00
    }

    response = client.post(
        "/api/budgets",
        data=json.dumps(payload),
        content_type="application/json"
    )

    assert response.status_code == 400

    message = response.get_json()["message"].lower()

    assert "budgets can only be set for expense categories" in message


def test_invalid_budget_inputs(client):
    """Test invalid month and zero budget amount."""

    # Invalid month
    response_month = client.post(
        "/api/budgets",
        data=json.dumps({
            "category_id": 1,
            "month": 13,
            "year": 2026,
            "budget_amount": 1000.0
        }),
        content_type="application/json"
    )

    assert response_month.status_code == 400

    # Zero budget amount
    response_zero = client.post(
        "/api/budgets",
        data=json.dumps({
            "category_id": 1,
            "month": 11,
            "year": 2026,
            "budget_amount": 0.0
        }),
        content_type="application/json"
    )

    assert response_zero.status_code == 400

    message = response_zero.get_json()["message"].lower()

    assert "greater than zero" in message


def test_duplicate_budget_conflict(client):
    """Test duplicate budget prevention for a category and month."""

    payload = {
        "category_id": 2,
        "month": 11,
        "year": 2026,
        "budget_amount": 25000.00
    }

    first_response = client.post(
        "/api/budgets",
        data=json.dumps(payload),
        content_type="application/json"
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/api/budgets",
        data=json.dumps(payload),
        content_type="application/json"
    )

    assert second_response.status_code == 409

    message = second_response.get_json()["message"].lower()

    assert "already exists" in message


def test_detect_budget_overrun(client):
    """
    Test budget utilization and overspending.

    Category: Transportation
    Monthly budget: ₹4,000
    Actual expenses: ₹4,800
    Overrun: ₹800
    Utilization: 120%
    """

    # Step 1: Create a budget of ₹4,000.
    budget_response = client.post(
        "/api/budgets",
        data=json.dumps({
            "category_id": 3,
            "month": 11,
            "year": 2026,
            "budget_amount": 4000.00
        }),
        content_type="application/json"
    )

    assert budget_response.status_code == 201

    # Step 2: Add an expense of ₹4,800.
    transaction_response = client.post(
        "/api/transactions",
        data=json.dumps({
            "amount": 4800.00,
            "transaction_type": "Expense",
            "category_id": 3,
            "transaction_date": "2026-11-05",
            "description": "Vehicle maintenance and fuel"
        }),
        content_type="application/json"
    )

    assert transaction_response.status_code == 201

    # Step 3: Retrieve the November 2026 budgets.
    response = client.get(
        "/api/budgets?month=11&year=2026"
    )

    assert response.status_code == 200

    budgets = response.get_json()["data"]

    transport_budget = next(
        (
            budget for budget in budgets
            if budget["category_id"] == 3
        ),
        None
    )

    assert transport_budget is not None

    assert transport_budget["budget_amount"] == 4000.0
    assert transport_budget["amount_spent"] == 4800.0
    assert transport_budget["remaining_budget"] == -800.0
    assert transport_budget["is_over_budget"] is True
    assert transport_budget["overrun_amount"] == 800.0
    assert transport_budget["budget_utilization_pct"] == 120.0


def test_update_and_delete_budget(client):
    """Test updating and deleting a budget."""

    # Create a budget.
    create_response = client.post(
        "/api/budgets",
        data=json.dumps({
            "category_id": 1,
            "month": 12,
            "year": 2026,
            "budget_amount": 3000.00
        }),
        content_type="application/json"
    )

    assert create_response.status_code == 201

    budget_id = (
        create_response.get_json()["data"]["budget_id"]
    )

    # Update the budget amount.
    update_response = client.put(
        f"/api/budgets/{budget_id}",
        data=json.dumps({
            "budget_amount": 3500.00
        }),
        content_type="application/json"
    )

    assert update_response.status_code == 200

    assert (
        update_response.get_json()["data"]["budget_amount"]
        == 3500.0
    )

    # Delete the budget.
    delete_response = client.delete(
        f"/api/budgets/{budget_id}"
    )

    assert delete_response.status_code == 200

    # Verify that the budget no longer exists.
    get_response = client.get(
        f"/api/budgets/{budget_id}"
    )

    assert get_response.status_code == 404
