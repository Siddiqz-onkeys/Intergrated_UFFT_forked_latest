import mysql.connector
from datetime import datetime 
from flask import Flask,request,render_template,jsonify,redirect,url_for,Blueprint,session,current_app
from flask_mail import Message
import os,time
from werkzeug.utils import secure_filename
from threading import Timer
from apscheduler.schedulers.background import BackgroundScheduler
import smtplib
import traceback
from db_connection import get_connection

## initializing the flask application
app=Flask(__name__)

expense_bp = Blueprint('expense', __name__, template_folder='templates', static_folder='static')


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads', 'receipts')

# Configure the upload folder for the Flask application
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Sort order for sorting functionality
sort_order = {
    'date': 'default',
    'name': 'default',
    'amount': 'default',
    'description': 'default',
    'receipt': 'default',
}


GMAIL_ID='dum31555@gmail.com'
GMAIL_PSWD='dweg wzyz mbfa wvkv'

def sendEmail(to, sub, msg):
    print(f"Email to {to} sent with sub:{sub} and message {msg}")
    s=smtplib.SMTP('smtp.gmail.com',587)
    s.starttls()
    s.login(GMAIL_ID,GMAIL_PSWD)
    s.sendmail(GMAIL_ID, to, f"Subject: {sub}\n\n{msg}")
    s.quit()

#establishing a conenction with the database using the configuration
connect_=get_connection()
#cursor=connect_.cursor()
cursor = connect_.cursor(buffered=True)


def get_recc_to_sendemail():
    print("Called")
    cursor.execute("SELECT users.user_name,users.email,recc_expenses.amount,recc_expenses.description FROM users JOIN recc_expenses on users.user_id=recc_expenses.user_id WHERE start_date BETWEEN CURDATE() AND CURDATE() + INTERVAL 3 DAY;")
    res = cursor.fetchall()

    recs=[{
        'user_name':exp[0],
        'email':exp[1],
        'amount':exp[2],
        'description':exp[3]
    }for exp in res]
    subject="remainder for the upcoming reccuring expense"

    for exp in recs:
        msg=(
            f"Hey {exp['user_name']},\n\n"
            f"This is just a remainder for your upcoming recurring expense:\n"
            f"Expense: {exp['description']}\n"
            f"Amount: ${exp['amount']}\n"
            f"Regards,\n Expense Management Team,\n Famora"
        )
        sendEmail(exp['email'],subject,msg)
    print("mail has been sent")

############ to automate the remainder sending fucntion ###########
scheduler = BackgroundScheduler()
scheduler.add_job(func=get_recc_to_sendemail, trigger="interval", hours=24)  # Runs every 24 hours
scheduler.start()

########################### Shut down the scheduler when the app stops
import atexit
atexit.register(lambda: scheduler.shutdown())

########### Fetch expenses #############
def get_expenses():
    cursor.execute("SELECT expense_id, date, name, amount, description, receipt FROM expenses e1 JOIN categories c1 ON e1.category_id = c1.category_id WHERE user_id=%s ORDER BY expense_id DESC ",(curr_user,))
    expenses = cursor.fetchall()

    expense_records = [
        {
            'expense_id': exp[0],
            'date_in': exp[1],
            'category': exp[2],
            'amount': exp[3],
            'desc': exp[4],
            'receipt': exp[5]
        }
        for exp in expenses
    ]
    
    return expense_records

######### Get users #######
def get_users():
    cursor.execute("SELECT user_id, user_name FROM users WHERE family_id = %s", (curr_family_id,))
    users_list = cursor.fetchall()

    users = [
        {
            'user_id': user[0],
            'user_name': user[1],
        } for user in users_list if user[0] != curr_user  # Exclude current user
    ]
    
    return users


########### get recurring expenses #######
def get_recs():
    # Fetch recurring expenses
        cursor.execute("SELECT rec_id, description, amount FROM recc_expenses WHERE user_id=%s ",(curr_user,))
        recs = cursor.fetchall()

        rec_exps = [
            {
                'rec_id': exp[0],
                'description': exp[1],
                'amount': exp[2],
            }
            for exp in recs
        ]
        return rec_exps


############ get categoies ########
def get_cats():
    # Fetch all categories
        cursor.execute("SELECT * FROM categories")
        cats = cursor.fetchall()
        categories = [
            {
                'cat_id': item[0],
                'cat_name': item[1]
            }
            for item in cats
        ]
        return categories


##### send user alert mail ###
def send_user_alert_email(user_email, total_expenses, user_budget):
    """Send an alert email to the user when budget for user is exceeded."""
    mail = current_app.extensions['mail']  # Use the current app's mail instance
    subject = f" Personal Budget Alert: User budget Exceeded"
    body = f"""
    Dear User,

    Alert! Your total expenses have exceeded your personal budget.
    
    Total Expenses: ₹{total_expenses}
    Threshold: ₹{user_budget}
    
    Please review your spending.
    
    Regards,
    Budget Tracker Team
    """
    message = Message(subject=subject, recipients=[user_email], body=body)

    try:
        mail.send(message)
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")

########### ESTABLISHING A ROUTE FOR THE HTML REQUEST ##########
@expense_bp.route('/', methods=["GET", "POST"])
def index():
    #carry the user id
    global curr_user
    curr_user=session['user_id']
    
    #carry the user role
    global curr_user_role
    curr_user_role=session['role'].lower()
    
    #carry the current date
    global current_date
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    #carry the fmaily id
    global curr_family_id
    curr_family_id=session['family_id']
    
    #carry the user name
    global curr_user_name
    curr_user_name=session['login_name']
    
    ## carry the email of the user
    global curr_user_email
    cursor.execute("SELECT email FROM users WHERE user_id=%s",(curr_user,))
    curr_user_email=cursor.fetchone()[0]
    
    # Fetching users data
    if request.method == "GET":

        return render_template(
            'index.html',major=verify_major(),
            expenses=get_expenses(),
            user_id=curr_user,
            users=get_users(),
            reccur_exps=get_recs(),
            categories=get_cats(),
            max_date=current_date,
            user_role=curr_user_role,
            user_name=curr_user_name,family_fetch=False
        )
    
    else:
        
        family_user = request.form.get('user_id')
        # Fetch expenses for the user
        try:
            cursor.execute("""
                SELECT expense_id, date, name, amount, description, receipt 
                FROM expenses e1 
                JOIN categories c1 ON e1.category_id = c1.category_id 
                WHERE user_id=%s 
                ORDER BY expense_id DESC
            """, (family_user,))
            expenses = cursor.fetchall()
            
            expense_records = [
                {
                    'expense_id': exp[0],
                    'date_in': exp[1],
                    'category': exp[2],
                    'amount': exp[3],
                    'desc': exp[4],
                    'receipt': exp[5]
                }
                for exp in expenses
            ]
        except mysql.connector.Error as err:
            print(f"Error fetching expenses: {err}")
            expense_records = []


        return render_template(
            'index.html',major=verify_major(),
            expenses=expense_records,
            user_id=curr_user,
            users=get_users(),
            reccur_exps=get_recs(),
            categories=get_cats(),
            max_date=current_date,
            user_role=curr_user_role,
            user_name=curr_user_name,
            family_fetch=True
        )

########## SAVING THE UPLOADED FILES IN A FOLDER ############
@expense_bp.route('/upload_receipt', methods=['POST'])
def upload_receipt():
    file = request.files['file']
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return render_template('index.html',expenses=get_expenses(),users=get_users(),max_date=current_date)


###### getting the form data and calling the add expense function
@expense_bp.route('/get_form_data',methods=['POST'])
def get_form_data():
    new_exp=False
    category=request.form.get('category')
    #print("Category being queried:", category)

    cursor.execute("SELECT category_id FROM categories WHERE name=%s",(category,))
    res=cursor.fetchone()
    category_id=res[0]
    
    
    date_in=request.form.get('date')
    #print(date_in)
        
    amount=float(request.form.get('amount'))
    #print(amount)
    
    description=request.form.get('desc')
    if not description :
        description=""
    #print(description)
        
    # Handle the receipt file upload
    receipt_file = request.files['file']
    receipt_filename = None
    receipt=""
    if receipt_file:
        receipt_filename = secure_filename(receipt_file.filename)
        receipt_file.save(os.path.join(app.config['UPLOAD_FOLDER'], receipt_filename))
        receipt = receipt_filename
    
    # Add the expense to the database
    add_expense(category_id, amount, date_in, description, receipt)
    new_exp=True
    
    
    ###### ADD { user_role=curr_user_role,user_name=curr_user_name } WHILE INTGRATING 
    return render_template(
            'index.html',major=verify_major(),
            expenses=get_expenses(),
            user_id=curr_user,
            users=get_users(),
            reccur_exps=get_recs(),
            categories=get_cats(),
            max_date=current_date,
            user_role=curr_user_role,
            user_name=curr_user_name
        )

####### ADD EXPENSE ###########
def add_expense(category_id, amount, date_in, description="", receipt=""):
    # Start constructing the query
    query = "INSERT INTO expenses (user_id, category_id, date, amount, family_id"
    params = [curr_user, category_id, date_in, amount, curr_family_id]
    
    # Dynamically add optional columns
    if description:
        query += ", description"
        params.append(description)
    if receipt:
        query += ", receipt"
        params.append(receipt)
    
    # Close the column list and prepare placeholders
    values = ', '.join(['%s'] * len(params))
    query += f") VALUES ({values})"
    
    # Execute the query
    cursor.execute(query, tuple(params))
    connect_.commit()
    
    # Calculate user's total expenses dynamically
    cursor.execute('''
        SELECT SUM(amount) AS total_expenses
        FROM expenses
        WHERE user_id = %s
    ''', (curr_user,))
    total_expenses = cursor.fetchone()
    total_expenses = total_expenses[0] if total_expenses else 0

    # Fetch user's personal budget
    cursor.execute('SELECT amount AS user_budget FROM budgets WHERE user_id = %s', (curr_user,))
    budget_data = cursor.fetchone()

    # Send alert email if expenses exceed budget
    if budget_data and total_expenses > budget_data[0]:
        send_user_alert_email(curr_user_email, total_expenses, budget_data[0])

    # Check if total expenses exceed the category threshold
    cursor.execute('''
        SELECT 
            budgets.amount AS budget_amount,
            budgets.threshold_value,
            categories.name AS category_name
        FROM budgets
        INNER JOIN categories ON budgets.category_id = categories.category_id
        WHERE budgets.category_id = %s
    ''', (category_id,))
    budget = cursor.fetchone()

    cursor.execute('''
        SELECT SUM(amount) AS category_total_expenses
        FROM expenses
        WHERE category_id = %s and user_id=%s
    ''', (category_id,curr_user,))
    category_total_expenses = cursor.fetchone()
    category_total_expenses = category_total_expenses[0] if category_total_expenses else 0

    # Send email if category expenses exceed the threshold
    if budget and category_total_expenses > budget[1]:
        send_alert_email(curr_user_email, budget[2], category_total_expenses, budget[1])


#### to send mail s regarding the budgets 
def send_alert_email(user_mail,name, total_expenses, threshold_value):
        """Send an alert email to the user when budget threshold is exceeded."""
        mail = current_app.extensions['mail']  # Use the current app's mail instance
        subject = f"Budget Alert: {name} Expenses Exceeded"
        body = f"""
        Dear User,

        Your expenses for the category '{name}' have exceeded the budget threshold.
        
        Total Expenses: ₹{total_expenses}
        Threshold: ₹{threshold_value}
        
        Please review your spending.
        
        Regards,
        Budget Tracker Team
        """
        message = Message(subject=subject, recipients=[user_mail], body=body)

        try:
            mail.send(message)
            print("Email sent successfully!")
        except Exception as e:
            print(f"Error sending email: {e}")
        

######### AGE VERIFICATION ############
@expense_bp.route('/verify_major',methods=["GET"])
def verify_major():
    cursor.execute("SELECT dob FROM users WHERE user_id=%s",(curr_user,))
    dob=cursor.fetchone()[0]
    current_day=datetime.today()
    
    age=abs(dob.year-current_day.year)
    if (current_day.month, current_day.day) < (dob.month, dob.day):
        age -= 1
    
    is_major = age > 18
    return jsonify({"is_major": is_major})           
 
# Global variable to store the deleted expense
deleted_expense = None
@expense_bp.route('/delete_expense/<int:expense_id>', methods=["POST"])
def delete_expense(expense_id):
    print("entered")
    global deleted_expense
    isdeleted = False
    status_undo=False
    # Fetch the expense to delete
    cursor.execute("SELECT expense_id, user_id, category_id, CAST(date AS DATETIME), amount, family_id, description, receipt FROM expenses WHERE expense_id=%s", (expense_id,))
    deleted_expense = cursor.fetchone()
    
    if deleted_expense:
        cursor.execute("DELETE FROM expenses WHERE expense_id=%s", (expense_id,))
        connect_.commit()
        isdeleted = True

    ###### ADD { user_role=curr_user_role,user_name=curr_user_name } WHILE INTGRATING 
    return render_template(
            'index.html',major=verify_major(),
            expenses=get_expenses(),
            user_id=curr_user,
            users=get_users(),
            reccur_exps=get_recs(),
            categories=get_cats(),
            max_date=current_date,
            user_role=curr_user_role,
            user_name=curr_user_name,status_delete=isdeleted,
        )



###### Rollback the deletion  ################
@expense_bp.route('/rollback_deletion', methods=["POST"])
def rollback_deletion():
    status_undo=False
    if deleted_expense:
        # Log the deleted expense to verify
        print(f"Restoring deleted expense: {deleted_expense}")
        
        # Ensure the column names match the ones in your database schema
        # Insert the deleted expense back into the database
        cursor.execute(
            """
            INSERT INTO expenses (expense_id, user_id, category_id, date, amount, family_id, description, receipt)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                deleted_expense[0],  # expense_id (index 0)
                deleted_expense[1],  # user_id (index 1)
                deleted_expense[2],  # category_id (index 2)
                deleted_expense[3].strftime('%Y-%m-%d %H:%M:%S') if isinstance(deleted_expense[3], datetime) else None,  # date (index 3)
                deleted_expense[4],  # amount (index 4)
                deleted_expense[5],  # family_id (index 5)
                deleted_expense[6],  # description (index 6)
                deleted_expense[7]   # receipt (index 7)
            )
        )
        connect_.commit()
        isdeleted=False
        status_undo=True
    ###### ADD { user_role=curr_user_role,user_name=curr_user_name } WHILE INTGRATING 
    return render_template(
        'index.html',major=verify_major(),
        expenses=get_expenses(),
        user_id=curr_user,
        users=get_users(),
        reccur_exps=get_recs(),
        categories=get_cats(),
        max_date=current_date,
        user_role=curr_user_role,
        user_name=curr_user_name,status_undo=status_undo
    )




############ EDIT EXPENSE #######
@expense_bp.route('/edit_expense/<int:expense_id>', methods=["POST"])
def edit_expense(expense_id):
    ##### old values ####
    cursor.execute("SELECT amount,date,category_id,description,receipt FROM expenses WHERE expense_id=%s",(expense_id,))
    res=cursor.fetchone()
    old_amount=res[0]
    old_date=res[1]
    old_cat_id=res[2]
    cursor.execute("SELECT name FROM categories WHERE category_id=%s",(old_cat_id,))
    old_cat=cursor.fetchone()[0]
    old_desc=res[3]
    old_receipt=res[4]
    
    #### fetching new values fromthe form
    new_amount=request.form.get('amount')
    if not new_amount:
        new_amount=old_amount
        
    new_date=request.form.get('date')
    if not new_date:
        new_date=old_date
        
    new_category=request.form.get('category')
    if not new_category:
        new_category=old_cat
    
    cursor.execute("SELECT category_id FROM categories WHERE name=%s",(new_category,))
    new_cat_id=cursor.fetchone()[0]
    
    new_desc=request.form.get('desc')
    
    new_receipt = request.files['file']
    new_receipt_filename = None
    receipt = None  # Initialize receipt

    if new_receipt:
        new_receipt_filename = secure_filename(new_receipt.filename)
        new_receipt.save(os.path.join(app.config['UPLOAD_FOLDER'], new_receipt_filename))
        receipt = new_receipt_filename
        
        # Check if old_receipt is valid and different from new receipt
        if old_receipt and receipt != old_receipt:
            old_receipt_path = os.path.join(app.config['UPLOAD_FOLDER'], old_receipt)
            if os.path.exists(old_receipt_path):  # Ensure old_receipt_path is valid
                os.remove(old_receipt_path)

    else:
        receipt = old_receipt  # Keep the old receipt if no new file is uploaded

        
    cursor.execute("UPDATE expenses SET category_id=%s,amount=%s,description=%s,date=%s,receipt=%s WHERE expense_id=%s",(new_cat_id,new_amount,new_desc,new_date,receipt,expense_id,))
    connect_.commit()
    return render_template(
            'index.html',major=verify_major(),
            expenses=get_expenses(),
            user_id=curr_user,
            users=get_users(),
            reccur_exps=get_recs(),
            categories=get_cats(),
            max_date=current_date,user_role=curr_user_role,
            user_name=curr_user_name
        )
           

###### ADD AMOUNT #####    
@expense_bp.route('/add_amount/<int:expense_id>',methods=["POST"])
def add_amount(expense_id):
    cursor.execute("SELECT amount FROM expenses WHERE expense_id=%s",(expense_id,))
    old_amount=cursor.fetchone()[0]
    
    new_amount=request.form.get('add_amount')
    sum=float(new_amount)+float(old_amount)
    
    cursor.execute("UPDATE expenses SET amount=%s WHERE expense_id=%s",(sum,expense_id,))
    connect_.commit()
    return render_template(
            'index.html',major=verify_major(),
            expenses=get_expenses(),
            user_id=curr_user,
            users=get_users(),
            reccur_exps=get_recs(),
            categories=get_cats(),
            max_date=current_date,user_role=curr_user_role,
            user_name=curr_user_name
        )


@expense_bp.route('/filter_expenses', methods=["GET"])
def filter_expenses():
    min_amount = request.args.get('filter_amount_range_min')  # Minimum amount input
    max_amount = request.args.get('filter_amount_range_max')  # Maximum amount input
    category = request.args.get('filter_category')  # Category input
    desc = request.args.get('description')  # Description
    receipt = request.args.get('receipt')  # Receipt

    # Base query and parameters
    query = """
        SELECT e.expense_id, e.date, c.name, e.amount, e.description, e.receipt
        FROM expenses e
        JOIN categories c ON e.category_id = c.category_id
        WHERE e.user_id = %s
    """
    params = [curr_user]

    # Add filters dynamically
    conditions = []

    if category:
        conditions.append("c.name = %s")
        params.append(category)
    if min_amount and max_amount:
        conditions.append("e.amount BETWEEN %s AND %s")
        params.extend([min_amount, max_amount])
    elif min_amount:
        conditions.append("e.amount >= %s")
        params.append(min_amount)
    elif max_amount:
        conditions.append("e.amount <= %s")
        params.append(max_amount)
    if desc:
        conditions.append("e.description IS NOT NULL")
    if receipt:
        conditions.append("e.receipt IS NOT NULL")

    # Add conditions to the query
    if conditions:
        query += " AND " + " AND ".join(conditions)

    # Debug: Print query and params for troubleshooting
    print("Generated Query:", query)
    print("Parameters:", params)

    # Execute the query
    cursor.execute(query, tuple(params))
    filtered_expenses = cursor.fetchall()

    # Format the result
    filtered_expenses_list = [
        {
            'expense_id': exp[0],
            'date_in': exp[1],
            'category': exp[2],
            'amount': exp[3],
            'desc': exp[4],
            'receipt': exp[5]
        }
        for exp in filtered_expenses
    ]
    isfiltered=True
    # Render the filtered data
    current_date = datetime.now().strftime('%Y-%m-%d')
    return render_template(
            'index.html',major=verify_major(),
            expenses=filtered_expenses_list,
            user_id=curr_user,
            users=get_users(),
            reccur_exps=get_recs(),
            categories=get_cats(),isfiltered=isfiltered,
            max_date=current_date,user_role=curr_user_role,
            user_name=curr_user_name
        )


###### route to reset the view ########
@expense_bp.route('/reset_filters',methods=["GET"])
def reset_filters():
    # Redirect to the root route, where the unfiltered data is displayed
   return render_template(
            'index.html',major=verify_major(),
            expenses=get_expenses(),
            user_id=curr_user,
            users=get_users(),
            reccur_exps=get_recs(),
            categories=get_cats(),
            max_date=current_date,user_role=curr_user_role,
            user_name=curr_user_name
        )


        
######## ADD RECCURRING EXPENSE TO THE EXPENSES #########
@expense_bp.route('/add_rec_to_exp/<int:rec_id>',methods=["POST"])
def add_rec_to_exp(rec_id):
    cursor.execute("SELECT user_id, family_id, amount, category_id,description,start_date FROM recc_expenses where rec_id=%s ",(rec_id,))
    params=cursor.fetchone()
    params=list(params)
    params[-1]=request.form.get('date')
    cursor.execute("INSERT INTO expenses (user_id, family_id, amount, category_id,description,date) VALUES (%s,%s,%s,%s,%s,%s)",(tuple(params)))
    connect_.commit()  
    return render_template(
            'index.html',major=verify_major(),
            expenses=get_expenses(),
            user_id=curr_user,
            users=get_users(),
            reccur_exps=get_recs(),
            categories=get_cats(),
            max_date=current_date,user_role=curr_user_role,
            user_name=curr_user_name
        )


####### METHOD TO ADD A NEW RECCURING EXPENSE #######
@expense_bp.route('/add_rec_exp',methods=["POST"])
def add_rec_exp():   
    category=request.form.get('category')
    #print("Category being queried:", category)

    cursor.execute("SELECT category_id FROM categories WHERE name=%s",(category,))
    res=cursor.fetchone()
    category_id=res[0]
    
    start_date=request.form.get('start-date')
    
    end_date=request.form.get('end-date')
    
    amount=request.form.get('amount')
    
    desc=request.form.get('desc')
    
    cursor.execute("INSERT INTO recc_expenses (user_id,family_id,category_id,start_date,end_date,amount,description) VALUES (%s,%s,%s,%s,%s,%s,%s) ",(curr_user,curr_family_id,category_id,start_date,end_date,amount,desc,))
    connect_.commit()
    
    return render_template(
            'index.html',major=verify_major(),
            expenses=get_expenses(),
            user_id=curr_user,
            users=get_users(),
            reccur_exps=get_recs(),
            categories=get_cats(),
            max_date=current_date,user_role=curr_user_role,
            user_name=curr_user_name
        )


@expense_bp.route('/overview',methods=["POST"])
def overview():
    select_par=int(request.form.get('duration'))    
    # Define the base query
    base_query = """
    WITH category_totals AS (
        SELECT 
            c.name AS category_name, 
            SUM(e.amount) AS total_spent_on_category
        FROM expenses e
        JOIN categories c ON e.category_id = c.category_id
        WHERE e.user_id = {curr_user} {date_filter}
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
    WHERE e.user_id = {curr_user} {date_filter};
    """

    # Define date filters based on the option selected
    date_filter = ""
    match select_par:  # `select_par` determines the time range       
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

    # Inject the date filter into the query
    final_query = base_query.format(date_filter=date_filter,curr_user=curr_user)

    # Execute the query
    cursor.execute(final_query)
   
    tot=cursor.fetchone()
    summary_=[tot[0],tot[1],tot[2],tot[3],tot[4]]
    return render_template(
            'index.html',major=verify_major(),summary=summary_,
            expenses=get_expenses(),
            user_id=curr_user,
            users=get_users(),
            reccur_exps=get_recs(),
            categories=get_cats(),
            max_date=current_date,user_role=curr_user_role,
            user_name=curr_user_name
        )

if __name__=="__main__":
    app.run(debug=True)
