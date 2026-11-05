
"""
Transaction Routes Blueprint for PennyWise Backend.
Exposes endpoints for viewing, adding, updating, and deleting transactions.
"""

from flask import Blueprint, request

from services.transaction_service import TransactionService
from utils.response import success_response, error_response
from database import DatabaseError


transaction_bp = Blueprint(
    "transaction_bp",
    __name__,
    url_prefix="/api/transactions"
)


@transaction_bp.route("", methods=["GET"])
def get_transactions():
    """
    GET /api/transactions

    Query Parameters:
    - start_date (YYYY-MM-DD)
    - end_date (YYYY-MM-DD)
    - date (YYYY-MM-DD)
    - month (1-12)
    - year (YYYY)
    - category_id (integer)
    - type (Income or Expense)
    """
    try:
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        single_date = request.args.get("date")

        if single_date:
            start_date = single_date
            end_date = single_date

        month = request.args.get("month", type=int)
        year = request.args.get("year", type=int)
        category_id = request.args.get("category_id", type=int)
        tx_type = request.args.get("type")

        transactions = TransactionService.get_all_transactions(
            start_date=start_date,
            end_date=end_date,
            month=month,
            year=year,
            category_id=category_id,
            transaction_type=tx_type
        )

        return success_response(
            data=transactions,
            message=f"Retrieved {len(transactions)} transactions successfully"
        )

    except ValueError as ve:
        return error_response(str(ve), status_code=400)

    except DatabaseError as de:
        return error_response(str(de), status_code=500)

    except Exception:
        return error_response(
            "An unexpected error occurred while retrieving transactions.",
            status_code=500
        )


@transaction_bp.route("/<int:transaction_id>", methods=["GET"])
def get_transaction_by_id(transaction_id: int):
    """
    GET /api/transactions/<id>
    Retrieve a single transaction by ID.
    """
    try:
        transaction = TransactionService.get_transaction_by_id(
            transaction_id
        )

        if not transaction:
            return error_response(
                f"Transaction with ID {transaction_id} not found",
                status_code=404
            )

        return success_response(
            data=transaction,
            message="Transaction retrieved successfully"
        )

    except DatabaseError as de:
        return error_response(str(de), status_code=500)

    except Exception:
        return error_response(
            "An unexpected error occurred while retrieving the transaction.",
            status_code=500
        )


@transaction_bp.route("", methods=["POST"])
def create_transaction():
    """
    POST /api/transactions

    JSON Body:
    {
        "amount": 1500.50,
        "transaction_type": "Expense",
        "category_id": 1,
        "transaction_date": "2026-11-02",
        "description": "Weekly grocery purchase"
    }
    """
    try:
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return error_response(
                "Request body must be a valid JSON object.",
                status_code=400
            )

        new_transaction = TransactionService.create_transaction(
            amount=data.get("amount"),
            transaction_type=data.get("transaction_type"),
            category_id=data.get("category_id"),
            transaction_date=data.get("transaction_date"),
            description=data.get("description")
        )

        return success_response(
            data=new_transaction,
            message="Transaction added successfully",
            status_code=201
        )

    except ValueError as ve:
        return error_response(str(ve), status_code=400)

    except DatabaseError as de:
        return error_response(str(de), status_code=500)

    except Exception:
        return error_response(
            "An unexpected error occurred while adding the transaction.",
            status_code=500
        )


@transaction_bp.route("/<int:transaction_id>", methods=["PUT"])
def update_transaction(transaction_id: int):
    """
    PUT /api/transactions/<id>
    Update an existing transaction.
    """
    try:
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return error_response(
                "Request body must be a valid JSON object.",
                status_code=400
            )

        updated = TransactionService.update_transaction(
            transaction_id=transaction_id,
            amount=data.get("amount"),
            transaction_type=data.get("transaction_type"),
            category_id=data.get("category_id"),
            transaction_date=data.get("transaction_date"),
            description=data.get("description")
        )

        return success_response(
            data=updated,
            message="Transaction updated successfully"
        )

    except KeyError as ke:
        return error_response(
            str(ke).strip("'"),
            status_code=404
        )

    except ValueError as ve:
        return error_response(str(ve), status_code=400)

    except DatabaseError as de:
        return error_response(str(de), status_code=500)

    except Exception:
        return error_response(
            "An unexpected error occurred while updating the transaction.",
            status_code=500
        )


@transaction_bp.route("/<int:transaction_id>", methods=["DELETE"])
def delete_transaction(transaction_id: int):
    """
    DELETE /api/transactions/<id>
    Delete a transaction by ID.
    """
    try:
        TransactionService.delete_transaction(transaction_id)

        return success_response(
            data={"transaction_id": transaction_id},
            message="Transaction deleted successfully"
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
            "An unexpected error occurred while deleting the transaction.",
            status_code=500
        )
