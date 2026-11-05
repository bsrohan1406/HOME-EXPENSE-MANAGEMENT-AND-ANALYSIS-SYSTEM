
"""
Unit and integration tests for Transaction Management APIs
and TransactionService.

Tests follow the approved PennyWise database schema.
"""

import json


def test_add_income_transaction_success(client):
    """Test adding a valid income transaction."""

    payload = {
        "amount": 75000.00,
        "transaction_type": "Income",
        "category_id": 9,
        "transaction_date": "2026-11-01",
        "description": "November Salary Payment"
    }

    response = client.post(
        "/api/transactions",
        data=json.dumps(payload),
        content_type="application/json"
    )

    assert response.status_code == 201

    data = response.get_json()

    assert data["status"] == "success"
    assert data["data"]["amount"] == 75000.0
    assert data["data"]["category_name"] == "Salary"
    assert data["data"]["transaction_type"] == "income"


def test_add_expense_transaction_success(client):
    """Test adding a valid expense transaction."""

    payload = {
        "amount": 3450.50,
        "transaction_type": "Expense",
        "category_id": 1,
        "transaction_date": "2026-11-02",
        "description": "Supermarket essentials"
    }

    response = client.post(
        "/api/transactions",
        data=json.dumps(payload),
        content_type="application/json"
    )

    assert response.status_code == 201

    data = response.get_json()

    assert data["status"] == "success"
    assert data["data"]["amount"] == 3450.50
    assert data["data"]["category_name"] == "Groceries"
    assert data["data"]["transaction_type"] == "expense"


def test_invalid_transaction_amount(client):
    """Test that zero and negative amounts are rejected."""

    # Zero amount
    response_zero = client.post(
        "/api/transactions",
        data=json.dumps({
            "amount": 0.0,
            "transaction_type": "Expense",
            "category_id": 1,
            "transaction_date": "2026-11-02"
        }),
        content_type="application/json"
    )

    assert response_zero.status_code == 400
    assert "greater than zero" in (
        response_zero.get_json()["message"].lower()
    )

    # Negative amount
    response_negative = client.post(
        "/api/transactions",
        data=json.dumps({
            "amount": -500.0,
            "transaction_type": "Expense",
            "category_id": 1,
            "transaction_date": "2026-11-02"
        }),
        content_type="application/json"
    )

    assert response_negative.status_code == 400


def test_invalid_category_or_type_mismatch(client):
    """Test category existence and transaction type validation."""

    # Non-existent category
    response_nonexistent = client.post(
        "/api/transactions",
        data=json.dumps({
            "amount": 1000.0,
            "transaction_type": "Expense",
            "category_id": 9999,
            "transaction_date": "2026-11-02"
        }),
        content_type="application/json"
    )

    assert response_nonexistent.status_code == 400

    # Salary is an income category, not an expense category.
    response_mismatch = client.post(
        "/api/transactions",
        data=json.dumps({
            "amount": 1000.0,
            "transaction_type": "Expense",
            "category_id": 9,
            "transaction_date": "2026-11-02"
        }),
        content_type="application/json"
    )

    assert response_mismatch.status_code == 400

    message = response_mismatch.get_json()["message"].lower()

    assert "cannot be used for an 'expense' transaction" in message


def test_invalid_transaction_date(client):
    """Test rejection of an incorrectly formatted transaction date."""

    response = client.post(
        "/api/transactions",
        data=json.dumps({
            "amount": 500.0,
            "transaction_type": "Expense",
            "category_id": 1,
            "transaction_date": "02/11/2026"
        }),
        content_type="application/json"
    )

    assert response.status_code == 400

    message = response.get_json()["message"].lower()

    assert "yyyy-mm-dd" in message


def test_retrieve_and_filter_transactions(client):
    """Test retrieving transactions and applying filters."""

    # Add an income transaction.
    income_response = client.post(
        "/api/transactions",
        data=json.dumps({
            "amount": 50000.0,
            "transaction_type": "Income",
            "category_id": 9,
            "transaction_date": "2026-11-01",
            "description": "Salary"
        }),
        content_type="application/json"
    )

    assert income_response.status_code == 201

    # Add an expense transaction.
    expense_response = client.post(
        "/api/transactions",
        data=json.dumps({
            "amount": 2500.0,
            "transaction_type": "Expense",
            "category_id": 3,
            "transaction_date": "2026-11-02",
            "description": "Transit"
        }),
        content_type="application/json"
    )

    assert expense_response.status_code == 201

    # Retrieve all transactions.
    all_response = client.get("/api/transactions")

    assert all_response.status_code == 200

    all_data = all_response.get_json()["data"]

    assert len(all_data) >= 2

    # Filter by expense type.
    expense_filter_response = client.get(
        "/api/transactions?type=Expense"
    )

    assert expense_filter_response.status_code == 200

    expense_data = expense_filter_response.get_json()["data"]

    assert all(
        transaction["transaction_type"] == "expense"
        for transaction in expense_data
    )

    # Filter by month and year.
    month_response = client.get(
        "/api/transactions?month=11&year=2026"
    )

    assert month_response.status_code == 200


def test_update_and_delete_transaction(client):
    """Test updating and deleting an existing transaction."""

    # Create a transaction.
    create_response = client.post(
        "/api/transactions",
        data=json.dumps({
            "amount": 1200.0,
            "transaction_type": "Expense",
            "category_id": 1,
            "transaction_date": "2026-11-02",
            "description": "Original purchase"
        }),
        content_type="application/json"
    )

    assert create_response.status_code == 201

    transaction_id = (
        create_response.get_json()["data"]["transaction_id"]
    )

    # Update amount and description.
    update_response = client.put(
        f"/api/transactions/{transaction_id}",
        data=json.dumps({
            "amount": 1500.0,
            "description": "Updated purchase with extras"
        }),
        content_type="application/json"
    )

    assert update_response.status_code == 200

    updated_data = update_response.get_json()["data"]

    assert updated_data["amount"] == 1500.0
    assert updated_data["description"] == (
        "Updated purchase with extras"
    )

    # Delete the transaction.
    delete_response = client.delete(
        f"/api/transactions/{transaction_id}"
    )

    assert delete_response.status_code == 200

    # Verify that it no longer exists.
    get_response = client.get(
        f"/api/transactions/{transaction_id}"
    )

    assert get_response.status_code == 404
