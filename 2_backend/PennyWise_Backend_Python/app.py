"""
PennyWise Backend Application Entry Point.
Home Budget Management and Expense Analysis System.

Strict Tech Stack:
- Python 3.x
- Flask Framework with CORS
- MySQL with mysql-connector-python
- Pandas & NumPy for numerical calculations and analytics
- Matplotlib for server-side chart generation
"""

import logging
from datetime import datetime, timezone

from flask import Flask, jsonify, request
from flask_cors import CORS

from config import Config
import database

from routes import (
    category_bp,
    transaction_bp,
    budget_bp,
    analytics_bp
)

from utils.response import success_response, error_response


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logger = logging.getLogger("pennywise")


def create_app(config_class=Config) -> Flask:
    """
    Application factory for PennyWise Flask Backend.
    """

    app = Flask(__name__)

    # Load application configuration
    app.config.from_object(config_class)

    # Enable CORS for frontend integration
    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": app.config.get("CORS_ORIGINS", "*")
            }
        },
        supports_credentials=True
    )

    # Initialize MySQL connection pool
    if not app.config.get("TESTING", False):

        pool = database.init_connection_pool(
            pool_size=app.config.get(
                "MYSQL_POOL_SIZE",
                Config.MYSQL_POOL_SIZE
            )
        )

        if pool is None:
            logger.warning(
                "MySQL connection pool could not be initialized. "
                "Check MySQL service and configuration."
            )

    # Register API Blueprints
    app.register_blueprint(category_bp)
    app.register_blueprint(transaction_bp)
    app.register_blueprint(budget_bp)
    app.register_blueprint(analytics_bp)

    # System Health Check Endpoint
    @app.route("/api/health", methods=["GET"])
    def health_check():
        """
        GET /api/health

        Checks service status and database connectivity.
        """

        db_healthy, db_message = database.test_connection()

        status_code = 200 if db_healthy else 503

        health_data = {
            "service": "PennyWise Backend API",

            "status": (
                "healthy" if db_healthy else "degraded"
            ),

            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),

            "database": {
                "type": "MySQL",
                "connected": db_healthy,
                "message": db_message
            },

            "modules": {
                "transactions": "active",
                "categories": "active",
                "budgets": "active",
                "analytics": "active",
                "charts": "active"
            }
        }

        return jsonify(health_data), status_code

    # Root route
    @app.route("/", methods=["GET"])
    def root():
        """
        Root endpoint for API verification.
        """

        return jsonify({
            "message": (
                "Welcome to PennyWise API - "
                "Home Budget Management and Expense Analysis System"
            ),
            "documentation": "/docs/API_DOCUMENTATION.md",
            "health_check": "/api/health"
        }), 200

    # Global Error Handlers

    @app.errorhandler(400)
    def bad_request(error):
        return error_response(
            "Bad request: The request could not be understood by the server.",
            status_code=400
        )

    @app.errorhandler(404)
    def not_found(error):
        return error_response(
            "The requested resource or endpoint was not found.",
            status_code=404
        )

    @app.errorhandler(405)
    def method_not_allowed(error):
        return error_response(
            f"HTTP method '{request.method}' is not allowed on this endpoint.",
            status_code=405
        )

    @app.errorhandler(database.DatabaseError)
    def handle_database_error(error):

        logger.error(
            "A database error was handled by the application."
        )

        return error_response(
            str(error),
            status_code=500
        )

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):

        logger.error(
            "Unhandled application exception.",
            exc_info=True
        )

        return error_response(
            "An internal server error occurred. Please try again later.",
            status_code=500
        )

    return app


# Application instance for WSGI servers and direct execution
app = create_app()


if __name__ == "__main__":

    logger.info(
        "Starting PennyWise Backend on %s:%s (Debug: %s)",
        Config.HOST,
        Config.PORT,
        Config.DEBUG
    )

    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )