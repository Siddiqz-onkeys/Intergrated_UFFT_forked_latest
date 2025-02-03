import mysql.connector
from datetime import datetime 
from flask import Flask,request,render_template,jsonify,redirect,url_for,session,Blueprint
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


########## DEFINING A PATH TO SAVE THE UPLOADED FILES ##########
UPLOAD_FOLDER = 'static/uploads/receipts'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
sort_order={'date':'default',
            'name':'default',
            'amount':'default',
            'description':'default',
            'receipt':'default'}


#configuring the connect_ with the database
# db_config={
#     'host':'127.0.0.1',
#     'user':'root',
#     'password':'$9Gamb@098',
#     'database':'project_ufft',
#     'port':3306
# }



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
#connect_=mysql.connector.connect(**db_config)
connect_=get_connection()
cursor=connect_.cursor()

def get_recc_to_sendemail():
    print("Called")
    cursor.execute("SELECT users.user_name,users.email,rec_expenses.amount,rec_expenses.description FROM users JOIN rec_expenses on users.user_id=rec_expenses.user_id WHERE start_date BETWEEN CURDATE() AND CURDATE() + INTERVAL 3 DAY;")
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


def get_users():
    cursor.execute("SELECT user_id,user_name,family_id FROM users")
    users_list=cursor.fetchall()
    
    users=[
        {
            'user_id': user[0],
            'user_name':user[1],
            'family_id': user[2]
            
        } for user in users_list
    ]
    return users

def get_rec_exps():
    # Fetch recurring expenses
        cursor.execute("SELECT rec_id, description, amount FROM rec_expenses WHERE user_id=%s ",(curr_user,))
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
    
########### ESTABLISHING A ROUTE FOR THE HTML REQUEST ##########
@app.route('/',methods=["GET",'POST']) #creates a root route for the flask application
 #index function that returnrs the HTML content from the file and sends it to the user as a response for accessing the root URL
def index():
    global current_date
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    '''
    ########### USED ONLY IN INTEGRATION FOR CARRYING THE USER DETAILS  ############################
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
    curr_user_name=session['login_name']'''
   
    if request.method=="GET":
        ###### ADD { user_role=curr_user_role,user_name=curr_user_name } WHILE INTGRATING 
        return render_template('index.html',users=get_users(),max_date=current_date)
    else:
        global curr_user
        curr_user = request.form.get('user_id')
        # Fetch expenses for the user
        global curr_family_id
        global curr_user_role
        cursor.execute("SELECT family_id,role FROM users WHERE user_id=%s",(curr_user,))
        res=cursor.fetchone()
        curr_family_id=res[0]
        curr_user_role=res[1]
        
        
        
        ###### ADD { user_role=curr_user_role,user_name=curr_user_name } WHILE INTGRATING 
        return render_template('index.html',expenses=get_expenses(),user_id=curr_user,users=get_users(),major=verify_major(),
                reccur_exps=get_rec_exps(),
                categories=get_cats(),
                max_date=current_date) #Flask by default looks for templkate forlder to render the html file


########## SAVING THE UPLOADED FILES IN A FOLDER ############
@expense_bp.route('/upload_receipt', methods=['POST'])
def upload_receipt():
    file = request.files['file']
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        ###### ADD { user_role=curr_user_role,user_name=curr_user_name } WHILE INTGRATING 
        return render_template('index.html',expenses=get_expenses(),users=get_users(),max_date=current_date,major=verify_major())


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
    return render_template('index.html',expenses=get_expenses(),user_id=curr_user,users=get_users(),major=verify_major(),
                reccur_exps=get_rec_exps(),
                categories=get_cats(),new_exp=new_exp,
                max_date=current_date) ##### this returns a success message 


####### ADD EXPENSE ###########
def add_expense(category_id, amount, date_in, description="", receipt=""):
    # Ensure previous query results are cleared
    while cursor.nextset():
        pass
    
    # Start constructing the query
    query = "INSERT INTO EXPENSES (user_id, category_id, date, amount, family_id"
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

 ######### AGE VERIFICATION ############

def verify_major():
    cursor.execute("SELECT dob FROM users WHERE user_id=%s",(curr_user,))
    dob=cursor.fetchone()[0]
    current_day=datetime.today()
    
    age=abs(dob.year-current_day.year)
    if (current_day.month, current_day.day) < (dob.month, dob.day):
        age -= 1
    
    is_major = age > 18
    return is_major

# Global variable to store the deleted expense
deleted_expense = None
@expense_bp.route('/delete_expense/<int:expense_id>', methods=["GET"])
def delete_expense(expense_id):
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
    return render_template('index.html',expenses=get_expenses(),user_id=curr_user, users=get_users(), reccur_exps=get_rec_exps(), categories=get_cats(),status_delete=isdeleted ,max_date=current_date,major=verify_major())
    

@expense_bp.route('/rollback_deletion', methods=["POST"])
def rollback_deletion():
    status_undo=False
    try:
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
        return render_template('index.html',expenses=get_expenses(),user_id=curr_user, users=get_users(), reccur_exps=get_rec_exps(), categories=get_cats(),status_delete=isdeleted ,max_date=current_date,major=verify_major(),status_undo=status_undo)
    except Exception as e:
        # Print the stack trace to get more detailed error info
        print("Error during rollback:", e)
        traceback.print_exc()
        return jsonify({"rolled_back": False, "error": str(e)}), 500



############ EDIT EXPENSE #######
@expense_bp.route('/edit_expense/<int:expense_id>', methods=["POST"])
def edit_expense(expense_id):
    ##### Fetch old values #####
    cursor.execute("SELECT amount, date, category_id, description, receipt FROM expenses WHERE expense_id=%s", (expense_id,))
    res = cursor.fetchone()
    
    if not res:
        flash("Expense not found.", "error")
        return redirect(url_for("expense.index"))

    old_amount, old_date, old_cat_id, old_desc, old_receipt = res

    cursor.execute("SELECT name FROM categories WHERE category_id=%s", (old_cat_id,))
    old_cat_res = cursor.fetchone()
    old_cat = old_cat_res[0] if old_cat_res else None

    ##### Fetch new values from the form #####
    new_amount = request.form.get('amount', old_amount)
    new_date = request.form.get('date', old_date)
    new_category = request.form.get('category', old_cat)

    # Ensure the category exists before fetching ID
    cursor.execute("SELECT category_id FROM categories WHERE name=%s", (new_category,))
    new_cat_res = cursor.fetchone()
    
    if new_cat_res:
        new_cat_id = new_cat_res[0]
    else:
        flash("Invalid category selected.", "error")
        return redirect(url_for("expense.index"))

    new_desc = request.form.get('desc', old_desc)

    ##### Handle Receipt Upload #####
    new_receipt = request.files.get('file')
    receipt = old_receipt  # Default to old receipt

    if new_receipt and new_receipt.filename:
        new_receipt_filename = secure_filename(new_receipt.filename)
        new_receipt.save(os.path.join(app.config['UPLOAD_FOLDER'], new_receipt_filename))
        receipt = new_receipt_filename
        
        # Remove old receipt file if it's different from the new one
        if old_receipt and old_receipt != receipt:
            old_receipt_path = os.path.join(app.config['UPLOAD_FOLDER'], old_receipt)
            if os.path.exists(old_receipt_path):
                os.remove(old_receipt_path)

    ##### Ensure No Unread Results Before UPDATE #####
    cursor.fetchall()  # Clear any remaining results

    ##### Execute Update Query #####
    cursor.execute(
        "UPDATE expenses SET category_id=%s, amount=%s, description=%s, date=%s, receipt=%s WHERE expense_id=%s",
        (new_cat_id, new_amount, new_desc, new_date, receipt, expense_id),
    )
    connect_.commit()

    ##### Render the Updated Page #####
    return render_template(
        'index.html',
        expenses=get_expenses(),
        user_id=curr_user,
        users=get_users(),
        major=verify_major(),
        reccur_exps=get_rec_exps(),
        categories=get_cats(),
        max_date=current_date
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
    ###### ADD { user_role=curr_user_role,user_name=curr_user_name } WHILE INTGRATING 
    return render_template('index.html',expenses=get_expenses(),user_id=curr_user,users=get_users(),major=verify_major(),
                reccur_exps=get_rec_exps(),
                categories=get_cats(),
                max_date=current_date)


@expense_bp.route('/filter_expenses', methods=["GET"])
def filter_expenses():
    min_amount = request.args.get('filter_amount_range_min')  # Minimum amount input from the frontend
    max_amount = request.args.get('filter_amount_range_max')  # Maximum amount input from the frontend
    category = request.args.get('filter_category')  # Category input from the frontend
    desc=request.args.get('description') # Description
    receipt=request.args.get('receipt') #receipt   

    # Initialize base query and parameters
    query = "SELECT e.expense_id,e.date,c.name,e.amount,e.description,e.receipt FROM expenses e JOIN categories c ON e.category_id = c.category_id WHERE user_id=%s "
    params = [curr_user]
    
    if category:
        query+="AND c.name=%s "
        params+=[category]
    if min_amount and max_amount:
        query+="AND e.amount BETWEEN %s AND %s "
        params+=[min_amount,max_amount]
    elif min_amount:
        query+="AND e.amount>=%s "
        params+=[min_amount]
    elif max_amount:
        query+="AND e.amount<%s "
        params+=[max_amount]
        
    if desc:
        query+="AND e.description IS NOT NULL "
    if receipt:
        query+="AND e.receipt IS NOT NULL "
        

    
    cursor.execute(query, tuple(params))
    filtered_expenses = cursor.fetchall()
    
    filtered_expenses_list=[
        {
            'expense_id':exp[0],
            'date_in':exp[1],
            'category':exp[2],            
            'amount':exp[3],
            'desc':exp[4],
            'receipt':exp[5]            
        }
        for exp in filtered_expenses
    ]
    isfiltered=True
    current_date = datetime.now().strftime('%Y-%m-%d')
    ###### ADD { user_role=curr_user_role,user_name=curr_user_name } WHILE INTGRATING 
    return render_template('index.html',expenses=filtered_expenses_list,user_id=curr_user,users=get_users(),major=verify_major(),
                reccur_exps=get_rec_exps(),
                categories=get_cats(),isfiltered=isfiltered,
                max_date=current_date)


###### route to reset the view ########
@expense_bp.route('/reset_filters')
def reset_filters():
    # Redirect to the root route, where the unfiltered data is displayed
    return redirect('/')

        
######## ADD RECCURRING EXPENSE TO THE EXPENSES #########
@expense_bp.route('/add_rec_to_exp/<int:rec_id>',methods=["POST"])
def add_rec_to_exp(rec_id):
    cursor.execute("SELECT user_id, family_id, amount, category_id,description,receipt,start_date FROM rec_expenses where rec_id=%s ",(rec_id,))
    params=cursor.fetchone()
    params=list(params)
    params[-1]=request.form.get('date')
    cursor.execute("INSERT INTO expenses (user_id, family_id, amount, category_id,description,receipt,date) VALUES (%s,%s,%s,%s,%s,%s,%s)",(tuple(params)))
    connect_.commit()  
    ###### ADD { user_role=curr_user_role,user_name=curr_user_name } WHILE INTGRATING 
    return render_template('index.html',expenses=get_expenses(),user_id=curr_user,users=get_users(),major=verify_major(),
                reccur_exps=get_rec_exps(),
                categories=get_cats(),
                max_date=current_date)


####### METHOD TO ADD A NEW RECCURING EXPENSE #######
@expense_bp.route('/add_rec_exp',methods=["POST"])
def add_rec_exp(): 
    user_id=curr_user
    family_id=curr_family_id
    category=request.form.get('category')
    #print("Category being queried:", category)

    cursor.execute("SELECT category_id FROM categories WHERE name=%s",(category,))
    res=cursor.fetchone()
    category_id=res[0]
    
    date_in=request.form.get('date')
    
    amount=request.form.get('amount')
    
    desc=request.form.get('desc')
    
    cursor.execute("INSERT INTO rec_expenses (user_id,family_id,category_id,date,amount,description) VALUES (%s,%s,%s,%s,%s,%s) ",(user_id,family_id,category_id,date_in,amount,desc,))
    connect_.commit()
    
    ###### ADD { user_role=curr_user_role,user_name=curr_user_name } WHILE INTGRATING 
    return render_template('index.html',expenses=get_expenses(),user_id=curr_user,users=get_users(),major=verify_major(),
                reccur_exps=get_rec_exps(),
                categories=get_cats(),
                max_date=current_date)


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
    ###### ADD { user_role=curr_user_role,user_name=curr_user_name } WHILE INTGRATING 
    return render_template('index.html',expenses=get_expenses(),user_id=curr_user,users=get_users(),major=verify_major(),
                reccur_exps=get_rec_exps(),
                categories=get_cats(),
                max_date=current_date,summary=summary_)

if __name__=="__main__":
    app.run(debug=True)