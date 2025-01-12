from flask import Flask, render_template, request, redirect, url_for, flash, jsonify,Blueprint
from decimal import Decimal
from savings_goals_manager import SavingsGoalsManager
from db_connection import get_connection



app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Required for flash messages

saving_bp = Blueprint('Saving', __name__, template_folder='templates', static_folder='static')


# Initialize the SavingsGoalsManager
manager = SavingsGoalsManager()

@saving_bp.route('/')
def index():
    return render_template('index_saving.html')

@saving_bp.route('/create_goal', methods=['GET', 'POST'])
def create_goal():
    if request.method == 'POST':
        try:
            user_id = int(request.form['user_id'])
            user_goal = float(request.form['user_goal'])
            deadline = request.form['deadline']
            
            # Check if the user is an admin
            is_admin = manager.is_admin(user_id)
            family_goal = request.form.get('family_goal')
            
            if family_goal and not is_admin:
                flash("Only administrators can create family goals.", "error")
                return redirect(url_for('create_goal'))
            
            # Create a family goal if admin
            family_goal = float(family_goal) if family_goal else None
            success = manager.create_savings_goal(user_id, user_goal, deadline, family_goal)
            
            if success:
                flash("Savings goal created successfully!", "success")
            else:
                flash("Failed to create savings goal.saving goal adready exits", "error")
        except ValueError as e:
            flash(f"Invalid input: {str(e)}", "error")
            
        return redirect(url_for('Saving.create_goal'))
        
    return render_template('create_goal.html')

@saving_bp.route('/contribute', methods=['GET', 'POST'])
def contribute():
    if request.method == 'POST':
        try:
            user_id = int(request.form['user_id'])
            contribution_type = request.form['contribution_type']
            amount = float(request.form['amount'])

            # First check if user is admin and if it's a family contribution
            if contribution_type == 'family':
                # Check if family_target_amount is 0
                query = """
                SELECT family_target_amount 
                FROM savings_goals 
                WHERE user_id = %s
                """
                manager.cursor.execute(query, (user_id,))
                goal_info = manager.cursor.fetchone()

                if goal_info and goal_info['family_target_amount'] == 0:
                    if manager.is_admin(user_id):
                        # Redirect admin to update goal page with pre-filled values
                        flash('Family goal has been reached! Please set a new family goal.', 'success')
                        return redirect(url_for('update_goal', 
                                              user_id=user_id, 
                                              goal_type='family'))
                    else:
                        flash('Family goal has been reached! Please wait for admin to set a new goal.', 'info')
                        return redirect(url_for('Saving.contribute'))

            # Process the contribution if we haven't redirected
            success, message = manager.contribute_to_goal(user_id, contribution_type, amount)

            if success:
                # Get current goal information
                query = """
                SELECT user_target_amount, family_target_amount
                FROM savings_goals 
                WHERE user_id = %s
                """
                manager.cursor.execute(query, (user_id,))
                goal_info = manager.cursor.fetchone()

                if goal_info:
                    if contribution_type == 'user' and goal_info['user_target_amount'] == 0:
                        flash('Congratulations! You\'ve completed your goal! Please set a new personal goal!', 'success')
                        return redirect(url_for('update_goal', user_id=user_id, goal_type='user'))
                    elif contribution_type == 'family' and goal_info['family_target_amount'] == 0:
                        if manager.is_admin(user_id):
                            flash('Congratulations! Family goal completed! Please set a new family goal!', 'success')
                            return redirect(url_for('update_goal', user_id=user_id, goal_type='family'))
                        else:
                            flash('Congratulations! Your family has completed its goal! An admin will set a new family goal.', 'success')
                else:
                    flash('Goal information not found.', 'error')
            else:
                flash(message, 'error')

        except ValueError as e:
            flash(f'Invalid input: {str(e)}', 'error')

        return redirect(url_for('Saving.contribute'))

    return render_template('contribute.html')
@saving_bp.route('/display_goals', methods=['GET', 'POST'])
def display_goals():
    goals = None
    if request.method == 'POST':
        try:
            user_id = int(request.form['user_id'])
            family_id = manager.get_family_id(user_id)

            if family_id:
                # Fetch goals from database
                manager.cursor.execute("SELECT * FROM savings_goals WHERE family_id = %s", (family_id,))
                goals = manager.cursor.fetchall()

        except ValueError as e:
            flash(f'Invalid input: {str(e)}', 'error')

    return render_template('display_goals.html', goals=goals)

@saving_bp.route('/update_goal', methods=['GET', 'POST'])
def update_goal():
    # Get URL parameters for pre-filling the form
    pre_fill_user_id = request.args.get('user_id', '')
    pre_fill_goal_type = request.args.get('goal_type', 'user')

    if request.method == 'POST':
        try:
            user_id = int(request.form['user_id'])
            update_type = request.form['update_type']
            new_goal = float(request.form['new_goal'])
            deadline = request.form['deadline']
            confirmation = request.form.get('confirmation', 'no')

            if confirmation != 'yes':
                flash('Update cancelled by user.', 'error')
                return redirect(url_for('update_goal'))

            if update_type == 'user':
                success, message = manager.new_update_goal(user_id, new_goal, deadline)
            else:  # family
                if not manager.is_admin(user_id):
                    flash('Only administrators can update family goals.', 'error')
                    return redirect(url_for('update_goal'))
                success, message = manager.new_update_family_goal(user_id, new_goal, deadline)

            if success:
                flash(message, 'success')
            else:
                flash(message, 'error')

        except ValueError as e:
            flash(f'Invalid input: {str(e)}', 'error')

        return redirect(url_for('Saving.update_goal'))

    return render_template('update_goal.html', 
                         pre_fill_user_id=pre_fill_user_id,
                         pre_fill_goal_type=pre_fill_goal_type)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
