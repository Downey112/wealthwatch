import os
import sys
import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import auth  # noqa: E402
import main  # noqa: E402

JWT_SECRET = "test-secret-that-is-at-least-32-bytes-long"
SUPABASE_URL = "https://project.supabase.co"

client = TestClient(main.app, raise_server_exceptions=False)


def token(email, key=JWT_SECRET, algorithm="HS256", **overrides):
    claims = {
        "sub": "00000000-0000-0000-0000-000000000000",
        "email": email,
        "aud": "authenticated",
        "iss": f"{SUPABASE_URL}/auth/v1",
        "exp": int(time.time()) + 3600,
        **overrides,
    }
    return jwt.encode(claims, key, algorithm=algorithm)


def bearer(value):
    return {"Authorization": f"Bearer {value}"}


ALICE = bearer(token("alice@example.com"))
BOB = bearer(token("bob@example.com"))


@pytest.fixture(autouse=True)
def environment(tmp_path, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("POSTGRES_URL", raising=False)
    monkeypatch.delenv("DEV_USER_EMAIL", raising=False)
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("SUPABASE_URL", SUPABASE_URL)
    monkeypatch.setenv("SUPABASE_JWT_SECRET", JWT_SECRET)


def call(method, path, headers=ALICE, params=None, body=None):
    response = client.request(method, f"/api{path}", headers=headers, params=params, json=body)
    return response.status_code, response.json()


def add(headers=ALICE, **overrides):
    body = {
        "amount": 12.5,
        "type": "expense",
        "category": "Food",
        "description": "Lunch",
        "transaction_date": "2026-03-15",
        **overrides,
    }
    return call("POST", "/addtransaction", headers, body=body)


def test_add_and_list_transaction():
    status, created = add()
    assert status == 201
    assert created["transaction_id"] > 0

    status, rows = call("GET", "/gettransactions", params={"year": "2026", "month": "3"})
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
    _, rows = call("GET", "/gettransactions", params={"year": "2026", "month": "3"})
    assert [r["date"] for r in rows] == ["2026-03-31", "2026-03-01"]


def test_december_range_rolls_over_the_year():
    add(transaction_date="2026-12-31")
    add(transaction_date="2027-01-01")
    _, rows = call("GET", "/gettransactions", params={"year": "2026", "month": "12"})
    assert [r["date"] for r in rows] == ["2026-12-31"]


def test_limit_applies_without_a_period():
    for day in ("01", "02", "03"):
        add(transaction_date=f"2026-03-{day}")
    _, rows = call("GET", "/gettransactions", params={"limit": "2"})
    assert [r["date"] for r in rows] == ["2026-03-03", "2026-03-02"]


def test_summary_totals_and_categories():
    add(amount=3000, type="income", category="Salary")
    add(amount=200.10, category="Food")
    add(amount=99.90, category="Food")
    add(amount=450, category="Housing")
    add(amount=999, transaction_date="2026-04-01")

    status, summary = call("GET", "/getsummary", params={"year": "2026", "month": "3"})
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
    _, summary = call("GET", "/getsummary", params={"year": "2026", "month": "1"})
    assert summary["total_income"] == 0
    assert summary["net_savings"] == 0
    assert summary["categories"] == []


def test_users_only_see_and_delete_their_own_transactions():
    _, created = add(headers=ALICE)
    tx_id = created["transaction_id"]

    _, bobs = call("GET", "/gettransactions", headers=BOB)
    assert bobs == []

    status, _ = call("DELETE", f"/deletetransaction/{tx_id}", BOB)
    assert status == 404

    status, _ = call("DELETE", f"/deletetransaction/{tx_id}", ALICE)
    assert status == 200
    _, rows = call("GET", "/gettransactions", headers=ALICE)
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


@pytest.mark.parametrize("content", [b"{not json", b"[1, 2]", b""])
def test_bodies_that_are_not_a_json_object_are_rejected(content):
    response = client.post(
        "/api/addtransaction",
        headers={**ALICE, "Content-Type": "application/json"},
        content=content,
    )
    assert response.status_code == 400
    assert "error" in response.json()


@pytest.mark.parametrize("params", [
    {"year": "2026", "month": "13"},
    {"year": "abc", "month": "3"},
    {"limit": "0"},
    {"limit": "many"},
])
def test_invalid_query_parameters_are_rejected(params):
    status, _ = call("GET", "/gettransactions", params=params)
    assert status == 400


def test_delete_requires_a_numeric_id():
    status, _ = call("DELETE", "/deletetransaction/1 OR 1=1")
    assert status == 400


def test_unknown_routes_use_the_json_error_shape():
    status, body = call("GET", "/nope")
    assert status == 404
    assert "error" in body


def test_requests_without_a_token_are_unauthorised():
    status, body = call("GET", "/gettransactions", headers={})
    assert status == 401
    assert body == {"error": "Sign in required"}


@pytest.mark.parametrize("bad_token", [
    "not-a-jwt",
    token("alice@example.com", key="a-different-secret-of-sufficient-length!"),
    token("alice@example.com", exp=int(time.time()) - 60),
    token("alice@example.com", aud="anon"),
    token("alice@example.com", iss="https://evil.example/auth/v1"),
    token(None),
    jwt.encode({"email": "alice@example.com", "aud": "authenticated"}, None, algorithm="none"),
])
def test_invalid_tokens_are_unauthorised(bad_token):
    status, body = call("GET", "/gettransactions", headers=bearer(bad_token))
    assert status == 401
    assert body == {"error": "Sign in required"}


def test_tokens_signed_with_the_project_jwks_key_are_accepted(monkeypatch):
    private_key = ec.generate_private_key(ec.SECP256R1())

    class FakeJwksClient:
        def get_signing_key_from_jwt(self, _token):
            return type("SigningKey", (), {"key": private_key.public_key()})

    urls = []
    monkeypatch.setattr(auth, "jwks_client", lambda url: urls.append(url) or FakeJwksClient())
    monkeypatch.delenv("SUPABASE_JWT_SECRET")

    carol = bearer(token("carol@example.com", key=private_key, algorithm="ES256"))
    status, _ = add(headers=carol)
    assert status == 201
    assert urls == [f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json"]

    other_key = ec.generate_private_key(ec.SECP256R1())
    forged = bearer(token("carol@example.com", key=other_key, algorithm="ES256"))
    status, _ = call("GET", "/gettransactions", headers=forged)
    assert status == 401


def test_dev_user_email_is_used_when_there_is_no_token(monkeypatch):
    monkeypatch.setenv("DEV_USER_EMAIL", "dev@localhost")
    status, _ = add(headers={})
    assert status == 201
    _, rows = call("GET", "/gettransactions", headers=bearer(token("dev@localhost")))
    assert len(rows) == 1


def test_dev_user_email_is_ignored_on_vercel(monkeypatch):
    monkeypatch.setenv("DEV_USER_EMAIL", "dev@localhost")
    monkeypatch.setenv("VERCEL", "1")
    status, _ = call("GET", "/gettransactions", headers={})
    assert status == 401


def test_postgres_url_drops_options_libpq_does_not_know(monkeypatch):
    assert main.db.postgres_url() is None

    monkeypatch.setenv(
        "POSTGRES_URL",
        "postgres://u:p@host:6543/postgres?sslmode=require&supa=base-pooler.x&pgbouncer=true",
    )
    assert main.db.postgres_url() == "postgres://u:p@host:6543/postgres?sslmode=require"

    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@other/db")
    assert main.db.postgres_url() == "postgresql://u:p@other/db"


def test_health_needs_no_sign_in():
    status, body = call("GET", "/health", headers={})
    assert status == 200
    assert body == {"status": "ok"}


def test_unexpected_errors_do_not_leak_details(monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("password=hunter2")

    monkeypatch.setattr(main.db, "get_or_create_user", boom)
    status, body = call("GET", "/gettransactions")
    assert status == 500
    assert body == {"error": "Internal server error"}
