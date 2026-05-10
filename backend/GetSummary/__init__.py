import azure.functions as func
import logging
import json
from db_config import get_db_connection, get_user_id_from_auth
from datetime import datetime

def main(req: func.HttpRequest) -> func.HttpResponse:
    user_email = req.headers.get("x-ms-client-principal-name")
    if not user_email:
        return func.HttpResponse("Unauthorized", status_code=401)
    
    user_id = get_user_id_from_auth(user_email)
    
    # Get current month if not specified
    year = req.params.get('year', datetime.now().year)
    month = req.params.get('month', datetime.now().month)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get monthly summary
    cursor.execute("EXEC GetMonthlySummary ?, ?, ?", (user_id, year, month))
    summary = cursor.fetchone()
    
    # Get category breakdown
    cursor.execute("EXEC GetCategoryBreakdown ?, ?, ?", (user_id, year, month))
    categories = []
    for row in cursor.fetchall():
        categories.append({
            "category": row[0],
            "total": float(row[1])
        })
    
    conn.close()
    
    result = {
        "year": int(year),
        "month": int(month),
        "total_income": float(summary[0]) if summary[0] else 0,
        "total_expense": float(summary[1]) if summary[1] else 0,
        "net_savings": float(summary[2]) if summary[2] else 0,
        "categories": categories
    }
    
    return func.HttpResponse(
        json.dumps(result),
        mimetype="application/json"
    )