import mysql.connector
from datetime import datetime 
from flask import Flask,request,render_template,jsonify,redirect,url_for,Blueprint
import os,time
from werkzeug.utils import secure_filename
from db_connection import get_connection

## initializing the flask application
app=Flask(__name__)


expense_bp = Blueprint('expense', __name__, template_folder='templates', static_folder='static')


########## DEFINING A PATH TO SAVE THE UPLOADED FILES ##########
# UPLOAD_FOLDER = './static/uploads/receipts'
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# sort_order={'date':'default',
#             'name':'default',
#             'amount':'default',
#             'description':'default',
#             'receipt':'default'}



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


# #configuring the connect_ with the database
# db_config={
#     'host':'localhost',
#     'user':'root',
#     'password':'$9Gamb@098',
#     'database':'project_ufft',
#     'port':3306
# }

# #establishing a conenction with the database using the configuration
# connect_=mysql.connector.connect(**db_config)
# cursor=connect_.cursor()

#establishing a conenction with the database using the configuration
connect_=get_connection()
#cursor=connect_.cursor()
cursor = connect_.cursor(buffered=True)



########### ESTABLISHING A ROUTE FOR THE HTML REQUEST ##########
@expense_bp.route('/', methods=["GET", "POST"])
def index():
    global current_date
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    # Fetching users data
    try:
        cursor.execute("SELECT user_id, user_name, family_id FROM users")
        users_list = cursor.fetchall()
        
        users = [
            {
                'user_id': user[0],
                'user_name': user[1],
                'family_id': user[2]
            } for user in users_list
        ]
    except mysql.connector.Error as err:
        print(f"Error fetching users: {err}")
        users = []

    if request.method == "GET":
        return render_template('index.html', users=users, max_date=current_date)
    else:
        global curr_user
        curr_user = request.form.get('user_id')
        
        # Fetch expenses for the user
        try:
            cursor.execute("""
                SELECT expense_id, date, name, amount, description, receipt 
                FROM expenses e1 
                JOIN categories c1 ON e1.category_id = c1.category_id 
                WHERE user_id=%s 
                ORDER BY expense_id DESC
            """, (curr_user,))
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

        # Fetch recurring expenses
        try:
            cursor.execute("SELECT rec_id, description, amount, user_id FROM recc_expenses WHERE user_id=%s",(curr_user,))
            recs = cursor.fetchall()
            
            rec_exps = [
                {
                    'rec_id': exp[0],
                    'description': exp[1],
                    'amount': exp[2],
                    'user_id': exp[3]
                }
                for exp in recs
            ]
        except mysql.connector.Error as err:
            print(f"Error fetching recurring expenses: {err}")
            rec_exps = []

        # Fetch all categories
        try:
            cursor.execute("SELECT * FROM categories")
            cats = cursor.fetchall()
            
            categories = [
                {
                    'cat_id': item[0],
                    'cat_name': item[1]
                }
                for item in cats
            ]
        except mysql.connector.Error as err:
            print(f"Error fetching categories: {err}")
            categories = []

        return render_template(
            'index.html',
            expenses=expense_records,
            user_id=curr_user,
            users=users,
            reccur_exps=rec_exps,
            categories=categories,
            max_date=current_date
        )

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
    
    user_id=1
    
    family_id=1
    
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
    add_expense(family_id, category_id, amount, date_in, description, receipt)
    
    
    return render_template('index.html',expenses=get_expenses(),users=get_users(),max_date=current_date) ##### this returns a success message 


####### ADD EXPENSE ###########
def add_expense(family_id, category_id, amount, date_in, description="", receipt=""):
    # Start constructing the query
    query = "INSERT INTO EXPENSES (user_id, category_id, date, amount, family_id"
    params = [curr_user, category_id, date_in, amount, family_id]
    
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
 

deleted_expenses = {}
undo_timeout = 10 
   
########## DELETE EXPENSE  #######
@expense_bp.route('/delete_expense/<int:expense_id>', methods=['POST'])
def delete_expense(expense_id):
    # Delete the expense from the database
    print("called in app")
    cursor.execute(" DELETE FROM expenses WHERE expense_id = %s", (expense_id,))
    connect_.commit()
    return render_template('index.html',expenses=get_expenses(),users=get_users(),max_date=current_date)

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
    return render_template('index.html',expenses=get_expenses(),users=get_users(),max_date=current_date)
           

###### ADD AMOUNT #####    
@expense_bp.route('/add_amount/<int:expense_id>',methods=["POST"])
def add_amount(expense_id):
    cursor.execute("SELECT amount FROM expenses WHERE expense_id=%s",(expense_id,))
    old_amount=cursor.fetchone()[0]
    
    new_amount=request.form.get('add_amount')
    sum=float(new_amount)+float(old_amount)
    
    cursor.execute("UPDATE expenses SET amount=%s WHERE expense_id=%s",(sum,expense_id,))
    connect_.commit()
    return render_template('index.html',expenses=get_expenses(),users=get_users(),max_date=current_date)


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

    # Render the filtered data
    current_date = datetime.now().strftime('%Y-%m-%d')
    return render_template('index.html', expenses=filtered_expenses_list, max_date=current_date)



###### route to reset the view ########
@expense_bp.route('/reset_filters')
def reset_filters():
    # Redirect to the root route, where the unfiltered data is displayed
    return redirect(url_for('expense.index'))


###### Sorting function ##
@expense_bp.route('/sort_table/<sort_by>')
def sort_table(sort_by):
    query="SELECT e.expense_id,e.date,c.name,e.amount,e.description,e.receipt FROM expenses e JOIN categories c ON e.category_id = c.category_id WHERE user_id=%s "
    print(sort_by,sort_order[sort_by])
    if sort_order[sort_by]=="default":
        sort_order[sort_by]='asc'
        query+=" ORDER BY %s ASC"
    
    elif sort_order[sort_by]=='asc':
        sort_order[sort_by]='desc'
        query+=" ORDER BY %s DESC"
    else:
        sort_order[sort_by]='default'
        return redirect('/')
        
    cursor.execute(query,(curr_user,sort_by,))
    sorted_expenses=cursor.fetchall() 
    cursor.reset()
    expenses = [
        {
            'expense_id': exp[0],
            'date_in': exp[1],
            'category': exp[2],
            'amount': exp[3],
            'desc': exp[4],
            'receipt': exp[5],
        }
        for exp in sorted_expenses
    ]
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    return render_template('index.html', expenses=expenses, max_date=current_date)
        
######## ADD RECCURRING EXPENSE TO THE EXPENSES #########
@expense_bp.route('/add_rec_to_exp/<int:rec_id>',methods=["POST"])
def add_rec_to_exp(rec_id):
    cursor.execute("SELECT user_id, family_id, amount, category_id,description,receipt,date FROM rec_expenses where rec_id=%s ",(rec_id,))
    params=cursor.fetchone()
    params=list(params)
    params[-1]=request.form.get('date')
    cursor.execute("INSERT INTO expenses (user_id, family_id, amount, category_id,description,receipt,date) VALUES (%s,%s,%s,%s,%s,%s,%s)",(tuple(params)))
    connect_.commit()  
    return render_template('index.html',expenses=get_expenses(),users=get_users(),max_date=current_date)


####### METHOD TO ADD A NEW RECCURING EXPENSE #######
@expense_bp.route('/add_rec_exp',methods=["POST"])
def add_rec_exp(): 
    user_id=1
    family_id=1   
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
    
    return render_template('index.html',expenses=get_expenses(),users=get_users(),max_date=current_date)


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
    return render_template('index.html',summary=summary_,expenses=get_expenses(),users=get_users(),max_date=current_date,method="POST")

if __name__=="__main__":
    app.run(debug=True)
