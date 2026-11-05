"""
PennyWise Backend API Blueprints package.
"""

from routes.category_routes import category_bp
from routes.transaction_routes import transaction_bp
from routes.budget_routes import budget_bp
from routes.analytics_routes import analytics_bp

__all__ = ["category_bp", "transaction_bp", "budget_bp", "analytics_bp"]
