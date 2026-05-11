import azure.functions as func
import logging
import json
import pymssql
import os
from datetime import datetime
from decimal import Decimal

app = func.FunctionApp()

# Helper function to convert Decimal to float for JSON serialization
def convert_decimal(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

# Database connection helper using pymssql
def get_db_connection():
    server = os.environ.get("DB_SERVER")
    database = os.environ.get("DB_NAME")
    username = os.environ.get("DB_USER")
    password = os.environ.get("DB_PASSWORD")
    
    logging.info(f"Connecting to {server}...")
    
    return pymssql.connect(
        server=server,
        database=database,
        user=username,
        password=password,
        autocommit=False
    )

def get_user_id_from_auth(req, conn):
    """Extract user info from Static Web Apps headers"""
    user_email = req.headers.get("x-ms-client-principal-name")
    
    logging.info(f"User Email: {user_email}")
    
    if not user_email:
        user_email = "test@example.com"
        logging.warning("No auth header found, using test@example.com")
    
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute("SELECT user_id FROM users WHERE email = %s", (user_email,))
    row = cursor.fetchone()
    
    if row:
        user_db_id = row[0]
        logging.info(f"Found existing user: {user_db_id}")
        return user_db_id
    else:
        # Create new user
        cursor.execute(
            "INSERT INTO users (email, display_name) VALUES (%s, %s)",
            (user_email, user_email.split('@')[0])
        )
        conn.commit()
        
        # Get the new user_id
        cursor.execute("SELECT user_id FROM users WHERE email = %s", (user_email,))
        user_db_id = cursor.fetchone()[0]
        logging.info(f"Created new user: {user_db_id}")
        return user_db_id

# Add Transaction endpoint
@app.route(route="AddTransaction", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def add_transaction(req: func.HttpRequest) -> func.HttpResponse:
    try:
        req_body = req.get_json()
        logging.info(f"AddTransaction request body: {req_body}")
        
        conn = get_db_connection()
        user_id = get_user_id_from_auth(req, conn)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO transactions (user_id, amount, type, category, description, transaction_date)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            user_id,
            float(req_body['amount']),
            req_body['type'],
            req_body['category'],
            req_body.get('description', ''),
            req_body['transaction_date']
        ))
        
        conn.commit()
        
        # Get the inserted transaction ID
        cursor.execute("SELECT @@IDENTITY AS id")
        transaction_id = cursor.fetchone()[0]
        
        conn.close()
        
        return func.HttpResponse(
            json.dumps({"transaction_id": transaction_id, "message": "Transaction added"}),
            status_code=201,
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Error in AddTransaction: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}), 
            status_code=400, 
            mimetype="application/json"
        )

# Get Transactions endpoint
@app.route(route="GetTransactions", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_transactions(req: func.HttpRequest) -> func.HttpResponse:
    try:
        conn = get_db_connection()
        user_id = get_user_id_from_auth(req, conn)
        
        year = req.params.get('year')
        month = req.params.get('month')
        limit = req.params.get('limit', '50')
        
        cursor = conn.cursor()
        
        if year and month:
            cursor.execute("""
                SELECT transaction_id, amount, type, category, description, transaction_date
                FROM transactions
                WHERE user_id = %s AND YEAR(transaction_date) = %s AND MONTH(transaction_date) = %s
                ORDER BY transaction_date DESC
            """, (user_id, int(year), int(month)))
        else:
            cursor.execute("""
                SELECT TOP %s transaction_id, amount, type, category, description, transaction_date
                FROM transactions
                WHERE user_id = %s
                ORDER BY transaction_date DESC
            """, (int(limit), user_id))
        
        transactions = []
        for row in cursor.fetchall():
            transaction_date = row[5]
            if hasattr(transaction_date, 'isoformat'):
                date_str = transaction_date.isoformat()
            else:
                date_str = str(transaction_date)
            
            # Convert Decimal to float for JSON serialization
            amount_val = float(row[1]) if isinstance(row[1], Decimal) else row[1]
            
            transactions.append({
                "id": row[0],
                "amount": float(amount_val),
                "type": row[2],
                "category": row[3],
                "description": row[4] if row[4] else "",
                "date": date_str
            })
        
        conn.close()
        
        # Use custom JSON encoder for Decimal
        return func.HttpResponse(
            json.dumps(transactions, default=convert_decimal),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        logging.error(f"Error in GetTransactions: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=400,
            mimetype="application/json"
        )

# Get Summary endpoint
@app.route(route="GetSummary", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_summary(req: func.HttpRequest) -> func.HttpResponse:
    try:
        conn = get_db_connection()
        user_id = get_user_id_from_auth(req, conn)
        
        now = datetime.now()
        year = req.params.get('year', str(now.year))
        month = req.params.get('month', str(now.month))
        
        try:
            year_int = int(year)
            month_int = int(month)
        except ValueError:
            return func.HttpResponse(
                json.dumps({"error": "Invalid year or month format"}),
                status_code=400,
                mimetype="application/json"
            )
        
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as total_income,
                SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as total_expense,
                SUM(CASE WHEN type = 'income' THEN amount ELSE -amount END) as net_savings
            FROM transactions
            WHERE user_id = %s AND YEAR(transaction_date) = %s AND MONTH(transaction_date) = %s
        """, (user_id, year_int, month_int))
        
        summary = cursor.fetchone()
        
        cursor.execute("""
            SELECT category, SUM(amount) as total
            FROM transactions
            WHERE user_id = %s AND type = 'expense' AND YEAR(transaction_date) = %s AND MONTH(transaction_date) = %s
            GROUP BY category
            ORDER BY total DESC
        """, (user_id, year_int, month_int))
        
        categories = []
        for row in cursor.fetchall():
            # Convert Decimal to float
            total_val = float(row[1]) if isinstance(row[1], Decimal) else row[1]
            categories.append({
                "category": row[0],
                "total": float(total_val)
            })
        
        conn.close()
        
        result = {
            "year": year_int,
            "month": month_int,
            "total_income": float(summary[0]) if summary[0] else 0,
            "total_expense": float(summary[1]) if summary[1] else 0,
            "net_savings": float(summary[2]) if summary[2] else 0,
            "categories": categories
        }
        
        return func.HttpResponse(
            json.dumps(result, default=convert_decimal),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        logging.error(f"Error in GetSummary: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=400,
            mimetype="application/json"
        )

# Delete Transaction endpoint
@app.route(route="DeleteTransaction/{id}", methods=["DELETE"], auth_level=func.AuthLevel.ANONYMOUS)
def delete_transaction(req: func.HttpRequest) -> func.HttpResponse:
    try:
        transaction_id = req.route_params.get('id')
        if not transaction_id:
            return func.HttpResponse("Transaction ID required", status_code=400)
        
        conn = get_db_connection()
        user_id = get_user_id_from_auth(req, conn)
        
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transactions WHERE transaction_id = %s AND user_id = %s", 
                       (transaction_id, user_id))
        conn.commit()
        
        affected = cursor.rowcount
        conn.close()
        
        if affected > 0:
            return func.HttpResponse("Deleted successfully", status_code=200)
        else:
            return func.HttpResponse("Transaction not found", status_code=404)
    except Exception as e:
        logging.error(f"Error in DeleteTransaction: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}), 
            status_code=400, 
            mimetype="application/json"
        )