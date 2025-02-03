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

###### Creating session ################# do not remove it is imp ####
def create_session(session,cur,login_name):
    session['login_name'] = login_name
    cur.execute("SELECT user_id, role, family_id, name FROM users WHERE user_name = %s", (login_name,))
    user_data = cur.fetchone()
    if user_data:
        session['user_id'], session['role'], session['family_id'], session['name'] = user_data
    else:
        print("User not found.")

