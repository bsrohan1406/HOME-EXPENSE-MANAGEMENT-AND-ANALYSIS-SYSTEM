"""
Transaction Service module for PennyWise Backend.

Handles business logic, validations, and database queries
for income and expense transactions.

Uses the approved MySQL schema:

transactions:
- id
- kind
- amount
- transaction_date
- category_id
- description

categories:
- id
- name
- kind
- color
"""

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple

from database import execute_query, DatabaseError
from services.category_service import CategoryService


class TransactionService:

    @staticmethod
    def _validate_transaction_payload(
        amount: Any,
        transaction_type: str,
        category_id: int,
        transaction_date: str,
        description: Optional[str] = None
    ) -> Tuple[Decimal, str, int, str, Optional[str]]:
        """Validate and sanitize transaction input data."""

        # 1. Validate amount
        if amount is None:
            raise ValueError("Transaction amount is required.")

        try:
            amount_dec = Decimal(str(amount).strip())
        except (InvalidOperation, ValueError, TypeError):
            raise ValueError(
                "Transaction amount must be a valid number."
            )

        if not amount_dec.is_finite() or amount_dec <= Decimal("0.00"):
            raise ValueError("Amount must be greater than zero.")

        if amount_dec.as_tuple().exponent < -2:
            raise ValueError(
                "Transaction amount cannot have more than 2 decimal places."
            )

        # 2. Validate transaction type
        if not transaction_type or not str(transaction_type).strip():
            raise ValueError("Transaction type is required.")

        clean_type = str(transaction_type).strip().lower()

        if clean_type not in ("income", "expense"):
            raise ValueError(
                "Transaction type must be either 'Income' or 'Expense'."
            )

        # 3. Validate category
        if category_id is None:
            raise ValueError("Category ID is required.")

        try:
            cat_id_int = int(category_id)
        except (ValueError, TypeError):
            raise ValueError("Category ID must be an integer.")

        if cat_id_int <= 0:
            raise ValueError("Category ID must be a positive integer.")

        category = CategoryService.get_category_by_id(cat_id_int)

        if not category:
            raise ValueError(
                f"Category with ID {cat_id_int} does not exist."
            )

        category_type = str(category["type"]).strip().lower()

        if category_type != clean_type:
            raise ValueError(
                f"Category '{category['name']}' is an "
                f"'{category_type}' category, which cannot be used "
                f"for an '{clean_type}' transaction."
            )

        # 4. Validate date
        if not transaction_date or not str(transaction_date).strip():
            raise ValueError("Transaction date is required.")

        clean_date_str = str(transaction_date).strip()

        try:
            parsed_date = datetime.strptime(
                clean_date_str,
                "%Y-%m-%d"
            ).date()

            clean_date_str = parsed_date.strftime("%Y-%m-%d")

        except ValueError:
            raise ValueError(
                "Transaction date must be in YYYY-MM-DD format."
            )

        # 5. Validate description
        clean_desc = (
            str(description).strip()
            if description is not None
            else None
        )

        if clean_desc and len(clean_desc) > 255:
            raise ValueError(
                "Description cannot exceed 255 characters."
            )

        return (
            amount_dec,
            clean_type,
            cat_id_int,
            clean_date_str,
            clean_desc
        )

    @staticmethod
    def _format_transaction_row(
        row: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format database row for JSON response."""

        if not row:
            return row

        result = dict(row)

        if result.get("amount") is not None:
            result["amount"] = float(result["amount"])

        if result.get("transaction_date") is not None:
            result["transaction_date"] = str(
                result["transaction_date"]
            )

        return result

    @staticmethod
    def get_all_transactions(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        month: Optional[int] = None,
        year: Optional[int] = None,
        category_id: Optional[int] = None,
        transaction_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve transactions with filtering options."""

        query = """
            SELECT
                t.id AS transaction_id,
                t.transaction_date,
                t.kind AS transaction_type,
                t.category_id,
                c.name AS category_name,
                c.kind AS category_type,
                t.amount,
                t.description
            FROM transactions t
            INNER JOIN categories c
                ON t.category_id = c.id
            WHERE 1=1
        """

        params = []

        if transaction_type:
            clean_type = str(transaction_type).strip().lower()

            if clean_type not in ("income", "expense"):
                raise ValueError(
                    "Transaction type must be either 'Income' or 'Expense'."
                )

            query += " AND t.kind = %s"
            params.append(clean_type)

        if category_id is not None:
            try:
                category_id = int(category_id)
            except (ValueError, TypeError):
                raise ValueError("Category ID must be an integer.")

            query += " AND t.category_id = %s"
            params.append(category_id)

        if start_date:
            query += " AND t.transaction_date >= %s"
            params.append(start_date)

        if end_date:
            query += " AND t.transaction_date <= %s"
            params.append(end_date)

        if month is not None:
            month = int(month)

            if not 1 <= month <= 12:
                raise ValueError("Month must be between 1 and 12.")

            query += " AND MONTH(t.transaction_date) = %s"
            params.append(month)

        if year is not None:
            year = int(year)

            if not 1 <= year <= 9999:
                raise ValueError("Invalid year.")

            query += " AND YEAR(t.transaction_date) = %s"
            params.append(year)

        query += """
            ORDER BY
                t.transaction_date DESC,
                t.id DESC
        """

        rows = execute_query(
            query,
            tuple(params),
            fetch_all=True
        )

        return [
            TransactionService._format_transaction_row(row)
            for row in rows
        ]

    @staticmethod
    def get_transaction_by_id(
        transaction_id: int
    ) -> Optional[Dict[str, Any]]:
        """Retrieve a single transaction by ID."""

        query = """
            SELECT
                t.id AS transaction_id,
                t.transaction_date,
                t.kind AS transaction_type,
                t.category_id,
                c.name AS category_name,
                c.kind AS category_type,
                t.amount,
                t.description
            FROM transactions t
            INNER JOIN categories c
                ON t.category_id = c.id
            WHERE t.id = %s
        """

        row = execute_query(
            query,
            (transaction_id,),
            fetch_one=True
        )

        return (
            TransactionService._format_transaction_row(row)
            if row else None
        )

    @staticmethod
    def create_transaction(
        amount: Any,
        transaction_type: str,
        category_id: int,
        transaction_date: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new income or expense transaction."""

        (
            amount_dec,
            clean_type,
            cat_id,
            clean_date,
            clean_desc
        ) = TransactionService._validate_transaction_payload(
            amount,
            transaction_type,
            category_id,
            transaction_date,
            description
        )

        query = """
            INSERT INTO transactions (
                transaction_date,
                kind,
                category_id,
                amount,
                description
            )
            VALUES (%s, %s, %s, %s, %s)
        """

        transaction_id = execute_query(
            query,
            (
                clean_date,
                clean_type,
                cat_id,
                amount_dec,
                clean_desc
            ),
            commit=True
        )

        created_transaction = (
            TransactionService.get_transaction_by_id(
                transaction_id
            )
        )

        if not created_transaction:
            raise DatabaseError(
                "Transaction was created but could not be retrieved."
            )

        return created_transaction

    @staticmethod
    def update_transaction(
        transaction_id: int,
        amount: Optional[Any] = None,
        transaction_type: Optional[str] = None,
        category_id: Optional[int] = None,
        transaction_date: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update an existing transaction."""

        current = TransactionService.get_transaction_by_id(
            transaction_id
        )

        if not current:
            raise KeyError(
                f"Transaction with ID {transaction_id} not found."
            )

        target_amount = (
            amount if amount is not None
            else current["amount"]
        )

        target_type = (
            transaction_type if transaction_type is not None
            else current["transaction_type"]
        )

        target_cat_id = (
            category_id if category_id is not None
            else current["category_id"]
        )

        target_date = (
            transaction_date if transaction_date is not None
            else current["transaction_date"]
        )

        target_desc = (
            description if description is not None
            else current["description"]
        )

        (
            amount_dec,
            clean_type,
            cat_id,
            clean_date,
            clean_desc
        ) = TransactionService._validate_transaction_payload(
            target_amount,
            target_type,
            target_cat_id,
            target_date,
            target_desc
        )

        query = """
            UPDATE transactions
            SET
                transaction_date = %s,
                kind = %s,
                category_id = %s,
                amount = %s,
                description = %s
            WHERE id = %s
        """

        execute_query(
            query,
            (
                clean_date,
                clean_type,
                cat_id,
                amount_dec,
                clean_desc,
                transaction_id
            ),
            commit=True
        )

        updated_transaction = (
            TransactionService.get_transaction_by_id(
                transaction_id
            )
        )

        if not updated_transaction:
            raise DatabaseError(
                "Transaction was updated but could not be retrieved."
            )

        return updated_transaction

    @staticmethod
    def delete_transaction(transaction_id: int) -> bool:
        """Delete a transaction by ID."""

        current = TransactionService.get_transaction_by_id(
            transaction_id
        )

        if not current:
            raise KeyError(
                f"Transaction with ID {transaction_id} not found."
            )

        execute_query(
            "DELETE FROM transactions WHERE id = %s",
            (transaction_id,),
            commit=True
        )

        return True