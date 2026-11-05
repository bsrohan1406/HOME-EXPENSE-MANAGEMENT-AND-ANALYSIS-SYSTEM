
"""
Budget Service module for PennyWise Backend.
Handles budget creation, validation, updates, deletion,
and monthly spending comparisons.
"""

from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple

from database import execute_query
from services.category_service import CategoryService


class BudgetService:

    @staticmethod
    def _validate_budget_payload(
        category_id: int,
        month: int,
        year: int,
        budget_amount: Any
    ) -> Tuple[int, int, int, Decimal]:
        """Validate and sanitize budget inputs."""

        # Validate category ID
        if category_id is None:
            raise ValueError("Category ID is required.")

        try:
            cat_id_int = int(category_id)
        except (ValueError, TypeError):
            raise ValueError("Category ID must be an integer.")

        if cat_id_int <= 0:
            raise ValueError("Category ID must be greater than zero.")

        category = CategoryService.get_category_by_id(cat_id_int)

        if not category:
            raise ValueError(
                f"Category with ID {cat_id_int} does not exist."
            )

        category_type = str(category.get("type", "")).lower()

        if category_type != "expense":
            raise ValueError(
                f"Budgets can only be set for Expense categories. "
                f"'{category['name']}' is an Income category."
            )

        # Validate month
        if month is None:
            raise ValueError("Month is required.")

        try:
            month_int = int(month)
        except (ValueError, TypeError):
            raise ValueError("Month must be an integer between 1 and 12.")

        if not 1 <= month_int <= 12:
            raise ValueError("Month must be between 1 and 12.")

        # Validate year
        if year is None:
            raise ValueError("Year is required.")

        try:
            year_int = int(year)
        except (ValueError, TypeError):
            raise ValueError("Year must be a valid 4-digit integer.")

        if not 2000 <= year_int <= 2100:
            raise ValueError("Year must be between 2000 and 2100.")

        # Validate budget amount
        if budget_amount is None:
            raise ValueError("Budget amount is required.")

        try:
            amount_dec = Decimal(str(budget_amount).strip())

            if not amount_dec.is_finite():
                raise ValueError("Budget amount must be a valid number.")

        except (InvalidOperation, ValueError, TypeError):
            raise ValueError("Budget amount must be a valid number.")

        if amount_dec <= Decimal("0.00"):
            raise ValueError("Budget amount must be greater than zero.")

        if amount_dec.as_tuple().exponent < -2:
            raise ValueError(
                "Budget amount cannot have more than two decimal places."
            )

        return cat_id_int, month_int, year_int, amount_dec

    @staticmethod
    def _calculate_budget_metrics(
        budget_amount: float,
        actual_spent: float
    ) -> Dict[str, Any]:
        """Calculate budget utilization and remaining balance."""

        budget_amount = float(budget_amount)
        actual_spent = float(actual_spent)

        remaining = round(budget_amount - actual_spent, 2)
        is_over = actual_spent > budget_amount

        overrun_amount = (
            round(actual_spent - budget_amount, 2)
            if is_over else 0.0
        )

        utilization_pct = (
            round((actual_spent / budget_amount) * 100, 2)
            if budget_amount > 0 else 0.0
        )

        return {
            "budget_amount": round(budget_amount, 2),
            "amount_spent": round(actual_spent, 2),
            "remaining_budget": remaining,
            "budget_utilization_pct": utilization_pct,
            "is_over_budget": is_over,
            "overrun_amount": overrun_amount
        }

    @staticmethod
    def _format_budget_row(row: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a database budget row into an API response."""

        month_value = str(row["month"])
        year_int, month_int = map(int, month_value.split("-"))

        metrics = BudgetService._calculate_budget_metrics(
            budget_amount=float(row["budget_amount"]),
            actual_spent=float(row["amount_spent"])
        )

        return {
            "budget_id": row["budget_id"],
            "category_id": row["category_id"],
            "category_name": row["category_name"],
            "month": month_int,
            "year": year_int,
            **metrics
        }

    @staticmethod
    def get_actual_spending_for_category(
        category_id: int,
        month: int,
        year: int
    ) -> float:
        """Get actual expenses for a category in a given month."""

        month_key = f"{int(year):04d}-{int(month):02d}"

        query = """
            SELECT COALESCE(SUM(amount), 0.00) AS total_spent
            FROM transactions
            WHERE category_id = %s
              AND kind = 'expense'
              AND DATE_FORMAT(transaction_date, '%Y-%m') = %s
        """

        result = execute_query(
            query,
            (category_id, month_key),
            fetch_one=True
        )

        return (
            float(result["total_spent"])
            if result and result["total_spent"] is not None
            else 0.0
        )

    @staticmethod
    def get_budgets(
        month: Optional[int] = None,
        year: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve budgets with monthly spending comparisons."""

        query = """
            SELECT
                b.id AS budget_id,
                b.category_id,
                c.name AS category_name,
                b.month,
                b.amount AS budget_amount,
                COALESCE((
                    SELECT SUM(t.amount)
                    FROM transactions t
                    WHERE t.category_id = b.category_id
                      AND t.kind = 'expense'
                      AND DATE_FORMAT(
                          t.transaction_date, '%Y-%m'
                      ) = b.month
                ), 0.00) AS amount_spent
            FROM budgets b
            INNER JOIN categories c
                ON b.category_id = c.id
            WHERE 1 = 1
        """

        params = []

        if month is not None:
            try:
                month = int(month)
            except (ValueError, TypeError):
                raise ValueError("Month must be between 1 and 12.")

            if not 1 <= month <= 12:
                raise ValueError("Month must be between 1 and 12.")

            query += " AND RIGHT(b.month, 2) = %s"
            params.append(f"{month:02d}")

        if year is not None:
            try:
                year = int(year)
            except (ValueError, TypeError):
                raise ValueError("Year must be between 2000 and 2100.")

            if not 2000 <= year <= 2100:
                raise ValueError("Year must be between 2000 and 2100.")

            query += " AND LEFT(b.month, 4) = %s"
            params.append(f"{year:04d}")

        query += " ORDER BY b.month DESC, c.name ASC"

        rows = execute_query(
            query,
            tuple(params),
            fetch_all=True
        )

        return [
            BudgetService._format_budget_row(row)
            for row in rows
        ]

    @staticmethod
    def get_budget_by_id(
        budget_id: int
    ) -> Optional[Dict[str, Any]]:
        """Retrieve a single budget with spending metrics."""

        query = """
            SELECT
                b.id AS budget_id,
                b.category_id,
                c.name AS category_name,
                b.month,
                b.amount AS budget_amount,
                COALESCE((
                    SELECT SUM(t.amount)
                    FROM transactions t
                    WHERE t.category_id = b.category_id
                      AND t.kind = 'expense'
                      AND DATE_FORMAT(
                          t.transaction_date, '%Y-%m'
                      ) = b.month
                ), 0.00) AS amount_spent
            FROM budgets b
            INNER JOIN categories c
                ON b.category_id = c.id
            WHERE b.id = %s
        """

        row = execute_query(
            query,
            (budget_id,),
            fetch_one=True
        )

        if not row:
            return None

        return BudgetService._format_budget_row(row)

    @staticmethod
    def create_budget(
        category_id: int,
        month: int,
        year: int,
        budget_amount: Any
    ) -> Dict[str, Any]:
        """Create a monthly budget for an expense category."""

        cat_id, month_int, year_int, amount_dec = (
            BudgetService._validate_budget_payload(
                category_id,
                month,
                year,
                budget_amount
            )
        )

        month_key = f"{year_int:04d}-{month_int:02d}"

        # Check whether a budget already exists.
        existing = execute_query(
            """
            SELECT id
            FROM budgets
            WHERE category_id = %s AND month = %s
            """,
            (cat_id, month_key),
            fetch_one=True
        )

        if existing:
            raise ValueError(
                f"A budget for this category already exists "
                f"for {month_key}. Please update the existing "
                f"budget (ID: {existing['id']}) instead."
            )

        query = """
            INSERT INTO budgets (month, category_id, amount)
            VALUES (%s, %s, %s)
        """

        budget_id = execute_query(
            query,
            (month_key, cat_id, amount_dec),
            commit=True
        )

        return BudgetService.get_budget_by_id(budget_id)

    @staticmethod
    def update_budget(
        budget_id: int,
        budget_amount: Optional[Any] = None,
        month: Optional[int] = None,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """Update an existing budget."""

        current = BudgetService.get_budget_by_id(budget_id)

        if not current:
            raise KeyError(
                f"Budget with ID {budget_id} not found."
            )

        target_amount = (
            budget_amount
            if budget_amount is not None
            else current["budget_amount"]
        )

        target_month = (
            month if month is not None else current["month"]
        )

        target_year = (
            year if year is not None else current["year"]
        )

        cat_id, month_int, year_int, amount_dec = (
            BudgetService._validate_budget_payload(
                current["category_id"],
                target_month,
                target_year,
                target_amount
            )
        )

        month_key = f"{year_int:04d}-{month_int:02d}"

        # Check for a duplicate budget in the target month.
        existing = execute_query(
            """
            SELECT id
            FROM budgets
            WHERE category_id = %s
              AND month = %s
              AND id != %s
            """,
            (cat_id, month_key, budget_id),
            fetch_one=True
        )

        if existing:
            raise ValueError(
                f"A budget for this category already exists "
                f"for {month_key}."
            )

        query = """
            UPDATE budgets
            SET amount = %s, month = %s
            WHERE id = %s
        """

        execute_query(
            query,
            (amount_dec, month_key, budget_id),
            commit=True
        )

        return BudgetService.get_budget_by_id(budget_id)

    @staticmethod
    def delete_budget(budget_id: int) -> bool:
        """Delete a budget by ID."""

        current = BudgetService.get_budget_by_id(budget_id)

        if not current:
            raise KeyError(
                f"Budget with ID {budget_id} not found."
            )

        execute_query(
            "DELETE FROM budgets WHERE id = %s",
            (budget_id,),
            commit=True
        )

        return True
