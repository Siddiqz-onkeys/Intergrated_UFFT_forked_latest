# db_connection.py
import mysql.connector
from mysql.connector import Error

def get_connection():
    """Creates and returns a new database connection."""
    try:
        connection = mysql.connector.connect(
            host='localhost',          # Replace with your database host
            user='root',          # Replace with your database username
            password='root',  # Replace with your database password
            database='projectufft'   # Replace with your database name
        )
        return connection
    except Error as e:
        print(f"Error connecting to database: {e}")
        raise
