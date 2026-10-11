"""
AWS Lambda Handler for Jal-Saathi Decision Engine (/backend/decide).
"""

from __future__ import annotations
import json
import logging
from typing import Any, Dict
from pydantic import ValidationError
from .engine import decide

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def handler(event: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    """
    AWS Lambda entrypoint. Accepts API Gateway proxy event or direct dictionary payload.
    """
    try:
        # Extract payload from API Gateway proxy or direct invocation
        body = event.get("body", event)
        if isinstance(body, str):
            payload = json.loads(body)
        elif isinstance(body, dict):
            payload = body
        else:
            payload = {}

        # Execute decision pipeline
        response_dict = decide(payload)

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(response_dict),
        }

    except ValidationError as ve:
        logger.warning(f"Payload validation error: {ve}")
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "invalid_request_payload", "details": ve.errors()}),
        }
    except Exception as e:
        logger.error(f"Internal error processing decision: {e}", exc_info=True)
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "decision_engine_error", "message": str(e)}),
        }
