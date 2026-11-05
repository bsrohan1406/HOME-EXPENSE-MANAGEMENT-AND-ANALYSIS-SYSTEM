
"""
Unit and integration tests for Category Management APIs
and CategoryService.

Tests follow the approved PennyWise MySQL schema:
categories(id, name, kind, color).
"""

import json


def test_get_all_categories(client):
    """Test retrieving all categories."""

    response = client.get("/api/categories")

    assert response.status_code == 200

    data = response.get_json()

    assert data["status"] == "success"
    assert len(data["data"]) >= 5
    assert any(
        category["name"] == "Groceries"
        for category in data["data"]
    )


def test_filter_categories_by_type(client):
    """Test filtering categories by income and expense type."""

    # Expense filter
    expense_response = client.get(
        "/api/categories?type=Expense"
    )

    assert expense_response.status_code == 200

    expense_data = expense_response.get_json()["data"]

    assert all(
        category["type"] == "expense"
        for category in expense_data
    )

    assert any(
        category["name"] == "Groceries"
        for category in expense_data
    )

    # Income filter
    income_response = client.get(
        "/api/categories?type=Income"
    )

    assert income_response.status_code == 200

    income_data = income_response.get_json()["data"]

    assert all(
        category["type"] == "income"
        for category in income_data
    )

    assert any(
        category["name"] == "Salary"
        for category in income_data
    )

    # Invalid type filter
    invalid_response = client.get(
        "/api/categories?type=InvalidType"
    )

    assert invalid_response.status_code == 400


def test_get_category_by_id(client):
    """Test retrieving a category by ID and handling 404."""

    # Existing category
    response = client.get("/api/categories/1")

    assert response.status_code == 200

    data = response.get_json()

    assert data["data"]["name"] == "Groceries"
    assert data["data"]["type"] == "expense"

    # Non-existing category
    response_404 = client.get("/api/categories/9999")

    assert response_404.status_code == 404
    assert response_404.get_json()["status"] == "error"


def test_create_category_success(client):
    """Test creating a new valid category."""

    payload = {
        "name": "Entertainment",
        "type": "Expense",
        "color": "#FF5733"
    }

    response = client.post(
        "/api/categories",
        data=json.dumps(payload),
        content_type="application/json"
    )

    assert response.status_code == 201

    data = response.get_json()

    assert data["status"] == "success"
    assert data["data"]["name"] == "Entertainment"
    assert data["data"]["type"] == "expense"
    assert data["data"]["color"] == "#FF5733"


def test_create_category_duplicate_conflict(client):
    """Test that duplicate categories return 409 Conflict."""

    payload = {
        "name": "Groceries",
        "type": "Expense",
        "color": "#FF5733"
    }

    response = client.post(
        "/api/categories",
        data=json.dumps(payload),
        content_type="application/json"
    )

    assert response.status_code == 409

    data = response.get_json()

    assert data["status"] == "error"
    assert "already exists" in data["message"].lower()


def test_create_category_validation_errors(client):
    """Test category validation errors."""

    # Empty category name
    response_empty = client.post(
        "/api/categories",
        data=json.dumps({
            "name": "",
            "type": "Expense"
        }),
        content_type="application/json"
    )

    assert response_empty.status_code == 400

    # Invalid category type
    response_invalid = client.post(
        "/api/categories",
        data=json.dumps({
            "name": "Misc",
            "type": "Invalid"
        }),
        content_type="application/json"
    )

    assert response_invalid.status_code == 400


def test_update_category(client):
    """Test updating category details."""

    payload = {
        "color": "#00FF00"
    }

    response = client.put(
        "/api/categories/1",
        data=json.dumps(payload),
        content_type="application/json"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["status"] == "success"
    assert data["data"]["color"] == "#00FF00"


def test_delete_category(client):
    """Test deleting an unreferenced category."""

    # Create a temporary category
    create_response = client.post(
        "/api/categories",
        data=json.dumps({
            "name": "TempToDelete",
            "type": "Expense",
            "color": "#123456"
        }),
        content_type="application/json"
    )

    assert create_response.status_code == 201

    category_id = create_response.get_json()["data"]["category_id"]

    # Delete the category
    delete_response = client.delete(
        f"/api/categories/{category_id}"
    )

    assert delete_response.status_code == 200

    # Verify that it no longer exists
    get_response = client.get(
        f"/api/categories/{category_id}"
    )

    assert get_response.status_code == 404
