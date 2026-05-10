import os
import pyodbc
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    server = os.environ.get("DB_SERVER")
    database = os.environ.get("DB_NAME")
    username = os.environ.get("DB_USER")
    password = os.environ.get("DB_PASSWORD")
    
    connection_string = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
    
    return pyodbc.connect(connection_string)

def get_user_id_from_auth(email):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get or create user
    cursor.execute("SELECT user_id FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    
    if row:
        user_id = row[0]
    else:
        cursor.execute("INSERT INTO users (email) OUTPUT INSERTED.user_id VALUES (?)", (email,))
        user_id = cursor.fetchone()[0]
        conn.commit()
    
    conn.close()
    return user_id