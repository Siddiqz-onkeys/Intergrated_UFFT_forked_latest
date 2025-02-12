
from flask import Blueprint, render_template, request, redirect, flash, current_app,url_for,session
from datetime import datetime
from werkzeug.utils import secure_filename
from flask_mail import Message
from apscheduler.schedulers.background import BackgroundScheduler
import mysql.connector
from db_connection import get_connection
from flask_mail import Mail, Message


# # Database configuration
# DB_HOST = "localhost"
# DB_USER = "root"
# DB_PASSWORD = "Krishna1919@"
# DB_NAME = "projectufft"

# def get_db_connection():
#     """Establish and return a database connection."""
#     return mysql.connector.connect(
#         host=DB_HOST,
#         user=DB_USER,
#         password=DB_PASSWORD,
#         database=DB_NAME
#     )


 
def allowed_file(filename):
    """Check if the uploaded file is allowed based on extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'pdf'}

def send_alert_email(user_mail,name, total_expenses,category_budget_amount):
        """Send an alert email to the user when budget threshold is exceeded."""
        mail = current_app.extensions['mail']  # Use the current app's mail instance
        subject = f"Category Budget Alert: {name} Budget Exceeded"
        body = f"""
        Dear User,

        Your expenses for the category '{name}' have exceeded the budget amount.
        
        Total Expenses: ₹{total_expenses}
        Budget Amount: ₹{category_budget_amount}
        
        Please review your spending.
        
         
        """
        message = Message(subject=subject, recipients=[user_mail], body=body)

        try:
            mail.send(message)
            print("Email sent successfully!")
        except Exception as e:
            print(f"Error sending email: {e}")
        


def send_user_alert_email(user_email, total_expenses, user_budget):
    """Send an alert email to the user when budget for user is exceeded."""
    mail = current_app.extensions['mail']  # Use the current app's mail instance
    subject = f" User Budget Alert: User budget Exceeded"
    body = f"""
    Dear User,

    Alert! Your total expenses have exceeded your personal budget.
    
    Total Expenses: ₹{total_expenses}
    User Budget Amount: ₹{user_budget}
    
    Please review your spending.
     
    """
    message = Message(subject=subject, recipients=[user_email], body=body)

    try:
        mail.send(message)
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")
        
        
def send_budget_limit_email(user_email, total_expenses, budget_amount):
    subject = "User Budget Limit Reached"
    body = f"""
    Dear User,

    You have reached your Perosnal budget  of ₹{budget_amount}.
    
    Total Expenses: ₹{total_expenses}
    
    Please plan your expenses wisely.

     
    """
    send_email(user_email, subject, body)

def send_threshold_alert_email(user_email, total_expenses, threshold_value,user_budget):
    subject = "User Threshold Alert: Personal Expense Limit Exceeded"
    body = f"""
    Dear User,

    Alert! Your total expenses have exceeded your set threshold limit.
    
    Total Expenses: ₹{total_expenses}
    Your Budget Amount:₹{user_budget}
    Your Threshold Limit: ₹{threshold_value}
    
    Please review your spending.
    
  
    """
    send_email(user_email, subject, body)

def send_category_budget_limit_email(user_email, category_name, total_expenses, category_budget_amount):
    subject = f"Category Budget Limit Reached: {category_name}"
    body = f"""
    Dear User,

    You have reached the budget limit for the category '{category_name}'.
    
    Total Expenses: ₹{total_expenses}
    Category Budget Amount: ₹{category_budget_amount}
    
    Please manage your expenses accordingly.
 
    """
    send_email(user_email, subject, body)


def send_category_threshold_alert_email(user_email, category_name, total_expenses, threshold_value,category_budget_amount):
    subject = f"Category Threshold Exceeded: {category_name}"
    body = f"""
    Dear User,

    Your expenses for the category '{category_name}' have exceeded the threshold limit.
    
    Total Expenses: ₹{total_expenses}
    Budget Amount:₹{category_budget_amount}
    Threshold Limit: ₹{threshold_value}
    
    Please review your spending.
 
    """
    send_email(user_email, subject, body)

def send_email(user_email, subject, body):
    try:
        mail = current_app.extensions['mail']
        message = Message(subject=subject, recipients=[user_email], body=body)
        mail.send(message)
        print(f"Email sent: {subject}")
    except Exception as e:
        print(f"Error sending email: {e}")




# Blueprint definition
budget_bp = Blueprint('budget', __name__, template_folder='templates', static_folder='static')

# Budget routes
@budget_bp.route('/')
def home():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    # Get the logged-in user's username
    logged_in_user_name = session.get('user_name') or session.get('login_name')

    if not logged_in_user_name:
        flash("Please log in first.", "warning")
        return redirect(url_for('user_reg.signin'))

    # Fetch user details (role and family_id)
    cursor.execute('SELECT role, family_id FROM users WHERE user_name = %s', (logged_in_user_name,))
    user = cursor.fetchone()

    if not user:
        flash("User not found!", "error")
        return redirect(url_for('user_reg.signin'))

    user_role = user['role']
    family_id = user['family_id']  # Get the user's family_id

    # Fetch category budgets that belong to the user's family
    cursor.execute('''
        SELECT budgets.*, categories.name 
        FROM budgets
        INNER JOIN categories ON budgets.category_id = categories.category_id
        WHERE budgets.family_id = %s
    ''', (family_id,))
    category_budgets = cursor.fetchall()

    # Fetch user budgets that belong to the same family
    cursor.execute('''
        SELECT budgets.*, users.user_name AS name
        FROM budgets
        INNER JOIN users ON budgets.user_id = users.user_id
        WHERE budgets.family_id = %s
    ''', (family_id,))
    user_budgets = cursor.fetchall()

    connection.close()

    return render_template('home2.html', 
                           category_budgets=category_budgets, 
                           user_budgets=user_budgets, 
                           user_role=user_role)


@budget_bp.route('/add_category', methods=['GET', 'POST'])
def add_category():
    if request.method == 'POST':
        name = request.form['name']
        
        if not name.strip():
            flash('Category name cannot be empty!', 'danger')
        else:
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute('INSERT INTO categories (name) VALUES (%s)', (name,))
            connection.commit()
            connection.close()

            flash('Category added successfully!', 'success')

        return redirect(url_for('budget.add_category'))  # Redirects to same page

    return render_template('add_category.html')
@budget_bp.route('/add_budget', methods=['GET', 'POST'])
def add_budget():
    # Fetch the logged-in user's details
    logged_in_user_name = session.get('user_name') or session.get('login_name')
    if not logged_in_user_name:
        flash('You must be logged in to add a budget.', 'error')
        return redirect(url_for('user_reg.signin'))

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    # Get the family_id of the logged-in user
    cursor.execute('SELECT user_id, family_id FROM users WHERE user_name = %s', (logged_in_user_name,))
    user = cursor.fetchone()
    if not user:
        flash('User not found in the database.', 'error')
        connection.close()
        return redirect(url_for('user_reg.signin'))

    user_id = user['user_id']
    family_id = user['family_id']

    if request.method == 'POST':
        budget_type = request.form['budget_type']  # 'category' or 'user'
        amount = request.form['amount']
        threshold_value = request.form['threshold_value']
        recurring = bool(int(request.form['recurring']))
        start_date = request.form['start_date']
        end_date = request.form['end_date']

        if budget_type == 'category':
            category_id = request.form.get('category_id')
            if not category_id:
                flash('Category is required for a Category Budget!', 'danger')
            else:
                # Check if the same category budget exists for this family
                cursor.execute('SELECT 1 FROM budgets WHERE category_id = %s AND family_id = %s', (category_id, family_id))
                existing_budget = cursor.fetchone()
                
                if existing_budget:
                    flash('A budget for this category already exists in your family. You cannot add it again.', 'warning')
                else:
                    cursor.execute('''
                        INSERT INTO budgets (category_id, amount, start_date, end_date, recurring, threshold_value, user_id, family_id) 
                        VALUES (%s, %s, %s, %s, %s, %s, NULL, %s)
                    ''', (category_id, amount, start_date, end_date, recurring, threshold_value, family_id))
                    flash('Category budget added successfully!', 'success')

        elif budget_type == 'user':
            selected_user_id = request.form.get('user_id')
            if not selected_user_id:
                flash('User selection is required for a User Budget!', 'danger')
            else:
                # Check if the user already has a budget in the family
                cursor.execute('SELECT 1 FROM budgets WHERE user_id = %s AND family_id = %s', (selected_user_id, family_id))
                existing_user_budget = cursor.fetchone()
                
                if existing_user_budget:
                    flash('A budget for this user already exists in your family. You cannot add it again.', 'warning')
                else:
                    cursor.execute('''
                        INSERT INTO budgets (user_id, amount, start_date, end_date, recurring, threshold_value, category_id, family_id) 
                        VALUES (%s, %s, %s, %s, %s, %s, NULL, %s)
                    ''', (selected_user_id, amount, start_date, end_date, recurring, threshold_value, family_id))
                    flash('User budget added successfully!', 'success')

        connection.commit()
        connection.close()
        return redirect(url_for('budget.add_budget'))  # Redirect after form submission

    # Fetch updated categories and users with correct filtering
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute('SELECT * FROM categories')
    categories = cursor.fetchall()

    cursor.execute('SELECT user_id, name FROM users WHERE family_id = %s', (family_id,))  # Fetch only users in the same family
    users = cursor.fetchall()

    connection.close()

    return render_template('add_budget.html', categories=categories, users=users)



@budget_bp.route('/edit_budget/<int:id>', methods=['GET', 'POST'])

def edit_budget(id):
    budget_type = request.args.get('budget_type', 'category')
    
    # connection = get_db_connection()
    connection=get_connection()
    cursor = connection.cursor(dictionary=True)
    
    # Fetch the appropriate budget based on the type (category or user)
    if budget_type == 'category':
        cursor.execute('SELECT * FROM budgets WHERE budget_id = %s', (id,))
    else:
        cursor.execute('''
            SELECT budgets.*, users.user_name AS name
            FROM budgets
            INNER JOIN users ON budgets.user_id = users.user_id
            WHERE budget_id = %s
        ''', (id,))
    
    budget = cursor.fetchone()
    
    if not budget:
        flash('Budget not found!', 'danger')
        return redirect(url_for('budget.edit_budget', id=id, budget_type=budget_type))

    if request.method == 'POST':
        # Get updated fields
        amount = request.form['amount']
        threshold_value = request.form['threshold_value']
        recurring = bool(int(request.form['recurring']))
        start_date = request.form['start_date']
        end_date = request.form['end_date']

        # Update the budget in the database
        if budget_type == 'category':
            category_id = request.form['category_id']
            cursor.execute(''' 
                UPDATE budgets 
                SET category_id = %s, amount = %s, threshold_value = %s, recurring = %s, start_date = %s, end_date = %s 
                WHERE budget_id = %s
            ''', (category_id, amount, threshold_value, recurring, start_date, end_date, id))
        else:
            user_id = request.form['user_id']
            cursor.execute(''' 
                UPDATE budgets 
                SET user_id = %s, amount = %s, threshold_value = %s, recurring = %s, start_date = %s, end_date = %s 
                WHERE budget_id = %s
            ''', (user_id, amount, threshold_value, recurring, start_date, end_date, id))

        connection.commit()
        connection.close()

        flash('Budget updated successfully!', 'success')
        return redirect(url_for('budget.edit_budget', id=id, budget_type=budget_type))
    # Fetch categories or users for the dropdown
    if budget_type == 'category':
        cursor.execute('SELECT * FROM categories')
        dropdown = cursor.fetchall()
    else:
        cursor.execute('SELECT * FROM users')
        dropdown = cursor.fetchall()

    connection.close()
    return render_template('edit_budget.html', budget=budget, dropdown=dropdown, budget_type=budget_type)

@budget_bp.route('/expenses', methods=['GET', 'POST'])
def expenses():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True, buffered=True)
    
    logged_in_user_name = session.get('user_name') or session.get('login_name')

    if not logged_in_user_name:
        flash('User not found in session!', 'error')
        connection.close()
        return redirect(url_for('user_reg.signin'))

    # Fetch the logged-in user's details
    cursor.execute('SELECT user_id, family_id FROM users WHERE user_name = %s', (logged_in_user_name,))
    user = cursor.fetchone()

    user_id = user['user_id']
    family_id = user['family_id']

    if request.method == 'POST':
        description = request.form['description']
        amount = float(request.form['amount'])
        date = request.form['date']
        category_id = int(request.form['category_id'])

        # Fetch user email
        cursor.execute('SELECT email FROM users WHERE user_id = %s', (user_id,))
        user_email = cursor.fetchone()['email']

        # Insert the new expense
        cursor.execute('''
            INSERT INTO expenses (user_id, description, amount, date, category_id, family_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (user_id, description, amount, date, category_id, family_id))
        connection.commit()

        # Calculate total expenses **for this user in their family**
        cursor.execute('''
            SELECT SUM(amount) AS total_expenses
            FROM expenses
            WHERE user_id = %s AND family_id = %s
        ''', (user_id, family_id))
        total_expenses = cursor.fetchone()['total_expenses'] or 0

        # Fetch user-specific budget and threshold **in their family**
        cursor.execute('''
            SELECT amount, threshold_value 
            FROM budgets 
            WHERE user_id = %s AND family_id = %s
        ''', (user_id, family_id))
        budget_data = cursor.fetchone()

        if budget_data:
            user_budget = budget_data['amount']
            user_threshold = budget_data['threshold_value']

            # Send budget-related alerts
            if total_expenses > user_budget:
                send_user_alert_email(user_email, total_expenses, user_budget)
            elif total_expenses == user_budget:
                send_budget_limit_email(user_email, total_expenses, user_budget)
            elif total_expenses > user_threshold:
                send_threshold_alert_email(user_email, total_expenses, user_threshold, user_budget)

        # Calculate category total expenses **for this category in this family**
        cursor.execute('''
            SELECT SUM(amount) AS category_total_expenses
            FROM expenses
            WHERE category_id = %s AND family_id = %s
        ''', (category_id, family_id))
        category_total_expenses = cursor.fetchone()['category_total_expenses'] or 0

        # Fetch category budget and threshold **for this family only**
        cursor.execute('''
            SELECT amount, threshold_value, categories.name AS category_name
            FROM budgets
            INNER JOIN categories ON budgets.category_id = categories.category_id
            WHERE budgets.category_id = %s AND budgets.family_id = %s
        ''', (category_id, family_id))
        category_budget = cursor.fetchone()

        if category_budget:
            category_budget_amount = category_budget['amount']
            category_threshold = category_budget['threshold_value']
            category_name = category_budget['category_name']

            # Send category budget alerts
            if category_total_expenses > category_budget_amount:
                send_alert_email(user_email, category_name, category_total_expenses, category_budget_amount)
            elif category_total_expenses == category_budget_amount:
                send_category_budget_limit_email(user_email, category_name, category_total_expenses, category_budget_amount)
            elif category_total_expenses > category_threshold:
                send_category_threshold_alert_email(user_email, category_name, category_total_expenses, category_threshold, category_budget_amount)

        flash('Expense added successfully!', 'success')
        connection.close()
        return redirect('/budget/expenses')

    # Fetch only categories available to this family from the budgets table
    cursor.execute('''
        SELECT DISTINCT categories.category_id, categories.name 
        FROM budgets
        INNER JOIN categories ON budgets.category_id = categories.category_id
        WHERE budgets.family_id = %s
    ''', (family_id,))
    categories = cursor.fetchall()

    # Fetch user total expenses **for their family**
    cursor.execute('''
        SELECT SUM(amount) AS total_expenses
        FROM expenses
        WHERE user_id = %s AND family_id = %s
    ''', (user_id, family_id))
    total_expenses = cursor.fetchone()['total_expenses'] or 0

    # Fetch user budget **for their family**
    cursor.execute('SELECT amount FROM budgets WHERE user_id = %s AND family_id = %s', (user_id, family_id))
    user_budget = cursor.fetchone()
    user_budget = user_budget['amount'] if user_budget else 0

    connection.close()

    return render_template('expenses.html', categories=categories, user_budget=user_budget, total_expenses=total_expenses)




@budget_bp.route('/report')
def report():
    # Get report type from query parameters 
    report_type = request.args.get('report_type', 'category')
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    report_data = []

    # Get the logged-in user's username
    logged_in_user_name = session.get('user_name') or session.get('login_name')

    if not logged_in_user_name:
        flash("Please log in first.", "warning")
        return redirect(url_for('user_reg.signin'))

    # Fetch user details (role and family_id)
    cursor.execute('SELECT role, family_id FROM users WHERE user_name = %s', (logged_in_user_name,))
    user = cursor.fetchone()

    if not user:
        flash("User not found!", "error")
        return redirect(url_for('user_reg.signin'))

    family_id = user['family_id']

    if report_type == 'category':
        # Fetch Category Budgets for the user's family
        cursor.execute('''
            SELECT 
                budgets.category_id,
                budgets.amount AS budget_amount,
                budgets.threshold_value,
                categories.name
            FROM 
                budgets
            INNER JOIN 
                categories 
            ON 
                budgets.category_id = categories.category_id
            WHERE 
                budgets.family_id = %s
        ''', (family_id,))
        budgets = cursor.fetchall()

        # Calculate total expenses for each category
        cursor.execute('''
            SELECT 
                category_id,
                SUM(amount) AS total_expenses
            FROM 
                expenses
            WHERE 
                family_id = %s
            GROUP BY 
                category_id
        ''', (family_id,))
        expenses = cursor.fetchall()

        # Map expenses to categories
        expenses_dict = {expense['category_id']: expense['total_expenses'] for expense in expenses}

        # Prepare category report data
        for budget in budgets:
            category_id = budget['category_id']
            total_expenses = expenses_dict.get(category_id, 0)
            remaining = float(budget['budget_amount']) - total_expenses

            report_data.append({
                'name': budget['name'],
                'budget_amount': budget['budget_amount'],
                'threshold_value': budget['threshold_value'],
                'total_expenses': total_expenses,
                'remaining': remaining
            })

    elif report_type == 'user':
        # Fetch User Budgets for the user's family
        cursor.execute('''
            SELECT 
                budgets.user_id,
                budgets.amount AS budget_amount,
                budgets.threshold_value,
                users.user_name AS name
            FROM 
                budgets
            INNER JOIN 
                users 
            ON 
                budgets.user_id = users.user_id
            WHERE 
                budgets.family_id = %s
        ''', (family_id,))
        budgets = cursor.fetchall()

        # Calculate total expenses for each user
        cursor.execute('''
            SELECT 
                user_id,
                SUM(amount) AS total_expenses
            FROM 
                expenses
            WHERE 
                family_id = %s
            GROUP BY 
                user_id
        ''', (family_id,))
        expenses = cursor.fetchall()

        # Map expenses to users
        expenses_dict = {expense['user_id']: expense['total_expenses'] for expense in expenses}

        # Prepare user report data
        for budget in budgets:
            user_id = budget['user_id']
            total_expenses = expenses_dict.get(user_id, 0)
            remaining = float(budget['budget_amount']) - total_expenses

            report_data.append({
                'name': budget['name'],
                'budget_amount': budget['budget_amount'],
                'threshold_value': budget['threshold_value'],
                'total_expenses': total_expenses,
                'remaining': remaining
            })

    connection.close()

    # Render the report template
    return render_template(
        'report.html',
        report_data=report_data,
        report_type=report_type
    )

@budget_bp.route('/request_budget', methods=['GET', 'POST'])
def request_budget():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    # Get the logged-in user's user_name from the session
    logged_in_user_name = session.get('user_name') or session.get('login_name')

    # Fetch user_id using user_name
    cursor.execute('SELECT user_id FROM users WHERE user_name = %s', (logged_in_user_name,))
    user_data = cursor.fetchone()

    if not user_data:
        flash('User not found!', 'error')
        connection.close()
        return redirect('/request_budget')

    logged_in_user_id = user_data['user_id']  # Now we have user_id

    if request.method == 'POST':
        user_id = logged_in_user_id  # Automatically set the user_id to the logged-in user
        requested_amount = float(request.form['requested_amount'])
        reason = request.form['reason']

        # Fetch the family_id and user_name of the logged-in user
        cursor.execute('SELECT family_id, user_name FROM users WHERE user_id = %s', (user_id,))
        user = cursor.fetchone()

        if not user:
            flash('User not found!', 'error')
            connection.close()
            return redirect('/request_budget')

        family_id = user['family_id']
        user_name = user['user_name']

        # Now search for the HOF (Head of Family) with the same family_id
        cursor.execute('SELECT email, user_name FROM users WHERE family_id = %s AND role = "HOF"', (family_id,))
        hof_user = cursor.fetchone()

        if hof_user:
            hof_email = hof_user['email']
            hof_name = hof_user['user_name']
            # Send an email to the HOF with Accept/Reject links
            subject = "Budget Request Alert"
            body = f"""
            Dear {hof_name},

            A budget request has been submitted by a family member.

            User Name: {user_name}
            Requested Amount: ₹{requested_amount}
            Reason: {reason}

            Please review and take the necessary action.
            To approve the request and add the requested amount to the user's budget, click here:
            {url_for('budget.approve_reject', user_id=user_id, action='accept', requested_amount=requested_amount, _external=True)}

            To reject the request, click here:
            {url_for('budget.approve_reject', user_id=user_id, action='reject', requested_amount=requested_amount, _external=True)}

            Regards,
            Budget Tracker Team
            """
            message = Message(subject=subject, recipients=[hof_email], body=body)
            try:
                mail = current_app.extensions['mail']
                mail.send(message)
                flash(' Your budget request has been submitted successfully!', 'success')
            except Exception as e:
                print(f"Error sending email: {e}")
                flash(' Failed to send email to the HOF.', 'danger')
        else:
            flash(' HOF not found for this family.', 'error')

        connection.close()
        return redirect(url_for('budget.request_budget'))

    # If the method is GET, render the template with the logged-in user's info pre-filled
    connection.close()
    return render_template('request_budget.html', logged_in_user_id=logged_in_user_id)





@budget_bp.route('/approve_reject/<int:user_id>/<string:action>', methods=['GET'])
def approve_reject(user_id, action):
    requested_amount = request.args.get('requested_amount', type=float)

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    # Fetch the user email and name
    cursor.execute('SELECT email, user_name FROM users WHERE user_id = %s', (user_id,))
    user = cursor.fetchone()

    if not user:
        flash('User not found!', 'danger')
        connection.close()
        return redirect('/budget')

    user_email = user['email']
    user_name = user['user_name']

    if action == 'accept':
        requested_amount = float(requested_amount)
        # Update the user's budget
        cursor.execute('''
            UPDATE budgets
            SET amount = amount + %s
            WHERE user_id = %s
        ''', (requested_amount, user_id))
        connection.commit()

        # Send an acceptance email
        subject = "Budget Request Accepted"
        body = f"""
        Dear {user_name},

        Your budget request of ₹{requested_amount} has been accepted and added to your budget.

        Regards,
        Budget Tracker Team
        """
    elif action == 'reject':
        # Send a rejection email
        subject = "Budget Request Rejected"
        body = f"""
        Dear {user_name},

        Unfortunately, your budget request of ₹{requested_amount} has been rejected.

        Regards,
        Budget Tracker Team
        """
    else:
        flash('Invalid action!', 'danger')
        connection.close()
        return redirect('/budget')

    # Send email notification
    message = Message(subject=subject, recipients=[user_email], body=body)
    try:
        mail = current_app.extensions['mail']
        mail.send(message)
        flash(f'Budget request {action}ed successfully and email sent to the user!', 'success')
    except Exception as e:
        print(f"Error sending email: {e}")
        flash('Failed to send email to the user.', 'danger')

    connection.close()
    return redirect('/budget')


 
 
@budget_bp.route('/delete_budget/<int:id>/<budget_type>', methods=['POST', 'GET'])
def delete_budget(id, budget_type):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        # Delete the budget from the budgets table
        cursor.execute("DELETE FROM budgets WHERE budget_id = %s", (id,))
        connection.commit()
        #flash("Budget deleted successfully!", "success")
    except Exception as e:
        connection.rollback()
       # flash("Error deleting budget: " , "error")
    finally:
        connection.close()

    return redirect(url_for('budget.home'))  # Redirect back to home page