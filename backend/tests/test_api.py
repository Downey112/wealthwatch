import base64
import json
import os
import sys

import azure.functions as func
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import function_app  # noqa: E402

ALICE = {"x-ms-client-principal-name": "alice@example.com"}
BOB = {"x-ms-client-principal-name": "bob@example.com"}


@pytest.fixture(autouse=True)
def sqlite_db(tmp_path, monkeypatch):
    monkeypatch.delenv("DB_SERVER", raising=False)
    monkeypatch.delenv("DEV_USER_EMAIL", raising=False)
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "test.db"))


def call(handler, method="GET", headers=ALICE, params=None, body=None, route_params=None):
    req = func.HttpRequest(
        method=method,
        url="/api/test",
        headers=headers or {},
        params=params or {},
        route_params=route_params or {},
        body=json.dumps(body).encode() if body is not None else b"",
    )
    response = function_app.run(req, handler)
    return response.status_code, json.loads(response.get_body())


def add(headers=ALICE, **overrides):
    body = {
        "amount": 12.5,
        "type": "expense",
        "category": "Food",
        "description": "Lunch",
        "transaction_date": "2026-03-15",
        **overrides,
    }
    return call(function_app.add_transaction_handler, "POST", headers, body=body)


def test_add_and_list_transaction():
    status, created = add()
    assert status == 201
    assert created["transaction_id"] > 0

    status, rows = call(
        function_app.get_transactions_handler, params={"year": "2026", "month": "3"}
    )
    assert status == 200
    assert rows == [{
        "id": created["transaction_id"],
        "amount": 12.5,
        "type": "expense",
        "category": "Food",
        "description": "Lunch",
        "date": "2026-03-15",
    }]


def test_month_filter_excludes_other_months():
    add(transaction_date="2026-02-28")
    add(transaction_date="2026-03-01")
    add(transaction_date="2026-03-31")
    add(transaction_date="2026-04-01")
    _, rows = call(function_app.get_transactions_handler, params={"year": "2026", "month": "3"})
    assert [r["date"] for r in rows] == ["2026-03-31", "2026-03-01"]


def test_december_range_rolls_over_the_year():
    add(transaction_date="2026-12-31")
    add(transaction_date="2027-01-01")
    _, rows = call(function_app.get_transactions_handler, params={"year": "2026", "month": "12"})
    assert [r["date"] for r in rows] == ["2026-12-31"]


def test_limit_applies_without_a_period():
    for day in ("01", "02", "03"):
        add(transaction_date=f"2026-03-{day}")
    _, rows = call(function_app.get_transactions_handler, params={"limit": "2"})
    assert [r["date"] for r in rows] == ["2026-03-03", "2026-03-02"]


def test_summary_totals_and_categories():
    add(amount=3000, type="income", category="Salary")
    add(amount=200.10, category="Food")
    add(amount=99.90, category="Food")
    add(amount=450, category="Housing")
    add(amount=999, transaction_date="2026-04-01")

    status, summary = call(
        function_app.get_summary_handler, params={"year": "2026", "month": "3"}
    )
    assert status == 200
    assert summary == {
        "year": 2026,
        "month": 3,
        "total_income": 3000.0,
        "total_expense": 750.0,
        "net_savings": 2250.0,
        "categories": [
            {"category": "Housing", "total": 450.0},
            {"category": "Food", "total": 300.0},
        ],
    }


def test_summary_of_empty_month_is_zero():
    _, summary = call(function_app.get_summary_handler, params={"year": "2026", "month": "1"})
    assert summary["total_income"] == 0
    assert summary["net_savings"] == 0
    assert summary["categories"] == []


def test_users_only_see_and_delete_their_own_transactions():
    _, created = add(headers=ALICE)
    tx_id = str(created["transaction_id"])

    _, bobs = call(function_app.get_transactions_handler, headers=BOB)
    assert bobs == []

    status, _ = call(
        function_app.delete_transaction_handler, "DELETE", BOB, route_params={"id": tx_id}
    )
    assert status == 404

    status, _ = call(
        function_app.delete_transaction_handler, "DELETE", ALICE, route_params={"id": tx_id}
    )
    assert status == 200
    _, rows = call(function_app.get_transactions_handler, headers=ALICE)
    assert rows == []


@pytest.mark.parametrize("overrides", [
    {"amount": 0},
    {"amount": -5},
    {"amount": "abc"},
    {"amount": "NaN"},
    {"amount": 100000000},
    {"type": "transfer"},
    {"category": ""},
    {"category": "x" * 51},
    {"description": "x" * 256},
    {"transaction_date": "15/03/2026"},
    {"transaction_date": None},
])
def test_invalid_transactions_are_rejected(overrides):
    status, body = add(**overrides)
    assert status == 400
    assert "error" in body


def test_malformed_json_body_is_rejected():
    req = func.HttpRequest(method="POST", url="/api/test", headers=ALICE, body=b"{not json")
    response = function_app.run(req, function_app.add_transaction_handler)
    assert response.status_code == 400


@pytest.mark.parametrize("params", [
    {"year": "2026", "month": "13"},
    {"year": "abc", "month": "3"},
    {"limit": "0"},
    {"limit": "many"},
])
def test_invalid_query_parameters_are_rejected(params):
    status, _ = call(function_app.get_transactions_handler, params=params)
    assert status == 400


def test_delete_requires_a_numeric_id():
    status, _ = call(
        function_app.delete_transaction_handler, "DELETE", route_params={"id": "1 OR 1=1"}
    )
    assert status == 400


def test_requests_without_identity_are_unauthorised():
    status, body = call(function_app.get_transactions_handler, headers={})
    assert status == 401
    assert body == {"error": "Sign in required"}


def test_dev_user_email_is_used_when_no_identity_header(monkeypatch):
    monkeypatch.setenv("DEV_USER_EMAIL", "dev@localhost")
    status, _ = add(headers={})
    assert status == 201
    _, rows = call(
        function_app.get_transactions_handler,
        headers={"x-ms-client-principal-name": "dev@localhost"},
    )
    assert len(rows) == 1


def test_static_web_apps_principal_header_identifies_the_user():
    principal = base64.b64encode(json.dumps({"userDetails": "alice@example.com"}).encode())
    add(headers=ALICE)
    _, rows = call(
        function_app.get_transactions_handler,
        headers={"x-ms-client-principal": principal.decode()},
    )
    assert len(rows) == 1


def test_unexpected_errors_do_not_leak_details(monkeypatch):
    def boom(req, database, user_id):
        raise RuntimeError("password=hunter2")

    status, body = call(boom)
    assert status == 500
    assert body == {"error": "Internal server error"}
