
"""
Analytics & Chart Routes Blueprint for PennyWise Backend.

Provides structured data for the data-analysis module
and exposes Matplotlib chart endpoints.
"""

import logging

from flask import Blueprint, Response, request

from services.analytics_service import AnalyticsService
from integrations.analysis_adapter import AnalysisAdapter
from utils.response import success_response, error_response
from database import DatabaseError


logger = logging.getLogger(__name__)

analytics_bp = Blueprint(
    "analytics_bp",
    __name__,
    url_prefix="/api/analytics"
)


def get_optional_integer(value, field_name):
    """Convert an optional query parameter into an integer."""

    if value is None:
        return None

    try:
        return int(value)
    except (ValueError, TypeError):
        raise ValueError(f"{field_name} must be an integer.")


def get_period_parameters():
    """Read and validate month and year query parameters."""

    month = get_optional_integer(
        request.args.get("month"),
        "Month"
    )

    year = get_optional_integer(
        request.args.get("year"),
        "Year"
    )

    return AnalyticsService._validate_period(month, year)


def get_year_parameter():
    """Read and validate an optional year parameter."""

    year = get_optional_integer(
        request.args.get("year"),
        "Year"
    )

    _, year = AnalyticsService._validate_period(year=year)

    return year


# ============================================================
# 1. STRUCTURED DATA ENDPOINTS
# ============================================================

@analytics_bp.route("/summary", methods=["GET"])
def get_summary():
    """
    GET /api/analytics/summary

    Query Parameters:
    - month (optional, 1-12)
    - year (optional, YYYY)
    """

    try:
        month, year = get_period_parameters()

        summary = AnalyticsService.get_financial_summary(
            month=month,
            year=year
        )

        return success_response(
            data=summary,
            message="Financial summary retrieved successfully"
        )

    except ValueError as ve:
        return error_response(str(ve), status_code=400)

    except DatabaseError as de:
        logger.exception("Database error while retrieving financial summary.")
        return error_response(str(de), status_code=500)

    except Exception:
        logger.exception("Financial summary calculation failed.")
        return error_response(
            "An unexpected error occurred while calculating financial summary.",
            status_code=500
        )


@analytics_bp.route("/monthly", methods=["GET"])
def get_monthly_breakdown():
    """
    GET /api/analytics/monthly

    Query Parameters:
    - year (optional, YYYY)
    """

    try:
        year = get_year_parameter()

        monthly_data = AnalyticsService.get_monthly_breakdown(
            year=year
        )

        return success_response(
            data=monthly_data,
            message="Monthly breakdown retrieved successfully"
        )

    except ValueError as ve:
        return error_response(str(ve), status_code=400)

    except DatabaseError as de:
        logger.exception("Database error while retrieving monthly breakdown.")
        return error_response(str(de), status_code=500)

    except Exception:
        logger.exception("Monthly breakdown retrieval failed.")
        return error_response(
            "An unexpected error occurred while retrieving monthly breakdown.",
            status_code=500
        )


@analytics_bp.route("/categories", methods=["GET"])
def get_category_analytics():
    """
    GET /api/analytics/categories

    Query Parameters:
    - month (optional, 1-12)
    - year (optional, YYYY)
    - type (optional, Income or Expense)
    """

    try:
        month, year = get_period_parameters()

        category_type = request.args.get(
            "type",
            "Expense"
        )

        categories_data = AnalyticsService.get_category_distribution(
            month=month,
            year=year,
            transaction_type=category_type
        )

        return success_response(
            data=categories_data,
            message=(
                f"{category_type} category distribution "
                "retrieved successfully"
            )
        )

    except ValueError as ve:
        return error_response(str(ve), status_code=400)

    except DatabaseError as de:
        logger.exception("Database error while retrieving category analytics.")
        return error_response(str(de), status_code=500)

    except Exception:
        logger.exception("Category analytics calculation failed.")
        return error_response(
            "An unexpected error occurred while calculating category distribution.",
            status_code=500
        )


@analytics_bp.route("/budget-status", methods=["GET"])
def get_budget_status():
    """
    GET /api/analytics/budget-status

    Query Parameters:
    - month (optional, 1-12)
    - year (optional, YYYY)
    """

    try:
        month, year = get_period_parameters()

        status_data = AnalyticsService.get_budget_status(
            month=month,
            year=year
        )

        return success_response(
            data=status_data,
            message="Budget status analysis retrieved successfully"
        )

    except ValueError as ve:
        return error_response(str(ve), status_code=400)

    except DatabaseError as de:
        logger.exception("Database error while retrieving budget status.")
        return error_response(str(de), status_code=500)

    except Exception:
        logger.exception("Budget status retrieval failed.")
        return error_response(
            "An unexpected error occurred while retrieving budget status.",
            status_code=500
        )


# ============================================================
# 2. CHART HELPER
# ============================================================

def _serve_chart(
    img_bytes: bytes,
    b64_str: str,
    chart_name: str
):
    """
    Serve a chart as either a PNG image or base64 JSON response.
    """

    output_format = request.args.get(
        "format",
        ""
    ).lower()

    accept_header = request.headers.get(
        "Accept",
        ""
    ).lower()

    if (
        output_format == "png"
        or "image/png" in accept_header
        or "image/*" in accept_header
    ):
        return Response(
            img_bytes,
            mimetype="image/png"
        )

    return success_response(
        data={
            "chart_name": chart_name,
            "format": "base64",
            "image": b64_str
        },
        message=f"{chart_name} chart generated successfully"
    )


# ============================================================
# 3. MATPLOTLIB CHART ENDPOINTS
# ============================================================

@analytics_bp.route(
    "/charts/expense-distribution",
    methods=["GET"]
)
def chart_expense_distribution():
    """
    GET /api/analytics/charts/expense-distribution

    Generates a category-wise expense distribution chart.
    """

    try:
        month, year = get_period_parameters()

        img_bytes, b64_str = (
            AnalysisAdapter.generate_expense_distribution_chart(
                month=month,
                year=year
            )
        )

        return _serve_chart(
            img_bytes,
            b64_str,
            "Category-Wise Expense Distribution"
        )

    except ValueError as ve:
        return error_response(str(ve), status_code=400)

    except Exception:
        logger.exception("Expense distribution chart generation failed.")
        return error_response(
            "Failed to generate expense distribution chart.",
            status_code=500
        )


@analytics_bp.route(
    "/charts/monthly-comparison",
    methods=["GET"]
)
def chart_monthly_comparison():
    """
    GET /api/analytics/charts/monthly-comparison

    Generates a monthly income vs. expense comparison chart.
    """

    try:
        year = get_year_parameter()

        img_bytes, b64_str = (
            AnalysisAdapter.generate_monthly_income_vs_expense_chart(
                year=year
            )
        )

        return _serve_chart(
            img_bytes,
            b64_str,
            "Monthly Income vs. Expenses"
        )

    except ValueError as ve:
        return error_response(str(ve), status_code=400)

    except Exception:
        logger.exception("Monthly comparison chart generation failed.")
        return error_response(
            "Failed to generate monthly comparison chart.",
            status_code=500
        )


@analytics_bp.route(
    "/charts/expense-trend",
    methods=["GET"]
)
def chart_expense_trend():
    """
    GET /api/analytics/charts/expense-trend

    Generates a monthly expense trend chart.
    """

    try:
        year = get_year_parameter()

        img_bytes, b64_str = (
            AnalysisAdapter.generate_monthly_expense_trend_chart(
                year=year
            )
        )

        return _serve_chart(
            img_bytes,
            b64_str,
            "Monthly Expense Trend"
        )

    except ValueError as ve:
        return error_response(str(ve), status_code=400)

    except Exception:
        logger.exception("Expense trend chart generation failed.")
        return error_response(
            "Failed to generate monthly expense trend chart.",
            status_code=500
        )


@analytics_bp.route(
    "/charts/budget-utilization",
    methods=["GET"]
)
def chart_budget_utilization():
    """
    GET /api/analytics/charts/budget-utilization

    Generates a budget vs. actual spending chart.
    """

    try:
        month, year = get_period_parameters()

        img_bytes, b64_str = (
            AnalysisAdapter.generate_budget_utilization_chart(
                month=month,
                year=year
            )
        )

        return _serve_chart(
            img_bytes,
            b64_str,
            "Budget Utilization"
        )

    except ValueError as ve:
        return error_response(str(ve), status_code=400)

    except Exception:
        logger.exception("Budget utilization chart generation failed.")
        return error_response(
            "Failed to generate budget utilization chart.",
            status_code=500
        )
