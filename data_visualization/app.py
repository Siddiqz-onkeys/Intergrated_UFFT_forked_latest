from flask import Flask, render_template, request, jsonify,send_file,  redirect, url_for,request,Blueprint, session, make_response
import mysql.connector  
from datetime import datetime, timedelta
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from db_connection import get_connection
from collections import defaultdict



app = Flask(__name__)

data_visualization_bp = Blueprint('data_visualization', __name__, template_folder='templates', static_folder='static')


# # MySQL Database Configuration
# DB_CONFIG = {
#     'host': 'localhost',
#     'user': 'root',
#     'password': 'root',
#     'database': 'ProjectUFFT'
# }

# Use to store expanse data which is fetched from the filters 
Expense_data=[]



# Utility function to fetch database connection
def get_db_connection():
    #return mysql.connector.connect(**DB_CONFIG)
    return get_connection()

@data_visualization_bp.route('/', methods=['GET', 'POST'])
def index():
    if 'login_name' not in session:
        return redirect(url_for('user_reg.signin'))
    
    u_id = session['user_id']
    u_role = session['role'].lower()
    family_members = []
    expense_data = []
    category_totals = {}
    grouped_expenses = {}  # For grouping expenses by user
    selected_user_id = None
    search_query = ''
    time_range = ''
    start_date = ''
    end_date = ''
    family_id = session['family_id']  # Retrieve family_id from the session
    print(family_id)
    no_records = False  # Flag for no records
    success_message = False  # Default value for success message flag

    if family_id:
        # Fetch family members for the family ID stored in the session
        with get_db_connection() as connection:
            with connection.cursor(dictionary=True) as cursor:
                if u_role == "hof":
                    # HOF can select all family members
                    cursor.execute("SELECT user_id, name FROM users WHERE family_id = %s", (family_id,))
                    family_members = cursor.fetchall()
                else:
                    # Non-HOF users only see their own name
                    cursor.execute("SELECT user_id, name FROM users WHERE user_id = %s", (u_id,))
                    family_members = cursor.fetchall()

    if request.method == 'POST':
        Expense_data.clear()
        selected_user_id = request.form.get('user_id')
        search_query = request.form.get('search_query', '').strip()
        time_range = request.form.get('time_range')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')

        if family_members:
            user_ids = [member['user_id'] for member in family_members]

            if selected_user_id == "all" and u_role == "hof":
                selected_user_id = user_ids
            else:
                selected_user_id = [selected_user_id]

            query = """
                SELECT e.expense_id, e.user_id, u.name AS user_name, e.description, e.amount, c.name AS category_name, e.date
                FROM expenses e
                JOIN users u ON e.user_id = u.user_id
                JOIN categories c ON e.category_id = c.category_id
                WHERE e.family_id = %s AND e.user_id IN (%s)
            """
            query = query % ("%s", ",".join(['%s'] * len(selected_user_id)))
            params = [family_id] + selected_user_id

            if search_query:
                query += " AND e.description LIKE %s"
                params.append(f"%{search_query}%")

            if time_range == 'custom' and start_date and end_date:
                query += " AND e.date BETWEEN %s AND %s"
                params.extend([start_date, end_date])
            elif time_range == 'week':
                query += " AND e.date >= DATE_SUB(NOW(), INTERVAL 1 WEEK)"
            elif time_range == 'month':
                query += " AND e.date >= DATE_SUB(NOW(), INTERVAL 1 MONTH)"
            elif time_range == 'year':
                query += " AND e.date >= DATE_SUB(NOW(), INTERVAL 1 YEAR)"

            query += " ORDER BY e.date"

            with get_db_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    cursor.execute(query, params)
                    expense_data = cursor.fetchall()
                    Expense_data.append(expense_data)
                    
            # Group expenses by user_id for multiple pie charts
            grouped_expenses = {}
            for expense in expense_data:
                user_id = expense['user_id']
                user_name = expense['user_name']
                if user_id not in grouped_expenses:
                    grouped_expenses[user_id] = {'user_name': user_name, 'categories': {}}
                category = expense['category_name']
                amount = expense['amount']
                grouped_expenses[user_id]['categories'][category] = grouped_expenses[user_id]['categories'].get(category, 0) + amount

            # Check if no records were found
            no_records = len(expense_data) == 0

    if request.args.get('success_message') == 'success':
        success_message = True

    return render_template(
        'dv_index.html',
        u_role=u_role,
        u_id=u_id,
        family_members=family_members,
        expenses=expense_data,
        grouped_expenses=grouped_expenses,  # Send grouped data
        category_totals=category_totals,
        selected_user_id=selected_user_id,
        family_id=family_id,
        search_query=search_query,
        time_range=time_range,
        start_date=start_date,
        end_date=end_date,
        success_message=success_message,
        no_records=no_records  # Pass the flag to the template
    )



@data_visualization_bp.route('/download/csv')
def download_csv():
    # Prepare CSV data
    if not Expense_data:
        return "No matching expenses found.", 404
    
    
    expenses=Expense_data[0]
    data = {
    'Sr no': [idx + 1 for idx, _ in enumerate(expenses)], 
    'Category': [exp['category_name'] for exp in expenses],
    'Amount': [exp['amount'] for exp in expenses],
    'Date': [exp['date'].strftime("%d-%m-%Y") for exp in expenses],
    'Description': [exp['description'] or "N/A" for exp in expenses],
    'User Name': [exp['user_name'] for exp in expenses]
    }
    # Create CSV
    df = pd.DataFrame(data)
    output = BytesIO()
    df.to_csv(output, index=False, encoding='utf-8')
    output.seek(0)

    # Return CSV file
    return send_file(output, as_attachment=True, download_name='expenses.csv', mimetype='text/csv')

# Route to download Excel
@data_visualization_bp.route('/download/excel')
def download_excel():
    if not Expense_data:
        render_template('base.html') 
        return "<h1>404 Data Not Found<h1>", 404
    
    expenses=Expense_data[0]
    data = {
        'Sr no': [idx + 1 for idx, _ in enumerate(expenses)],
        'Category': [exp['category_name'] for exp in expenses],
        'Amount': [exp['amount'] for exp in expenses],
        'Date': [exp['date'].strftime("%d-%m-%Y") for exp in expenses],
        'Description': [exp['description'] or "N/A" for exp in expenses],
        'User Name' : [exp['user_name'] for exp in expenses]
    }
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Expenses')
    output.seek(0)
    return send_file(output, as_attachment=True, download_name='expenses.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


# Route to download PDF
@data_visualization_bp.route('/download/pdf')
def download_pdf():
    if not Expense_data:
        render_template('base.html') 
        return "<h1>404 Data Not Found<h1>", 404
    
    expenses=Expense_data[0]
    data = [['Sr no', 'Category', 'Amount', 'Date', 'Description', 'User Name']]
    data += [
    [idx + 1, exp['category_name'], f"{exp['amount']:.2f}", exp['date'].strftime("%d-%m-%y"), exp['description'] or "N/A", exp['user_name']]
    for idx, exp in enumerate(expenses)
    ]

    pdf_output = BytesIO()
    doc = SimpleDocTemplate(pdf_output, pagesize=letter)
    table = Table(data)
    table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey), ('GRID', (0, 0), (-1, -1), 1, colors.black)]))
    doc.build([Paragraph("Expense Report", getSampleStyleSheet()['Heading1']), Spacer(1, 12), table])
    pdf_output.seek(0)

    return send_file(pdf_output, as_attachment=True, download_name="expenses.pdf", mimetype="application/pdf")

@data_visualization_bp.route('/save_report', methods=['GET','POST'])
def save_report():
    if not Expense_data:
        return redirect(url_for('index'))  # Redirect if no expenses found
    
    expenses = Expense_data[0]
    #user_id = request.args.get('user_id')# Get the user_id from the URL or session, if needed
    user_id=session['user_id']
    report_data = generate_report_data(expenses)
    
    # Insert the report into the database
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO reports (user_id, content, generated_at)
                    VALUES (%s, %s, %s)
                """, (user_id, report_data, datetime.now()))
                connection.commit()
    except Exception as e:
        print(f"Error saving report: {e}")
        return "Failed to save report.", 500
    
    return redirect(url_for('data_visualization.index', success_message="success"))  # Redirect back to the home page

    

def generate_report_data(expenses):
    # Generate the report content based on the expenses
    report_content = "Expense Report\n"
    report_content += "ID, Category, Amount, Date, Description, User Name\n"
    for exp in expenses:
        report_content += f"{exp['expense_id']}, {exp['category_name']}, {exp['amount']}, {exp['date']}, {exp['description']}, {exp['user_name']}\n"
    
    return report_content


@data_visualization_bp.route('/history')
def show_history():
    reports = []
    name=session['name']
    with get_db_connection() as connection:
        with connection.cursor(dictionary=True) as cursor:
            user_id=session['user_id']
            cursor.execute(f'SELECT report_id, user_id, content, generated_at FROM reports where user_id={user_id}')
            reports = cursor.fetchall()

    return render_template('history.html', reports=reports,name=name)

@data_visualization_bp.route('/delete_report', methods=['POST'])
def delete_report():
    report_id = request.form.get('report_id')

    # Connect to the database and delete the report
    connection = get_db_connection()
    cursor = connection.cursor()
    
    # Deleting the report from the database
    delete_query = "DELETE FROM reports WHERE report_id = %s"
    cursor.execute(delete_query, (report_id,))
    connection.commit()
    
    cursor.close()
    connection.close()

    # Redirect back to the report history page
    return redirect(url_for('data_visualization.show_history'))

@data_visualization_bp.route('/show_report/<int:report_id>')
def show_report(report_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    user_id = session['user_id']
    name=session['name']
    # Fetch the report content and other details from the database
    cursor.execute("SELECT report_id, user_id, content, generated_at FROM reports WHERE report_id = %s and user_id=%s", (report_id,user_id))
    report = cursor.fetchone()
    cursor.close()
    connection.close()
    
    if report:
        # Parse the content into a list of dictionaries (table rows)
        content_lines = report['content'].strip().split('\n')
        
        # Extract headers from the first line and parse the rest as data
        content_headers = ["Expense Report ID", "Category", "Amount", "Date", "Description", "User Name"]
        content_data = [
            dict(zip(content_headers, line.split(', ')))
            for line in content_lines[2:]  # Skip the first line (headers)
        ]
        

        return render_template('show_report.html', report=report, content_data=content_data,name=name)
    else:
        return "<h1>Report not found</h1>", 404

@data_visualization_bp.errorhandler(404)
def page_not_found(e):
    return render_template(
        'index.html',
        error_message="Invalid action! The page you are trying to access does not exist.",
        families=[],
        family_members=[],
        expenses=[],
        category_totals={}
    ), 404

##### Summary ###### 

# Helper function to calculate the start of the week (Monday)
def get_week_start(date):
    if isinstance(date, str):
        date = datetime.strptime(date, '%d/%m/%Y')
    start_of_week = date - timedelta(days=date.weekday())  # Monday as the start of the week
    return start_of_week.strftime('%d/%m/%Y')


# Function to generate summary
def generate_summary(expense_data):
    total_expense = sum(exp['amount'] for exp in expense_data)
    summary_content = f"Total Expense: ₹{total_expense}\n"
    users = {}

    # Group expenses by user
    for exp in expense_data:
        user_name = exp['user_name']
        if user_name not in users:
            users[user_name] = []
        users[user_name].append(exp)

    for user_name, expenses in users.items():
        user_total_expense = sum(exp['amount'] for exp in expenses)
        unique_categories = set(exp['category_name'] for exp in expenses)
        highest_expense = max(expenses, key=lambda x: x['amount'])
        lowest_expense = min(expenses, key=lambda x: x['amount'])

        # Calculate category-wise expenses
        category_expenses = {}
        for exp in expenses:
            category = exp['category_name']
            if category not in category_expenses:
                category_expenses[category] = 0
            category_expenses[category] += exp['amount']

        # Format category-wise expense details
        category_details = "\n".join(
            f"  - {category}: ₹{amount:.2f}" for category, amount in category_expenses.items()
        )

        summary_content += (
            f"{user_name} spent ₹{user_total_expense:.2f} across {len(unique_categories)} categories.\n"
            f"The highest expense was ₹{highest_expense['amount']:.2f} on {highest_expense['category_name']}.\n"
            f"The lowest was ₹{lowest_expense['amount']:.2f} on {lowest_expense['category_name']}.\n"
            f"Category-wise expenses:\n{category_details}\n"
        )
    return summary_content



# Function to generate weekly brief summary
def generate_brief_summary(expense_data):
    user_expenses = defaultdict(lambda: defaultdict(list))
    weekly_totals = defaultdict(lambda: defaultdict(float))

    for exp in expense_data:
        user_name = exp['user_name']
        week_start = get_week_start(exp['date']) if isinstance(exp['date'], datetime) else get_week_start(exp['date'])
        user_expenses[user_name][week_start].append(exp)
        weekly_totals[user_name][week_start] += exp['amount']

    brief_summary_content = ""
    for user_name, weeks in user_expenses.items():
        brief_summary_content += f"{user_name}:\n"
        max_week = max(weekly_totals[user_name], key=weekly_totals[user_name].get)
        max_amount = weekly_totals[user_name][max_week]

        for week_start, expenses in weeks.items():
            total = weekly_totals[user_name][week_start]
            brief_summary_content += f"Week starting {week_start} (Total: ₹{total:.2f}):\n"
            for exp in expenses:
                date = exp['date']
                brief_summary_content += (
                    f"- Spent ₹{exp['amount']:.2f} on {exp['category_name']} on {date}.\n"
                )

        brief_summary_content += f"\nHighest expense week: Week starting {max_week} (₹{max_amount:.2f})\n\n"

    return brief_summary_content.strip()


# Flask routes
@data_visualization_bp.route('/generate_summary', methods=['POST'])
def generate_summary_endpoint():
    if not Expense_data or not Expense_data[0]:
        return jsonify({"error": "No expense data available."}), 400

    expense_data = Expense_data[0]
    try:
        summary = generate_summary(expense_data)
    except Exception as e:
        return jsonify({"error": f"Failed to generate summary: {e}"}), 500

    return jsonify({"summary": summary})


@data_visualization_bp.route('/generate_brief_summary', methods=['POST'])
def generate_brief_summary_endpoint():
    if not Expense_data or not Expense_data[0]:
        return jsonify({"error": "No expense data available."}), 400

    expense_data = Expense_data[0]
    try:
        brief_summary = generate_brief_summary(expense_data)
    except Exception as e:
        return jsonify({"error": f"Failed to generate brief summary: {e}"}), 500

    return jsonify({"brief_summary": brief_summary})


###### Family Summary ########
@data_visualization_bp.route('/fetch_family_summary', methods=['GET'])
def fetch_family_summary():
    family_id = request.args.get('family_id', type=int)
    time_period = request.args.get('time_period', default='24_hours')

    if not family_id:
        return render_template('summary.html', error_message="Family ID is required.", summary_data=None)

    time_filter = ""
    if time_period == '24_hours':
        time_filter = "AND e.date >= NOW() - INTERVAL 1 DAY"
    elif time_period == '1_week':
        time_filter = "AND e.date >= NOW() - INTERVAL 1 WEEK"
    elif time_period == '1_month':
        time_filter = "AND e.date >= NOW() - INTERVAL 1 MONTH"
    elif time_period == '1_year':
        time_filter = "AND e.date >= NOW() - INTERVAL 1 YEAR"

    query = f"""
        SELECT u.name AS user_name, SUM(e.amount) AS total_amount, c.name AS category_name
        FROM expenses e
        JOIN users u ON e.user_id = u.user_id
        JOIN categories c ON e.category_id = c.category_id
        WHERE e.family_id = %s {time_filter}
        GROUP BY u.name, c.name
        ORDER BY u.name, c.name
    """

    with get_db_connection() as connection:
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute(query, (family_id,))
            raw_data = cursor.fetchall()

    # Group data by user name
    summary_data = {}
    user_totals = {}
    total_expenses = 0

    for row in raw_data:
        user_name = row['user_name']
        if user_name not in summary_data:
            summary_data[user_name] = []
        summary_data[user_name].append({
            'category_name': row['category_name'],
            'total_amount': row['total_amount']
        })
        user_totals[user_name] = user_totals.get(user_name, 0) + row['total_amount']
        total_expenses += row['total_amount']

    if not summary_data:
        return render_template('summary.html', error_message="No data available for the selected time period.", summary_data=None)

    return render_template('summary.html', summary_data=summary_data, user_totals=user_totals, total_expenses=total_expenses, time_period=time_period, family_id=family_id)

if __name__ == '__main__':
    app.run(debug=True)
