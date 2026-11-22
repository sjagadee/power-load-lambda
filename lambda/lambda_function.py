"""
Serverless CRUD microservice handler.

API Gateway (REST, POST) -> this Lambda -> Amazon DynamoDB

Request body shape:
{
    "operation": "create" | "read" | "update" | "delete" | "list" | "echo" | "ping",
    "tableName": "lambda-apigateway",
    "payload":   { ...arguments passed straight to the boto3 Table call... }
}
"""

import json
import logging
from decimal import Decimal

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Created once per execution environment and reused across warm invocations.
dynamodb = boto3.resource("dynamodb")


def _to_json(obj):
    """DynamoDB returns numbers as Decimal; make them JSON serialisable."""
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    raise TypeError(f"Type {type(obj)} is not JSON serialisable")


def _parse_event(event):
    """Support both direct invocation and API Gateway proxy integration."""
    if isinstance(event, dict) and "body" in event and isinstance(event["body"], str):
        return json.loads(event["body"])
    return event


def lambda_handler(event, context):
    request = _parse_event(event)
    operation = request.get("operation")
    payload = request.get("payload", {}) or {}
    logger.info("operation=%s table=%s", operation, request.get("tableName"))

    # Operations that do not touch DynamoDB
    if operation == "echo":
        return payload
    if operation == "ping":
        return "pong"

    table_name = request.get("tableName")
    if not table_name:
        raise ValueError("'tableName' is required for DynamoDB operations")
    table = dynamodb.Table(table_name)

    operations = {
        "create": lambda p: table.put_item(**p),
        "read": lambda p: table.get_item(**p),
        "update": lambda p: table.update_item(**p),
        "delete": lambda p: table.delete_item(**p),
        "list": lambda p: table.scan(**p),
    }

    if operation not in operations:
        raise ValueError(f"Unrecognised operation '{operation}'")

    result = operations[operation](payload)
    # Round-trip through JSON so Decimals become plain numbers for API Gateway.
    return json.loads(json.dumps(result, default=_to_json))
