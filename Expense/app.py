import mysql.connector
from datetime import datetime 
from flask import Flask,request,render_template,jsonify,redirect,url_for,Blueprint
import os
from werkzeug.utils import secure_filename
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


# #configuring the connection with the database
# db_config={
#     'host':'localhost',
#     'user':'root',
#     'password':'$9Gamb@098',
#     'database':'project_ufft',
#     'port':3306
# }

#establishing a conenction with the database using the configuration
# connect_=mysql.connector.connect(**db_config)
connect_=get_connection()
cursor=connect_.cursor()



########### ESTABLISHING A ROUTE FOR THE HTML REQUEST ##########

@expense_bp.route('/') #creates a root route for the flask application
 #index function that returnrs the HTML content from the file and sends it to the user as a response for accessing the root URL
def index():
    
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    cursor.execute("SELECT expense_id,date,name,amount,description,receipt,user_id FROM expenses e1 JOIN categories c1 where e1.category_id=c1.category_id ORDER BY expense_id DESC")
    expenses=cursor.fetchall()
    
    expense_records=[
        {
            'expense_id':exp[0],
            'date_in':exp[1],
            'category':exp[2],            
            'amount':exp[3],
            'desc':exp[4],
            'receipt':exp[5],
            'user_id':exp[6]           
        }
        for exp in expenses
    ]
    
    return render_template('index.html', expenses=expense_records, max_date=current_date) #Flask by default looks for templkate forlder to render the html file


########## SAVING THE UPLOADED FILES IN A FOLDER ############
@expense_bp.route('/upload_receipt', methods=['POST'])
def upload_receipt():
    file = request.files['file']
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return redirect(url_for('expense.index'))


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
    add_expense(user_id, family_id, category_id, amount, date_in, description, receipt)
    
    return redirect(url_for('expense.index')) ##### this returns a success message 


####### ADD EXPENSE ###########
def add_expense(user_id, family_id, category_id, amount, date_in, description="", receipt=""):
    # Start constructing the query
    query = "INSERT INTO EXPENSES (user_id, category_id, date, amount, family_id"
    params = [user_id, category_id, date_in, amount, family_id]
    
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


@expense_bp.route('/verify_major/<int:user_id>',methods=["GET"])
def verify_major(user_id):
    cursor.execute("SELECT dob FROM users WHERE user_id=%s",(user_id,))
    dob=cursor.fetchone()[0]
    current_day=datetime.today()
    
    age=abs(dob.year-current_day.year)
    if (current_day.month, current_day.day) < (dob.month, dob.day):
        age -= 1
    
    is_major = age > 18
    return jsonify({"is_major": is_major})           
 
   
########## DELETE EXPENSE  #######
@expense_bp.route('/delete_expense/<int:expense_id>',methods=["GET"])
def delete_expense(expense_id):
    cursor.execute("DELETE FROM expenses WHERE expense_id=%s",(expense_id,))
    connect_.commit()
    return redirect(url_for('expense.index'))


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
    return redirect(url_for('expense.index'))
           

###### ADD AMOUNT #####    
@expense_bp.route('/add_amount/<int:expense_id>',methods=["POST"])
def add_amount(expense_id):
    cursor.execute("SELECT amount FROM expenses WHERE expense_id=%s",(expense_id,))
    old_amount=cursor.fetchone()[0]
    
    new_amount=request.form.get('add_amount')
    sum=float(new_amount)+float(old_amount)
    
    cursor.execute("UPDATE expenses SET amount=%s WHERE expense_id=%s",(sum,expense_id,))
    connect_.commit()
    return redirect(url_for('expense.index'))




@expense_bp.route('/filter_expenses', methods=["GET"])
def filter_expenses():
    min_amount = request.args.get('filter_amount_range_min')  # Minimum amount input from the frontend
    max_amount = request.args.get('filter_amount_range_max')  # Maximum amount input from the frontend
    category = request.args.get('filter_category')  # Category input from the frontend
    desc=request.args.get('description') # Description
    receipt=request.args.get('receipt') #receipt   

    # Initialize base query and parameters
    query = "SELECT e.expense_id,e.date,c.name,e.amount,e.description,e.receipt FROM expenses e JOIN categories c ON e.category_id = c.category_id WHERE "
    params = []
    
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
    return render_template('index.html', expenses=filtered_expenses_list, max_date=current_date)

###### route to reset the view ########
@expense_bp.route('/reset_filters')
def reset_filters():
    # Redirect to the root route, where the unfiltered data is displayed
    return redirect('/')


###### Sorting function ##
@expense_bp.route('/sort_table/<sort_by>')
def sort_table(sort_by):
    query="SELECT e.expense_id,e.date,c.name,e.amount,e.description,e.receipt FROM expenses e JOIN categories c ON e.category_id = c.category_id"
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
        
    cursor.execute(query,(sort_by,))
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
        

if __name__=="__main__":
    app.run(debug=True)
