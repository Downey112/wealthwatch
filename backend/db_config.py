import os
import pymssql
import logging

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