"""
API response helper utilities ensuring consistent JSON structure across all endpoints.
"""

from typing import Any, Optional, Tuple
from flask import jsonify, Response


def success_response(
    data: Optional[Any] = None,
    message: str = "Operation completed successfully",
    status_code: int = 200
) -> Tuple[Response, int]:
    """
    Generate a standardized JSON success response.
    Format:
    {
      "status": "success",
      "message": "...",
      "data": ...
    }
    """
    payload = {
        "status": "success",
        "message": message
    }
    if data is not None:
        payload["data"] = data
    return jsonify(payload), status_code


def error_response(
    message: str,
    status_code: int = 400
) -> Tuple[Response, int]:
    """
    Generate a standardized JSON error response.
    Format:
    {
      "status": "error",
      "message": "..."
    }
    """
    payload = {
        "status": "error",
        "message": message
    }
    return jsonify(payload), status_code
