import logging
import os
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any, Optional

from fastapi import Body, Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

import auth
import db

app = FastAPI(
    title="WealthWatch API",
    docs_url="/api/docs",
    redoc_url=None,
    openapi_url="/api/openapi.json",
)

MAX_AMOUNT = Decimal("99999999.99")  # transactions.amount is NUMERIC(10,2)
TRANSACTION_TYPES = ("income", "expense")
DEFAULT_LIMIT = 50
MAX_LIMIT = 500


class ApiError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


@app.exception_handler(ApiError)
def api_error(request, exc):
    return JSONResponse({"error": exc.message}, exc.status_code)


@app.exception_handler(HTTPException)
def http_error(request, exc):
    return JSONResponse({"error": exc.detail}, exc.status_code)


@app.exception_handler(RequestValidationError)
def invalid_request(request, exc):
    return JSONResponse({"error": "Request body must be valid JSON"}, 400)


@app.exception_handler(Exception)
def unhandled_error(request, exc):
    logging.exception("Unhandled error in %s %s", request.method, request.url.path)
    return JSONResponse({"error": "Internal server error"}, 500)


def get_user_email(request: Request):
    """Identify the caller from their Supabase access token.

    DEV_USER_EMAIL is a local-development fallback for requests that carry no
    token. It is ignored on Vercel so it can never open up a deployment.
    """
    scheme, _, token = (request.headers.get("authorization") or "").partition(" ")
    if scheme.lower() == "bearer" and token.strip():
        try:
            return auth.email_from_token(token.strip())
        except auth.AuthError as e:
            logging.info("Rejected access token: %s", e)
            raise ApiError("Sign in required", 401)

    email = None if os.environ.get("VERCEL") else os.environ.get("DEV_USER_EMAIL")
    if not email:
        raise ApiError("Sign in required", 401)
    return email


def get_database():
    with db.connect() as database:
        yield database


def get_user_id(email: str = Depends(get_user_email), database=Depends(get_database)):
    return db.get_or_create_user(database, email)


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


def parse_period(year, month, required):
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


@app.get("/api/health")
def health(database=Depends(get_database)):
    # Reads a real table: Supabase counts table queries as activity, so the
    # keepalive workflow's calls stop the free project from pausing.
    database.execute("SELECT 1 FROM users LIMIT 1").fetchone()
    return {"status": "ok"}


@app.post("/api/addtransaction", status_code=201)
def add_transaction(
    body: Any = Body(default=None),
    user_id: int = Depends(get_user_id),
    database=Depends(get_database),
):
    transaction = parse_transaction(body)
    transaction_id = database.insert(
        "transactions", "transaction_id", {"user_id": user_id, **transaction}
    )
    database.commit()
    return {"transaction_id": transaction_id, "message": "Transaction added"}


@app.get("/api/gettransactions")
def get_transactions(
    year: Optional[str] = None,
    month: Optional[str] = None,
    limit: Optional[str] = None,
    user_id: int = Depends(get_user_id),
    database=Depends(get_database),
):
    columns = "transaction_id, amount, type, category, description, transaction_date"
    order = "ORDER BY transaction_date DESC, transaction_id DESC"
    period = parse_period(year, month, required=False)

    if period:
        start, end = month_range(*period)
        cursor = database.execute(
            f"SELECT {columns} FROM transactions "
            f"WHERE user_id = %s AND transaction_date >= %s AND transaction_date < %s {order}",
            (user_id, start, end),
        )
    else:
        row_limit = parse_int(DEFAULT_LIMIT if limit is None else limit, "limit", 1, MAX_LIMIT)
        cursor = database.execute(
            f"SELECT {columns} FROM transactions WHERE user_id = %s {order} LIMIT %s",
            (user_id, row_limit),
        )

    return [
        {
            "id": row[0],
            "amount": float(row[1]),
            "type": row[2],
            "category": row[3],
            "description": row[4] or "",
            "date": str(row[5])[:10],
        }
        for row in cursor.fetchall()
    ]


@app.get("/api/getsummary")
def get_summary(
    year: Optional[str] = None,
    month: Optional[str] = None,
    user_id: int = Depends(get_user_id),
    database=Depends(get_database),
):
    year, month = parse_period(year, month, required=True)
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

    return {
        "year": year,
        "month": month,
        "total_income": round(income, 2),
        "total_expense": round(expense, 2),
        "net_savings": round(income - expense, 2),
        "categories": [
            {"category": row[0], "total": round(float(row[1]), 2)} for row in categories
        ],
    }


@app.delete("/api/deletetransaction/{id}")
def delete_transaction(
    id: str,
    user_id: int = Depends(get_user_id),
    database=Depends(get_database),
):
    transaction_id = parse_int(id, "id", 1, 2**31 - 1)
    cursor = database.execute(
        "DELETE FROM transactions WHERE transaction_id = %s AND user_id = %s",
        (transaction_id, user_id),
    )
    deleted = cursor.rowcount
    database.commit()
    if not deleted:
        raise ApiError("Transaction not found", 404)
    return {"message": "Transaction deleted"}
