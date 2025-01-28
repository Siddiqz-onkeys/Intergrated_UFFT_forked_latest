projectufft# db_connection.py
import mysql.connector
from mysql.connector import Error

def get_connection():
    """Creates and returns a new database connection."""
    try:
        connection = mysql.connector.connect(
            host='project-ufft-20.cvs82c00gy0z.ap-south-1.rds.amazonaws.com',          # Replace with your database host
            user='root',          # Replace with your database username
            password='$Drop_Down%86',  # Replace with your database password
            database='project-ufft-20'   # Replace with your database name
        )
        return connection
    except Error as e:
        print(f"Error connecting to database: {e}")
        raise
