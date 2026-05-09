import azure.functions as func
import json
import os
import pyodbc

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="summary")
def summary(req: func.HttpRequest) -> func.HttpResponse:
    # 1. Grab the secret keys from Azure Environment Variables
    conn_str = os.environ.get('SQL_CONNECTION_STRING')
    
    if not conn_str:
        return func.HttpResponse(
            json.dumps({"error": "Database connection string missing."}), 
            status_code=500, mimetype="application/json"
        )

    try:
        # 2. Connect to the Azure SQL Database
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        # 3. Query the real data! 
        # (Change 'Transactions', 'Amount', and 'Type' if your table is named differently)
        cursor.execute("SELECT ISNULL(SUM(Amount), 0) FROM Transactions WHERE Type = 'income'")
        total_income = float(cursor.fetchone()[0])

        cursor.execute("SELECT ISNULL(SUM(Amount), 0) FROM Transactions WHERE Type = 'expense'")
        total_expenses = float(cursor.fetchone()[0])

        # 4. Calculate the real balance
        balance = total_income - total_expenses

        # Format numbers beautifully for the React frontend
        formatted_income = f"RM {total_income:,.2f}"
        formatted_expenses = f"RM {total_expenses:,.2f}"
        formatted_balance = f"RM {balance:,.2f}"
        
        trend_text = "↑ Active this month" if balance >= 0 else "↓ Deficit this month"

        # 5. Package the real data to send to React
        financial_data = {
            "balance": formatted_balance,
            "trend": trend_text,
            "income": formatted_income,
            "expenses": formatted_expenses,
            # We will leave the chart bars as static for now to keep the UI looking cool
            "chartData": [
                {"height": "40%", "type": "green"},
                {"height": "60%", "type": "red"},
                {"height": "30%", "type": "green"},
                {"height": "80%", "type": "green"},
                {"height": "50%", "type": "red"}
            ]
        }

        return func.HttpResponse(
            json.dumps(financial_data),
            mimetype="application/json"
        )

    except Exception as e:
        # If the database crashes, send the exact error message to help us debug
        return func.HttpResponse(
            json.dumps({"error": f"Database Error: {str(e)}"}), 
            status_code=500, mimetype="application/json"
        )