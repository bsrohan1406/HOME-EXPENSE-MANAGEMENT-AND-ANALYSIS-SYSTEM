
"""
Budget Routes Blueprint for PennyWise Backend.
Exposes endpoints for creating, retrieving, updating, and deleting monthly
category budgets, including spending comparisons and overrun detection.
"""

from flask import Blueprint, request

from services.budget_service import BudgetService
from utils.response import success_response, error_response
from database import DatabaseError


budget_bp = Blueprint(
    "budget_bp",
    __name__,
    url_prefix="/api/budgets"
)


def get_optional_integer(value, field_name):
    """Convert an optional query parameter into an integer."""

    if value is None:
        return None

    try:
        return int(value)
    except (ValueError, TypeError):
        raise ValueError(f"{field_name} must be an integer.")


@budget_bp.route("", methods=["GET"])
def get_budgets():
    """
    GET /api/budgets

    Query Parameters:
    - month (1-12)
    - year (YYYY)
    """
    try:
        month = get_optional_integer(
            request.args.get("month"),
            "Month"
        )

        year = get_optional_integer(
            request.args.get("year"),
            "Year"
        )

        budgets = BudgetService.get_budgets(
            month=month,
            year=year
        )

        return success_response(
            data=budgets,
            message=f"Retrieved {len(budgets)} budget record(s) successfully"
        )

    except ValueError as ve:
        return error_response(str(ve), status_code=400)

    except DatabaseError as de:
        return error_response(str(de), status_code=500)

    except Exception:
        return error_response(
            "An unexpected error occurred while retrieving budgets.",
            status_code=500
        )


@budget_bp.route("/<int:budget_id>", methods=["GET"])
def get_budget_by_id(budget_id: int):
    """
    GET /api/budgets/<id>
    Retrieve a single budget by ID.
    """
    try:
        budget = BudgetService.get_budget_by_id(budget_id)

        if not budget:
            return error_response(
                f"Budget with ID {budget_id} not found",
                status_code=404
            )

        return success_response(
            data=budget,
            message="Budget retrieved successfully"
        )

    except DatabaseError as de:
        return error_response(str(de), status_code=500)

    except Exception:
        return error_response(
            "An unexpected error occurred while retrieving the budget.",
            status_code=500
        )


@budget_bp.route("", methods=["POST"])
def create_budget():
    """
    POST /api/budgets

    JSON Body:
    {
        "category_id": 1,
        "month": 11,
        "year": 2026,
        "budget_amount": 5000.00
    }
    """
    try:
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return error_response(
                "Request body must be a valid JSON object.",
                status_code=400
            )

        new_budget = BudgetService.create_budget(
            category_id=data.get("category_id"),
            month=data.get("month"),
            year=data.get("year"),
            budget_amount=data.get("budget_amount")
        )

        return success_response(
            data=new_budget,
            message="Budget created successfully",
            status_code=201
        )

    except ValueError as ve:
        err_msg = str(ve)

        status_code = (
            409 if "already exists" in err_msg.lower()
            else 400
        )

        return error_response(
            err_msg,
            status_code=status_code
        )

    except DatabaseError as de:
        return error_response(str(de), status_code=500)

    except Exception:
        return error_response(
            "An unexpected error occurred while creating the budget.",
            status_code=500
        )


@budget_bp.route("/<int:budget_id>", methods=["PUT"])
def update_budget(budget_id: int):
    """
    PUT /api/budgets/<id>

    JSON Body:
    {
        "budget_amount": 6000.00,
        "month": 11,
        "year": 2026
    }
    """
    try:
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return error_response(
                "Request body must be a valid JSON object.",
                status_code=400
            )

        updated = BudgetService.update_budget(
            budget_id=budget_id,
            budget_amount=data.get("budget_amount"),
            month=data.get("month"),
            year=data.get("year")
        )

        return success_response(
            data=updated,
            message="Budget updated successfully"
        )

    except KeyError as ke:
        return error_response(
            str(ke).strip("'"),
            status_code=404
        )

    except ValueError as ve:
        err_msg = str(ve)

        status_code = (
            409 if "already exists" in err_msg.lower()
            else 400
        )

        return error_response(
            err_msg,
            status_code=status_code
        )

    except DatabaseError as de:
        return error_response(str(de), status_code=500)

    except Exception:
        return error_response(
            "An unexpected error occurred while updating the budget.",
            status_code=500
        )


@budget_bp.route("/<int:budget_id>", methods=["DELETE"])
def delete_budget(budget_id: int):
    """
    DELETE /api/budgets/<id>
    Delete a budget by ID.
    """
    try:
        BudgetService.delete_budget(budget_id)

        return success_response(
            data={"budget_id": budget_id},
            message="Budget deleted successfully"
        )

    except KeyError as ke:
        return error_response(
            str(ke).strip("'"),
            status_code=404
        )

    except DatabaseError as de:
        return error_response(str(de), status_code=500)

    except Exception:
        return error_response(
            "An unexpected error occurred while deleting the budget.",
            status_code=500
        )
