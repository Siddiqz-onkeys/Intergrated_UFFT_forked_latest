import mysql.connector
from datetime import datetime 
from flask import Flask,request,render_template,jsonify,redirect,url_for
import os,time
from werkzeug.utils import secure_filename
from threading import Timer


## initializing the flask application
app=Flask(__name__)


########## DEFINING A PATH TO SAVE THE UPLOADED FILES ##########
UPLOAD_FOLDER = 'static/uploads/receipts'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
sort_order={'date':'default',
            'name':'default',
            'amount':'default',
            'description':'default',
            'receipt':'default'}


#configuring the connect_ with the database
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


########### ESTABLISHING A ROUTE FOR THE HTML REQUEST ##########
@app.route('/',methods=["GET",'POST']) #creates a root route for the flask application
 #index function that returnrs the HTML content from the file and sends it to the user as a response for accessing the root URL
def index():
    global current_date
    current_date = datetime.now().strftime('%Y-%m-%d')
    ######### fetching users data ########
    cursor.execute("SELECT user_id,user_name,family_id FROM users")
    users_list=cursor.fetchall()
    
    users=[
        {
            'user_id': user[0],
            'user_name':user[1],
            'family_id': user[2]
            
        } for user in users_list
    ]
    
    if request.method=="GET":
        return render_template('index.html',users=users,max_date=current_date)
    else:
        global curr_user
        curr_user = request.form.get('user_id')
        # Fetch expenses for the user
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

        # Fetch recurring expenses
        cursor.execute("SELECT rec_id, description, amount, user_id FROM recc_expenses")
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
        return render_template('index.html',expenses=expense_records,user_id=curr_user,users=users,
                reccur_exps=rec_exps,
                categories=categories,
                max_date=current_date) #Flask by default looks for templkate forlder to render the html file


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
@app.route('/upload_receipt', methods=['POST'])
def upload_receipt():
    file = request.files['file']
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return render_template('index.html',expenses=get_expenses(),users=get_users(),max_date=current_date)


###### getting the form data and calling the add expense function
@app.route('/get_form_data',methods=['POST'])
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

   
 
deleted_cache = {}
undo_timeout = 10

######### AGE VERIFICATION ############
@app.route('/verify_major', methods=["GET"])
def verify_major():
    cursor.execute("SELECT dob FROM users WHERE user_id=%s", (curr_user,))
    dob = cursor.fetchone()[0]
    current_day = datetime.today()

    age = abs(dob.year - current_day.year)
    if (current_day.month, current_day.day) < (dob.month, dob.day):
        age -= 1

    is_major = age > 18
    return jsonify({"is_major": is_major})

########## DELETE EXPENSE WITH AGE VERIFICATION ##########
@app.route('/delete_expense/<int:expense_id>', methods=["POST"])
def delete_expense(expense_id):
    # Verify if the user is a major
    cursor.execute("SELECT dob FROM users WHERE user_id=%s", (curr_user,))
    dob = cursor.fetchone()[0]
    current_day = datetime.today()

    age = abs(dob.year - current_day.year)
    if (current_day.month, current_day.day) < (dob.month, dob.day):
        age -= 1

    if age > 18:
        # Fetch the expense to delete
        cursor.execute("SELECT * FROM expenses WHERE expense_id=%s", (expense_id,))
        expense = cursor.fetchone()

        if expense:
            # Store the deleted expense in the cache
            deleted_cache[expense_id] = expense

            # Start a timer to permanently delete the expense after 4 seconds
            Timer(4.0, permanently_delete_expense, [expense_id]).start()

            # Delete the expense from the database
            cursor.execute("DELETE FROM expenses WHERE expense_id=%s", (expense_id,))
            connect_.commit()

            return jsonify({"message": "Expense deleted. Rollback available for 4 seconds."})
        else:
            return jsonify({"error": "Expense not found."})
    else:
        return jsonify({"error": "User is not a major and cannot delete expenses."})

########## PERMANENTLY DELETE EXPENSE ##########
def permanently_delete_expense(expense_id):
    # Remove the expense from the cache after 4 seconds
    if expense_id in deleted_cache:
        del deleted_cache[expense_id]

########## ROLLBACK DELETION ##########
@app.route('/rollback_deletion/<int:expense_id>', methods=["POST"])
def rollback_deletion(expense_id):
    # Check if the expense is in the cache
    if expense_id in deleted_cache:
        # Restore the expense to the database
        expense = deleted_cache.pop(expense_id)
        cursor.execute(
            "INSERT INTO expenses (expense_id, date_in, category, amount, desc) VALUES (%s, %s, %s, %s, %s)",
            expense
        )
        connect_.commit()
        return jsonify({"message": "Rollback successful."})
    else:
        return jsonify({"error": "Rollback window expired or expense already permanently deleted."})

############ EDIT EXPENSE #######
@app.route('/edit_expense/<int:expense_id>', methods=["POST"])
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
@app.route('/add_amount/<int:expense_id>',methods=["POST"])
def add_amount(expense_id):
    cursor.execute("SELECT amount FROM expenses WHERE expense_id=%s",(expense_id,))
    old_amount=cursor.fetchone()[0]
    
    new_amount=request.form.get('add_amount')
    sum=float(new_amount)+float(old_amount)
    
    cursor.execute("UPDATE expenses SET amount=%s WHERE expense_id=%s",(sum,expense_id,))
    connect_.commit()
    return render_template('index.html',expenses=get_expenses(),users=get_users(),max_date=current_date)


@app.route('/filter_expenses', methods=["GET"])
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
        query+="c.name=%s AND"
        params+=[category]
    if min_amount and max_amount:
        query+=" e.amount BETWEEN %s AND %s AND"
        params+=[min_amount,max_amount]
    elif min_amount:
        query+=" e.amount>=%s AND"
        params+=[min_amount]
    elif max_amount:
        query+=" e.amount<%s AND"
        params+=[max_amount]
        
    if desc:
        query+=" e.description IS NOT NULL AND"
    if receipt:
        query+=" e.receipt IS NOT NULL AND"
        

    query=query[:-4]
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
    
    current_date = datetime.now().strftime('%Y-%m-%d')
    return render_template('index.html', expenses=filtered_expenses_list,max_date=current_date)


###### route to reset the view ########
@app.route('/reset_filters')
def reset_filters():
    # Redirect to the root route, where the unfiltered data is displayed
    return redirect('/')


###### Sorting function ##
@app.route('/sort_table/<sort_by>')
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
@app.route('/add_rec_to_exp/<int:rec_id>',methods=["POST"])
def add_rec_to_exp(rec_id):
    cursor.execute("SELECT user_id, family_id, amount, category_id,description,receipt,date FROM recc_expenses where rec_id=%s ",(rec_id,))
    params=cursor.fetchone()
    params=list(params)
    params[-1]=request.form.get('date')
    cursor.execute("INSERT INTO expenses (user_id, family_id, amount, category_id,description,receipt,date) VALUES (%s,%s,%s,%s,%s,%s,%s)",(tuple(params)))
    connect_.commit()  
    return render_template('index.html',expenses=get_expenses(),users=get_users(),max_date=current_date)


####### METHOD TO ADD A NEW RECCURING EXPENSE #######
@app.route('/add_rec_exp',methods=["POST"])
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
    
    cursor.execute("INSERT INTO recc_expenses (user_id,family_id,category_id,date,amount,description) VALUES (%s,%s,%s,%s,%s,%s) ",(user_id,family_id,category_id,date_in,amount,desc,))
    connect_.commit()
    
    return render_template('index.html',expenses=get_expenses(),users=get_users(),max_date=current_date)


if __name__=="__main__":
    app.run(debug=True)
