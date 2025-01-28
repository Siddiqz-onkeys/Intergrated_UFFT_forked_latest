import mysql.connector
from datetime import datetime 
from flask import Flask,request,render_template,jsonify,redirect,url_for
import os,time
from werkzeug.utils import secure_filename

db_config={
    'host':'localhost',
    'user':'root',
    'password':'$9Gamb@098',
    'database':'project_ufft',
    'port':3306
}

#establishing a conenction with the database using the configuration
connect_=mysql.connector.connect(**db_config)
cursor=connect_.cursor()

select_par=int(input("1. LAST 10 DAYS \n2. LAST 15 DAYS \n3.LAST 1 MONTH \n4.LAST 3 MONTHS \n5.LAST 1 YEAR \n6.OVERALL \n CHOOSE ONE: "))

# Base query
query = """
WITH category_totals AS (
    SELECT 
        c.name AS category_name, 
        SUM(e.amount) AS total_spent_on_category
    FROM expenses e
    JOIN categories c ON e.category_id = c.category_id
    WHERE e.user_id = 1
        {date_filter}
    GROUP BY c.name
    ORDER BY total_spent_on_category DESC
    LIMIT 1
)
SELECT 
    ROUND(SUM(e.amount), 2) AS total_spent,
    (SELECT category_name FROM category_totals) AS most_spent_on_category,
    (SELECT total_spent_on_category FROM category_totals) AS amount_spent_on_top_category,
    ROUND(AVG(e.amount), 2) AS average_amount_spent,
    COUNT(*) AS total_expenses_logged
FROM expenses e
WHERE e.user_id = 1
    {date_filter};
"""

# Define date filters based on the option selected
date_filter = ""
match select_par:  # select_par determines the time range
    case 1:
        date_filter = "AND e.date >= CURDATE() - INTERVAL 10 DAY"
    case 2:
        date_filter = "AND e.date >= CURDATE() - INTERVAL 15 DAY"
    case 3:
        date_filter = "AND e.date >= CURDATE() - INTERVAL 1 MONTH"
    case 4:
        date_filter = "AND e.date >= CURDATE() - INTERVAL 3 MONTH"
    case 5:
        date_filter = "AND e.date >= CURDATE() - INTERVAL 1 YEAR"
    case 6:
        date_filter = ""  # No date filter for all-time expenses

# Final query with date filter injected
query = query.format(date_filter=date_filter)

# Execute the query
cursor.execute(query)   
tot=cursor.fetchone()
summary=[
    {
        'total_spent':tot[0],
        'most_spent_cat':tot[1],
        'most_spent_cat_amount':tot[2],
        'avg_amount_spent':tot[3],
        'no_of_exps_logged':tot[4]
    }
]
#return redirect('index.html',summary=summary)
print("TOTAL AMOUNT SPENT:",tot[0])
print("MOST SEPNT ON CATEGORY: ",tot[1])
print("AMOUNT SPENT ON MOST SPENT CATEGORY: ",tot[2])
print("AVERAGE AMOUNT SPENT: ",tot[3])
print("NO OF EXPENSES LOGGED: ",tot[4])

