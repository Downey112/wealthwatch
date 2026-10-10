import azure.functions as func
import base64
import json
import logging
import os
from datetime import date
from decimal import Decimal, InvalidOperation

import db

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

MAX_AMOUNT = Decimal("99999999.99")  # transactions.amount is DECIMAL(10,2)
TRANSACTION_TYPES = ("income", "expense")
DEFAULT_LIMIT = 50
MAX_LIMIT = 500


class ApiError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def json_response(body, status_code=200):
    return func.HttpResponse(
        json.dumps(body), status_code=status_code, mimetype="application/json"
    )


def get_user_email(req):
    """Identify the caller from the headers Azure Static Web Apps injects.

    These headers are only trustworthy when the Function App is reachable
    solely through Static Web Apps (a linked backend). DEV_USER_EMAIL is a
    local-development fallback and must not be set in production.
    """
    principal = req.headers.get("x-ms-client-principal")
    if principal:
        try:
            details = json.loads(base64.b64decode(principal)).get("userDetails")
        except (ValueError, AttributeError):
            details = None
        if details:
            return details

    email = req.headers.get("x-ms-client-principal-name") or os.environ.get("DEV_USER_EMAIL")
    if not email:
        raise ApiError("Sign in required", 401)
    return email


def run(req, handler):
    """Open a connection, resolve the user, and turn failures into JSON errors."""
    try:
        email = get_user_email(req)
        with db.connect() as database:
            user_id = db.get_or_create_user(database, email)
            return handler(req, database, user_id)
    except ApiError as e:
        return json_response({"error": e.message}, e.status_code)
    except Exception:
        logging.exception("Unhandled error in %s", handler.__name__)
        return json_response({"error": "Internal server error"}, 500)


def parse_int(value, name, minimum, maximum):
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ApiError(f"{name} must be a whole number")
    if not minimum <= number <= maximum:
        raise ApiError(f"{name} must be between {minimum} and {maximum}")
    return number


def month_range(year, month):
    """First day of the month and first day of the next, as ISO strings."""
    start = date(year, month, 1)
    end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    return start.isoformat(), end.isoformat()


def parse_period(req, required):
    year = req.params.get("year")
    month = req.params.get("month")
    if not year and not month and not required:
        return None
    today = date.today()
    return (
        parse_int(year or today.year, "year", 1900, 9999),
        parse_int(month or today.month, "month", 1, 12),
    )


def parse_transaction(body):
    if not isinstance(body, dict):
        raise ApiError("Request body must be a JSON object")

    try:
        amount = Decimal(str(body.get("amount"))).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        raise ApiError("amount must be a number")
    if not amount.is_finite() or amount <= 0 or amount > MAX_AMOUNT:
        raise ApiError(f"amount must be greater than 0 and at most {MAX_AMOUNT}")

    tx_type = body.get("type")
    if tx_type not in TRANSACTION_TYPES:
        raise ApiError("type must be 'income' or 'expense'")

    category = str(body.get("category") or "").strip()
    if not category or len(category) > 50:
        raise ApiError("category is required and must be at most 50 characters")

    description = str(body.get("description") or "").strip()
    if len(description) > 255:
        raise ApiError("description must be at most 255 characters")

    try:
        transaction_date = date.fromisoformat(str(body.get("transaction_date")))
    except ValueError:
        raise ApiError("transaction_date must be a date in YYYY-MM-DD format")

    return {
        "amount": amount,
        "type": tx_type,
        "category": category,
        "description": description,
        "transaction_date": transaction_date.isoformat(),
    }


def add_transaction_handler(req, database, user_id):
    try:
        body = req.get_json()
    except ValueError:
        raise ApiError("Request body must be valid JSON")

    transaction = parse_transaction(body)
    transaction_id = database.insert(
        "transactions", "transaction_id", {"user_id": user_id, **transaction}
    )
    database.commit()
    return json_response({"transaction_id": transaction_id, "message": "Transaction added"}, 201)


def get_transactions_handler(req, database, user_id):
    columns = "transaction_id, amount, type, category, description, transaction_date"
    order = "ORDER BY transaction_date DESC, transaction_id DESC"
    period = parse_period(req, required=False)

    if period:
        start, end = month_range(*period)
        cursor = database.execute(
            f"SELECT {columns} FROM transactions "
            f"WHERE user_id = %s AND transaction_date >= %s AND transaction_date < %s {order}",
            (user_id, start, end),
        )
    else:
        limit = parse_int(req.params.get("limit", DEFAULT_LIMIT), "limit", 1, MAX_LIMIT)
        cursor = database.execute(
            f"SELECT {columns} FROM transactions WHERE user_id = %s {order} "
            f"{database.limit_clause}",
            (user_id, limit),
        )

    return json_response([
        {
            "id": row[0],
            "amount": float(row[1]),
            "type": row[2],
            "category": row[3],
            "description": row[4] or "",
            "date": str(row[5])[:10],
        }
        for row in cursor.fetchall()
    ])


def get_summary_handler(req, database, user_id):
    year, month = parse_period(req, required=True)
    start, end = month_range(year, month)
    in_month = "user_id = %s AND transaction_date >= %s AND transaction_date < %s"

    totals = database.execute(
        f"""
        SELECT
            SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END),
            SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END)
        FROM transactions
        WHERE {in_month}
        """,
        (user_id, start, end),
    ).fetchone()
    income = float(totals[0] or 0)
    expense = float(totals[1] or 0)

    categories = database.execute(
        f"""
        SELECT category, SUM(amount) AS total
        FROM transactions
        WHERE {in_month} AND type = 'expense'
        GROUP BY category
        ORDER BY total DESC
        """,
        (user_id, start, end),
    ).fetchall()

    return json_response({
        "year": year,
        "month": month,
        "total_income": round(income, 2),
        "total_expense": round(expense, 2),
        "net_savings": round(income - expense, 2),
        "categories": [
            {"category": row[0], "total": round(float(row[1]), 2)} for row in categories
        ],
    })


def delete_transaction_handler(req, database, user_id):
    transaction_id = parse_int(req.route_params.get("id"), "id", 1, 2**31 - 1)
    cursor = database.execute(
        "DELETE FROM transactions WHERE transaction_id = %s AND user_id = %s",
        (transaction_id, user_id),
    )
    deleted = cursor.rowcount
    database.commit()
    if not deleted:
        raise ApiError("Transaction not found", 404)
    return json_response({"message": "Transaction deleted"})


@app.route(route="addtransaction", methods=["POST"])
def add_transaction(req: func.HttpRequest) -> func.HttpResponse:
    return run(req, add_transaction_handler)


@app.route(route="gettransactions", methods=["GET"])
def get_transactions(req: func.HttpRequest) -> func.HttpResponse:
    return run(req, get_transactions_handler)


@app.route(route="getsummary", methods=["GET"])
def get_summary(req: func.HttpRequest) -> func.HttpResponse:
    return run(req, get_summary_handler)


@app.route(route="deletetransaction/{id}", methods=["DELETE"])
def delete_transaction(req: func.HttpRequest) -> func.HttpResponse:
    return run(req, delete_transaction_handler)
