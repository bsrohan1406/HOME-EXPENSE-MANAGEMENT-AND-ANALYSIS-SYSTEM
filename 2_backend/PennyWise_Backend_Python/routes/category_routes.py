"""
Category Routes Blueprint for PennyWise Backend.

Exposes endpoints for:
- Viewing categories
- Creating categories
- Updating categories
- Deleting categories
"""

from flask import Blueprint, request

from services.category_service import CategoryService
from utils.response import success_response, error_response
from database import DatabaseError


category_bp = Blueprint(
    "category_bp",
    __name__,
    url_prefix="/api/categories"
)


@category_bp.route("", methods=["GET"])
def get_categories():
    """
    GET /api/categories

    Optional query parameter:
    - type: Income or Expense
    """

    try:
        category_type = request.args.get("type")

        categories = CategoryService.get_all_categories(
            category_type=category_type
        )

        return success_response(
            data=categories,
            message=f"Retrieved {len(categories)} categories successfully"
        )

    except ValueError as ve:
        return error_response(
            str(ve),
            status_code=400
        )

    except DatabaseError as de:
        return error_response(
            str(de),
            status_code=500
        )

    except Exception:
        return error_response(
            "An unexpected error occurred while retrieving categories.",
            status_code=500
        )


@category_bp.route("/<int:category_id>", methods=["GET"])
def get_category_by_id(category_id: int):
    """
    GET /api/categories/<category_id>

    Retrieve a specific category by its ID.
    """

    try:
        category = CategoryService.get_category_by_id(
            category_id
        )

        if not category:
            return error_response(
                f"Category with ID {category_id} not found",
                status_code=404
            )

        return success_response(
            data=category,
            message="Category retrieved successfully"
        )

    except DatabaseError as de:
        return error_response(
            str(de),
            status_code=500
        )

    except Exception:
        return error_response(
            "An unexpected error occurred while retrieving the category.",
            status_code=500
        )


@category_bp.route("", methods=["POST"])
def create_category():
    """
    POST /api/categories

    Expected JSON:

    {
        "name": "Groceries",
        "type": "Expense",
        "color": "#FF5733"
    }
    """

    try:
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return error_response(
                "Request body must be a valid JSON object.",
                status_code=400
            )

        name = data.get("name")
        category_type = data.get("type")
        color = data.get("color")

        new_category = CategoryService.create_category(
            name=name,
            category_type=category_type,
            color=color
        )

        return success_response(
            data=new_category,
            message="Category created successfully",
            status_code=201
        )

    except ValueError as ve:
        error_message = str(ve)

        status_code = (
            409 if "already exists" in error_message.lower()
            else 400
        )

        return error_response(
            error_message,
            status_code=status_code
        )

    except DatabaseError as de:
        return error_response(
            str(de),
            status_code=500
        )

    except Exception:
        return error_response(
            "An unexpected error occurred while creating the category.",
            status_code=500
        )


@category_bp.route("/<int:category_id>", methods=["PUT"])
def update_category(category_id: int):
    """
    PUT /api/categories/<category_id>

    Expected JSON:

    {
        "name": "Food",
        "type": "Expense",
        "color": "#33A1FF"
    }
    """

    try:
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return error_response(
                "Request body must be a valid JSON object.",
                status_code=400
            )

        updated = CategoryService.update_category(
            category_id=category_id,
            name=data.get("name"),
            category_type=data.get("type"),
            color=data.get("color")
        )

        return success_response(
            data=updated,
            message="Category updated successfully"
        )

    except KeyError as ke:
        return error_response(
            str(ke).strip("'"),
            status_code=404
        )

    except ValueError as ve:
        error_message = str(ve)

        status_code = (
            409 if "already exists" in error_message.lower()
            else 400
        )

        return error_response(
            error_message,
            status_code=status_code
        )

    except DatabaseError as de:
        return error_response(
            str(de),
            status_code=500
        )

    except Exception:
        return error_response(
            "An unexpected error occurred while updating the category.",
            status_code=500
        )


@category_bp.route("/<int:category_id>", methods=["DELETE"])
def delete_category(category_id: int):
    """
    DELETE /api/categories/<category_id>

    Delete a category if no transactions or budgets reference it.
    """

    try:
        CategoryService.delete_category(category_id)

        return success_response(
            data={"category_id": category_id},
            message="Category deleted successfully"
        )

    except KeyError as ke:
        return error_response(
            str(ke).strip("'"),
            status_code=404
        )

    except ValueError as ve:
        return error_response(
            str(ve),
            status_code=409
        )

    except DatabaseError as de:
        return error_response(
            str(de),
            status_code=500
        )

    except Exception:
        return error_response(
            "An unexpected error occurred while deleting the category.",
            status_code=500
        )