import os
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

class Config:
    """Base configuration loaded from environment variables."""
    SECRET_KEY = os.getenv("SECRET_KEY", "pennywise-dev-secret-key-change-in-production")
    DEBUG = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")
    PORT = int(os.getenv("PORT", 5000))
    HOST = os.getenv("HOST", "0.0.0.0")

    # MySQL Database Configuration
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "pennywise_db")
    MYSQL_POOL_SIZE = int(os.getenv("MYSQL_POOL_SIZE", 5))

    # CORS Settings
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

    # Chart Generation Settings
    CHARTS_DIR = os.getenv("CHARTS_DIR", os.path.join(os.path.dirname(__file__), "charts"))


class TestingConfig(Config):
    """Configuration for running automated unit/integration tests."""
    TESTING = True
    DEBUG = False
    MYSQL_DATABASE = os.getenv("TEST_MYSQL_DATABASE", "pennywise_test_db")
