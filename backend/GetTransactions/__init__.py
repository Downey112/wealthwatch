import azure.functions as func
import logging
import json
from db_config import get_db_connection, get_user_id_from_auth

def main(req: func.HttpRequest) -> func.HttpResponse:
    user_email = req.headers.get("x-ms-client-principal-name")
    if not user_email:
        return func.HttpResponse("Unauthorized", status_code=401)
    
    user_id = get_user_id_from_auth(user_email)
    
    # Get query parameters
    year = req.params.get('year')
    month = req.params.get('month')
    limit = req.params.get('limit', 50)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if year and month:
        cursor.execute("""
            SELECT transaction_id, amount, type, category, description, transaction_date, created_at
            FROM transactions
            WHERE user_id = ? AND YEAR(transaction_date) = ? AND MONTH(transaction_date) = ?
            ORDER BY transaction_date DESC
        """, (user_id, year, month))
    else:
        cursor.execute("""
            SELECT transaction_id, amount, type, category, description, transaction_date, created_at
            FROM transactions
            WHERE user_id = ?
            ORDER BY transaction_date DESC
            OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY
        """, (user_id, limit))
    
    transactions = []
    for row in cursor.fetchall():
        transactions.append({
            "id": row[0],
            "amount": float(row[1]),
            "type": row[2],
            "category": row[3],
            "description": row[4],
            "date": row[5].isoformat()
        })
    
    conn.close()
    
    return func.HttpResponse(
        json.dumps(transactions),
        mimetype="application/json"
    )