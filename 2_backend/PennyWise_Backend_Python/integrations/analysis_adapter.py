
"""
Analysis Adapter Module for PennyWise Backend.

Coordinates between the Flask backend, MySQL data storage,
Pandas, NumPy, and Matplotlib.

Responsibilities:
1. Retrieve transaction and budget records from MySQL.
2. Convert records into Pandas DataFrames.
3. Provide structured data for the analysis module.
4. Generate four Matplotlib charts.
5. Return chart images as PNG bytes and Base64 strings.
"""

import base64
import io
import logging
from typing import Optional, Tuple

import matplotlib

# Headless backend for server-side chart generation.
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from database import execute_query
from services.analytics_service import AnalyticsService
from services.budget_service import BudgetService


logger = logging.getLogger(__name__)


class AnalysisAdapter:
    """Adapter between the Flask backend and data-analysis module."""

    # ============================================================
    # 1. TRANSACTION DATAFRAME
    # ============================================================

    @staticmethod
    def get_transactions_dataframe(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        month: Optional[int] = None,
        year: Optional[int] = None,
        transaction_type: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Retrieve transaction records from MySQL.

        DataFrame columns:
        transaction_id, transaction_date, transaction_type,
        category_id, category_name, amount, description
        """

        query = """
            SELECT
                t.id AS transaction_id,
                t.transaction_date,
                t.kind AS transaction_type,
                t.category_id,
                c.name AS category_name,
                t.amount,
                t.description
            FROM transactions t
            INNER JOIN categories c
                ON t.category_id = c.id
            WHERE 1 = 1
        """

        params = []

        if transaction_type:
            normalized_type = transaction_type.strip().lower()

            if normalized_type not in ("income", "expense"):
                raise ValueError(
                    "Transaction type must be income or expense."
                )

            query += " AND t.kind = %s"
            params.append(normalized_type)

        if start_date:
            query += " AND t.transaction_date >= %s"
            params.append(start_date)

        if end_date:
            query += " AND t.transaction_date <= %s"
            params.append(end_date)

        if month is not None:
            if not 1 <= int(month) <= 12:
                raise ValueError("Month must be between 1 and 12.")

            query += " AND MONTH(t.transaction_date) = %s"
            params.append(int(month))

        if year is not None:
            if not 2000 <= int(year) <= 2100:
                raise ValueError("Year must be between 2000 and 2100.")

            query += " AND YEAR(t.transaction_date) = %s"
            params.append(int(year))

        query += " ORDER BY t.transaction_date ASC, t.id ASC"

        rows = execute_query(
            query,
            tuple(params),
            fetch_all=True
        )

        columns = [
            "transaction_id",
            "transaction_date",
            "transaction_type",
            "category_id",
            "category_name",
            "amount",
            "description"
        ]

        if not rows:
            return pd.DataFrame(columns=columns)

        df = pd.DataFrame(rows, columns=columns)

        df["amount"] = pd.to_numeric(
            df["amount"],
            errors="coerce"
        ).fillna(0.0)

        df["transaction_date"] = pd.to_datetime(
            df["transaction_date"],
            errors="coerce"
        )

        return df

    # ============================================================
    # 2. BUDGET DATAFRAME
    # ============================================================

    @staticmethod
    def get_budgets_dataframe(
        month: Optional[int] = None,
        year: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Retrieve budgets and calculated spending from BudgetService.
        Convert the returned records into a Pandas DataFrame.
        """

        budgets_data = BudgetService.get_budgets(
            month=month,
            year=year
        )

        columns = [
            "budget_id",
            "category_id",
            "category_name",
            "month",
            "year",
            "budget_amount",
            "amount_spent",
            "remaining_budget",
            "budget_utilization_pct",
            "is_over_budget",
            "overrun_amount"
        ]

        if not budgets_data:
            return pd.DataFrame(columns=columns)

        df = pd.DataFrame(budgets_data)

        numeric_columns = [
            "budget_amount",
            "amount_spent",
            "remaining_budget",
            "budget_utilization_pct",
            "overrun_amount"
        ]

        for column in numeric_columns:
            if column in df.columns:
                df[column] = pd.to_numeric(
                    df[column],
                    errors="coerce"
                ).fillna(0.0)

        return df

    # ============================================================
    # 3. MATPLOTLIB OUTPUT HELPER
    # ============================================================

    @staticmethod
    def _fig_to_outputs(
        fig: plt.Figure
    ) -> Tuple[bytes, str]:
        """
        Convert a Matplotlib figure into:
        1. PNG image bytes.
        2. Base64 encoded image data URL.
        """

        buffer = io.BytesIO()

        try:
            fig.tight_layout()

            fig.savefig(
                buffer,
                format="png",
                dpi=130,
                bbox_inches="tight"
            )

            buffer.seek(0)

            image_bytes = buffer.getvalue()

            base64_string = (
                "data:image/png;base64,"
                + base64.b64encode(image_bytes).decode("utf-8")
            )

            return image_bytes, base64_string

        finally:
            plt.close(fig)
            buffer.close()

    @staticmethod
    def _create_empty_chart(
        title: str,
        message: str = "No data recorded for this period"
    ) -> Tuple[bytes, str]:
        """Generate a placeholder chart when no data is available."""

        fig, ax = plt.subplots(figsize=(7, 4.5))

        ax.text(
            0.5,
            0.5,
            message,
            horizontalalignment="center",
            verticalalignment="center",
            fontsize=14,
            color="#6b7280",
            transform=ax.transAxes
        )

        ax.set_title(
            title,
            fontsize=14,
            fontweight="bold",
            pad=15
        )

        ax.set_axis_off()

        return AnalysisAdapter._fig_to_outputs(fig)

    # ============================================================
    # 4. CATEGORY-WISE EXPENSE DISTRIBUTION
    # ============================================================

    @staticmethod
    def generate_expense_distribution_chart(
        month: Optional[int] = None,
        year: Optional[int] = None
    ) -> Tuple[bytes, str]:
        """
        Generate a donut chart showing category-wise expenses.
        """

        df = AnalysisAdapter.get_transactions_dataframe(
            month=month,
            year=year,
            transaction_type="expense"
        )

        title_suffix = (
            f" ({month:02d}/{year})"
            if month and year
            else (f" ({year})" if year else " (All Time)")
        )

        chart_title = (
            f"Category-Wise Expense Distribution{title_suffix}"
        )

        if df.empty or df["amount"].sum() <= 0:
            return AnalysisAdapter._create_empty_chart(
                chart_title,
                "No expense transactions recorded."
            )

        category_df = (
            df.groupby("category_name")["amount"]
            .sum()
            .reset_index()
            .sort_values(by="amount", ascending=False)
        )

        labels = category_df["category_name"].tolist()
        amounts = category_df["amount"].to_numpy()

        fig, ax = plt.subplots(figsize=(8, 5.5))

        colors = plt.cm.tab20(
            np.linspace(0, 1, len(labels))
        )

        wedges, texts, autotexts = ax.pie(
            amounts,
            labels=labels,
            autopct="%1.1f%%",
            startangle=140,
            colors=colors,
            wedgeprops={
                "width": 0.45,
                "edgecolor": "white",
                "linewidth": 2
            },
            pctdistance=0.75
        )

        for autotext in autotexts:
            autotext.set_fontsize(9)
            autotext.set_fontweight("bold")
            autotext.set_color("#1f2937")

        ax.set_title(
            chart_title,
            fontsize=14,
            fontweight="bold",
            pad=20
        )

        return AnalysisAdapter._fig_to_outputs(fig)

    # ============================================================
    # 5. MONTHLY INCOME VS EXPENSES
    # ============================================================

    @staticmethod
    def generate_monthly_income_vs_expense_chart(
        year: Optional[int] = None
    ) -> Tuple[bytes, str]:
        """
        Generate a grouped bar chart comparing monthly income
        and expenses.
        """

        from datetime import date

        target_year = year or date.today().year

        monthly_data = AnalyticsService.get_monthly_breakdown(
            year=target_year
        )

        chart_title = (
            f"Monthly Income vs. Expenses ({target_year})"
        )

        df = pd.DataFrame(monthly_data)

        if (
            df.empty
            or (
                df["income"].sum() == 0
                and df["expense"].sum() == 0
            )
        ):
            return AnalysisAdapter._create_empty_chart(
                chart_title,
                f"No transactions recorded for {target_year}."
            )

        short_months = [
            item["month_name"][:3]
            for item in monthly_data
        ]

        incomes = df["income"].to_numpy()
        expenses = df["expense"].to_numpy()

        x = np.arange(len(short_months))
        width = 0.38

        fig, ax = plt.subplots(figsize=(10, 5))

        ax.bar(
            x - width / 2,
            incomes,
            width,
            label="Income",
            color="#10B981"
        )

        ax.bar(
            x + width / 2,
            expenses,
            width,
            label="Expenses",
            color="#EF4444"
        )

        ax.set_title(
            chart_title,
            fontsize=14,
            fontweight="bold",
            pad=15
        )

        ax.set_xlabel(
            "Month",
            fontsize=11,
            fontweight="semibold"
        )

        ax.set_ylabel(
            "Amount (₹)",
            fontsize=11,
            fontweight="semibold"
        )

        ax.set_xticks(x)
        ax.set_xticklabels(short_months)

        ax.legend(loc="upper right", frameon=True)
        ax.grid(axis="y", linestyle="--", alpha=0.5)

        return AnalysisAdapter._fig_to_outputs(fig)

    # ============================================================
    # 6. MONTHLY EXPENSE TREND
    # ============================================================

    @staticmethod
    def generate_monthly_expense_trend_chart(
        year: Optional[int] = None
    ) -> Tuple[bytes, str]:
        """
        Generate a line chart showing monthly expense trends.
        Also displays the average monthly expense.
        """

        from datetime import date

        target_year = year or date.today().year

        monthly_data = AnalyticsService.get_monthly_breakdown(
            year=target_year
        )

        chart_title = (
            f"Monthly Expense Trend ({target_year})"
        )

        df = pd.DataFrame(monthly_data)

        if df.empty or df["expense"].sum() == 0:
            return AnalysisAdapter._create_empty_chart(
                chart_title,
                f"No expenses recorded for {target_year}."
            )

        short_months = [
            item["month_name"][:3]
            for item in monthly_data
        ]

        expenses = df["expense"].to_numpy()

        fig, ax = plt.subplots(figsize=(9, 4.8))

        ax.plot(
            short_months,
            expenses,
            marker="o",
            linewidth=2.5,
            color="#F59E0B",
            label="Monthly Expense"
        )

        ax.fill_between(
            short_months,
            expenses,
            color="#FEF3C7",
            alpha=0.5
        )

        # Calculate average expense using NumPy.
        positive_expenses = expenses[expenses > 0]

        average_expense = (
            np.mean(positive_expenses)
            if len(positive_expenses) > 0
            else 0.0
        )

        if average_expense > 0:
            ax.axhline(
                average_expense,
                color="#DC2626",
                linestyle=":",
                linewidth=1.8,
                label=f"Average (₹{average_expense:,.0f})"
            )

        ax.set_title(
            chart_title,
            fontsize=14,
            fontweight="bold",
            pad=15
        )

        ax.set_xlabel(
            "Month",
            fontsize=11,
            fontweight="semibold"
        )

        ax.set_ylabel(
            "Expense Amount (₹)",
            fontsize=11,
            fontweight="semibold"
        )

        ax.legend(loc="upper left")
        ax.grid(True, linestyle="--", alpha=0.5)

        return AnalysisAdapter._fig_to_outputs(fig)

    # ============================================================
    # 7. BUDGET UTILIZATION
    # ============================================================

    @staticmethod
    def generate_budget_utilization_chart(
        month: Optional[int] = None,
        year: Optional[int] = None
    ) -> Tuple[bytes, str]:
        """
        Generate a horizontal bar chart comparing allocated
        budget with actual spending for each category.
        """

        df = AnalysisAdapter.get_budgets_dataframe(
            month=month,
            year=year
        )

        title_suffix = (
            f" ({month:02d}/{year})"
            if month and year
            else (f" ({year})" if year else "")
        )

        chart_title = (
            f"Budget vs. Actual Spending{title_suffix}"
        )

        if df.empty:
            return AnalysisAdapter._create_empty_chart(
                chart_title,
                "No budgets allocated for this period."
            )

        df = df.sort_values(
            by="budget_amount",
            ascending=True
        )

        categories = df["category_name"].tolist()
        budgets = df["budget_amount"].to_numpy()
        spent = df["amount_spent"].to_numpy()

        y = np.arange(len(categories))
        height = 0.35

        fig, ax = plt.subplots(
            figsize=(9, max(4.5, len(categories) * 0.7))
        )

        ax.barh(
            y + height / 2,
            budgets,
            height,
            label="Allocated Budget",
            color="#3B82F6"
        )

        # Red indicates over-budget spending.
        # Green indicates spending within budget.
        spent_colors = [
            "#EF4444" if actual > budget else "#10B981"
            for actual, budget in zip(spent, budgets)
        ]

        ax.barh(
            y - height / 2,
            spent,
            height,
            label="Actual Spent",
            color=spent_colors
        )

        ax.set_title(
            chart_title,
            fontsize=14,
            fontweight="bold",
            pad=15
        )

        ax.set_xlabel(
            "Amount (₹)",
            fontsize=11,
            fontweight="semibold"
        )

        ax.set_yticks(y)
        ax.set_yticklabels(categories)

        ax.legend(loc="lower right")
        ax.grid(axis="x", linestyle="--", alpha=0.5)

        return AnalysisAdapter._fig_to_outputs(fig)
