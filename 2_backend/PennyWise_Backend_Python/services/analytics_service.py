
"""
Analytics Service module for PennyWise Backend.

Computes financial summaries, savings rates, monthly trends,
and category distributions.

Provides structured numerical data for the data-analysis module
and REST endpoints.
"""

from typing import Any, Dict, List, Optional
from datetime import date

from database import execute_query
from services.budget_service import BudgetService


class AnalyticsService:

    @staticmethod
    def _validate_period(
        month: Optional[int] = None,
        year: Optional[int] = None
    ):
        """Validate optional month and year filters."""

        if month is not None:
            try:
                month = int(month)
            except (ValueError, TypeError):
                raise ValueError("Month must be an integer between 1 and 12.")

            if not 1 <= month <= 12:
                raise ValueError("Month must be between 1 and 12.")

        if year is not None:
            try:
                year = int(year)
            except (ValueError, TypeError):
                raise ValueError("Year must be a valid integer.")

            if not 2000 <= year <= 2100:
                raise ValueError("Year must be between 2000 and 2100.")

        return month, year

    @staticmethod
    def get_financial_summary(
        month: Optional[int] = None,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Calculate total income, expenses, savings, savings rate,
        and overall budget performance.

        If no month or year is supplied, calculate lifetime totals.
        """

        month, year = AnalyticsService._validate_period(month, year)

        # 1. Fetch income and expense totals.
        tx_query = """
            SELECT
                kind,
                COALESCE(SUM(amount), 0.00) AS total_amount,
                COUNT(*) AS transaction_count
            FROM transactions
            WHERE 1 = 1
        """

        params = []

        if month is not None:
            tx_query += " AND MONTH(transaction_date) = %s"
            params.append(month)

        if year is not None:
            tx_query += " AND YEAR(transaction_date) = %s"
            params.append(year)

        tx_query += " GROUP BY kind"

        rows = execute_query(
            tx_query,
            tuple(params),
            fetch_all=True
        )

        total_income = 0.0
        total_expense = 0.0
        income_tx_count = 0
        expense_tx_count = 0

        for row in rows:
            transaction_kind = str(row["kind"]).lower()
            amount = float(row["total_amount"])
            count = int(row["transaction_count"])

            if transaction_kind == "income":
                total_income = amount
                income_tx_count = count

            elif transaction_kind == "expense":
                total_expense = amount
                expense_tx_count = count

        # 2. Calculate savings.
        total_savings = round(total_income - total_expense, 2)

        savings_rate_pct = (
            round((total_savings / total_income) * 100, 2)
            if total_income > 0 else 0.0
        )

        # 3. Fetch budget performance.
        budgets = BudgetService.get_budgets(
            month=month,
            year=year
        )

        total_budget = round(
            sum(b["budget_amount"] for b in budgets), 2
        )

        total_budget_spent = round(
            sum(b["amount_spent"] for b in budgets), 2
        )

        total_remaining_budget = round(
            total_budget - total_budget_spent, 2
        )

        over_budget_count = sum(
            1 for b in budgets if b["is_over_budget"]
        )

        budget_utilization_pct = (
            round((total_budget_spent / total_budget) * 100, 2)
            if total_budget > 0 else 0.0
        )

        return {
            "period": {
                "month": month,
                "year": year
            },
            "income": {
                "total": round(total_income, 2),
                "transaction_count": income_tx_count
            },
            "expense": {
                "total": round(total_expense, 2),
                "transaction_count": expense_tx_count
            },
            "savings": {
                "total": total_savings,
                "savings_rate_pct": savings_rate_pct
            },
            "budget": {
                "total_budget": total_budget,
                "total_spent_on_budgeted": total_budget_spent,
                "remaining_budget": total_remaining_budget,
                "budget_utilization_pct": budget_utilization_pct,
                "over_budget_categories_count": over_budget_count,
                "total_budgeted_categories": len(budgets)
            }
        }

    @staticmethod
    def get_monthly_breakdown(
        year: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve month-by-month financial breakdown
        for a specific year.

        If year is omitted, use the current calendar year.
        """

        if year is None:
            target_year = date.today().year
        else:
            _, target_year = AnalyticsService._validate_period(
                year=year
            )

        month_names = {
            1: "January",
            2: "February",
            3: "March",
            4: "April",
            5: "May",
            6: "June",
            7: "July",
            8: "August",
            9: "September",
            10: "October",
            11: "November",
            12: "December"
        }

        # 1. Fetch monthly transaction totals.
        query = """
            SELECT
                MONTH(transaction_date) AS month_number,
                kind,
                COALESCE(SUM(amount), 0.00) AS total_amount
            FROM transactions
            WHERE YEAR(transaction_date) = %s
            GROUP BY MONTH(transaction_date), kind
            ORDER BY month_number ASC
        """

        rows = execute_query(
            query,
            (target_year,),
            fetch_all=True
        )

        monthly_data = {
            month_number: {
                "month": month_number,
                "month_name": month_names[month_number],
                "income": 0.0,
                "expense": 0.0,
                "budget": 0.0
            }
            for month_number in range(1, 13)
        }

        for row in rows:
            month_number = int(row["month_number"])
            transaction_kind = str(row["kind"]).lower()
            amount = float(row["total_amount"])

            if transaction_kind == "income":
                monthly_data[month_number]["income"] = round(
                    amount, 2
                )

            elif transaction_kind == "expense":
                monthly_data[month_number]["expense"] = round(
                    amount, 2
                )

        # 2. Fetch monthly budget totals.
        budget_query = """
            SELECT
                CAST(RIGHT(month, 2) AS UNSIGNED) AS month_number,
                COALESCE(SUM(amount), 0.00) AS total_budget
            FROM budgets
            WHERE LEFT(month, 4) = %s
            GROUP BY month
        """

        budget_rows = execute_query(
            budget_query,
            (f"{target_year:04d}",),
            fetch_all=True
        )

        for row in budget_rows:
            month_number = int(row["month_number"])

            if month_number in monthly_data:
                monthly_data[month_number]["budget"] = round(
                    float(row["total_budget"]), 2
                )

        # 3. Calculate monthly savings and budget utilization.
        results = []

        for month_number in range(1, 13):
            item = monthly_data[month_number]

            income = item["income"]
            expense = item["expense"]
            budget = item["budget"]

            savings = round(income - expense, 2)

            savings_rate = (
                round((savings / income) * 100, 2)
                if income > 0 else 0.0
            )

            utilization = (
                round((expense / budget) * 100, 2)
                if budget > 0 else 0.0
            )

            results.append({
                "year": target_year,
                "month": month_number,
                "month_name": item["month_name"],
                "income": income,
                "expense": expense,
                "savings": savings,
                "savings_rate_pct": savings_rate,
                "budget": budget,
                "budget_utilization_pct": utilization
            })

        return results

    @staticmethod
    def get_category_distribution(
        month: Optional[int] = None,
        year: Optional[int] = None,
        transaction_type: str = "Expense"
    ) -> List[Dict[str, Any]]:
        """
        Calculate income or expense distribution across categories.

        Includes total amount, transaction count,
        and percentage share of the total.
        """

        month, year = AnalyticsService._validate_period(
            month,
            year
        )

        clean_type = str(transaction_type).strip().lower()

        if clean_type not in ("income", "expense"):
            raise ValueError(
                "Transaction type must be Income or Expense."
            )

        query = """
            SELECT
                c.id AS category_id,
                c.name AS category_name,
                c.kind AS category_type,
                COALESCE(SUM(t.amount), 0.00) AS total_amount,
                COUNT(t.id) AS transaction_count
            FROM categories c
            LEFT JOIN transactions t
                ON c.id = t.category_id
                AND t.kind = %s
        """

        params = [clean_type]

        if month is not None:
            query += " AND MONTH(t.transaction_date) = %s"
            params.append(month)

        if year is not None:
            query += " AND YEAR(t.transaction_date) = %s"
            params.append(year)

        query += """
            WHERE c.kind = %s
            GROUP BY c.id, c.name, c.kind
            HAVING total_amount > 0
            ORDER BY total_amount DESC
        """

        params.append(clean_type)

        rows = execute_query(
            query,
            tuple(params),
            fetch_all=True
        )

        total_sum = sum(
            float(row["total_amount"])
            for row in rows
        )

        results = []

        for row in rows:
            amount = float(row["total_amount"])

            percentage = (
                round((amount / total_sum) * 100, 2)
                if total_sum > 0 else 0.0
            )

            results.append({
                "category_id": row["category_id"],
                "category_name": row["category_name"],
                "category_type": row["category_type"],
                "total_amount": round(amount, 2),
                "transaction_count": int(
                    row["transaction_count"]
                ),
                "percentage_of_total": percentage
            })

        return results

    @staticmethod
    def get_budget_status(
        month: Optional[int] = None,
        year: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve budget status by comparing allocated budgets
        with actual category expenditure.
        """

        month, year = AnalyticsService._validate_period(
            month,
            year
        )

        return BudgetService.get_budgets(
            month=month,
            year=year
        )
