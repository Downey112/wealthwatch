import azure.functions as func
import logging
from db_config import get_db_connection, get_user_id_from_auth

def main(req: func.HttpRequest) -> func.HttpResponse:
    user_email = req.headers.get("x-ms-client-principal-name")
    if not user_email:
        return func.HttpResponse("Unauthorized", status_code=401)
    
    transaction_id = req.route_params.get('id')
    if not transaction_id:
        return func.HttpResponse("Transaction ID required", status_code=400)
    
    user_id = get_user_id_from_auth(user_email)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM transactions WHERE transaction_id = ? AND user_id = ?", 
                   (transaction_id, user_id))
    conn.commit()
    
    affected = cursor.rowcount
    conn.close()
    
    if affected > 0:
        return func.HttpResponse("Deleted successfully", status_code=200)
    else:
        return func.HttpResponse("Transaction not found", status_code=404)