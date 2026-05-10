import azure.functions as func
import logging
import json
import datetime
from db_config import get_db_connection, get_user_id_from_auth

def main(req: func.HttpRequest) -> func.HttpResponse:
    # Get authenticated user email
    user_email = req.headers.get("x-ms-client-principal-name")
    if not user_email:
        return func.HttpResponse("Unauthorized", status_code=401)
    
    try:
        req_body = req.get_json()
        user_id = get_user_id_from_auth(user_email)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO transactions (user_id, amount, type, category, description, transaction_date)
            OUTPUT INSERTED.transaction_id
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            req_body['amount'],
            req_body['type'],
            req_body['category'],
            req_body.get('description', ''),
            req_body['transaction_date']
        ))
        
        transaction_id = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        
        return func.HttpResponse(
            json.dumps({"transaction_id": transaction_id, "message": "Transaction added"}),
            status_code=201,
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return func.HttpResponse(f"Error: {str(e)}", status_code=400)