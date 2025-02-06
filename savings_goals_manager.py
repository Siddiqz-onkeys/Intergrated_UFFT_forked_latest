from datetime import datetime
from flask import session
import calendar
import mysql.connector
from mysql.connector import Error
import datetime
from decimal import Decimal
from db_connection import get_connection
connection=get_connection()
#cursor=connection.cursor()
cursor = connection.cursor(buffered=True)
class SavingsGoalsManager:
    
    def get_user_id(self):
        """Retrieve the user ID from the session."""
        global user_id
        user_id = session.get('user_id')
        if not user_id:
            raise ValueError("User is not logged in.")
        return user_id
    
    def update_savings_goal(self):
        user_id = session.get('user_id')
        if not user_id:
            print("User is not logged in.")
            return False
        
    def validate_user(self, user_id):
        """
        Validate if user exists and get user details
        """
        try:
            query = "SELECT * FROM Users WHERE user_id = %s"
            cursor.execute(query, (user_id,))
            user = cursor.fetchone()
            return user
        except Error as e:
            print(f"Database error during user validation: {e}")
            return None

    def is_admin(self):
        user_id = self.get_user_id()
        query = "SELECT role FROM users WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        user = cursor.fetchone()
        return user and user[0].lower() == 'hof'

    def get_family_id(self):
        user_id = self.get_user_id()
        query = "SELECT family_id FROM users WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        user = cursor.fetchone()
        return user[0] if user else None
        
    def get_joint_id(self, user_id_1):
        """
        Get the joint ID for a given user
        """
        try:
            query = "SELECT joint_id FROM joint_goals WHERE user_id_1= %s"
            cursor.execute(query, (user_id_1,))
            joint = cursor.fetchone()
            return joint['joint_id'] if joint else None
        except Error as e:
            print(f"Database error getting family ID: {e}")
            return None

    def update_family_goal_for_family(self, family_id, new_family_goal):
        """
        Update the family goal for all users in the same family
        
        Args:
            family_id (int): The ID of the family to update
            new_family_goal (Decimal): The new family goal amount
        
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            # Convert new_family_goal to Decimal to ensure precision
            new_family_goal = Decimal(str(new_family_goal))

            # Update all savings goals for the family
            update_query = """
            UPDATE savings_goals 
            SET family_goal = %s, 
                family_target_amount = %s 
            WHERE family_id = %s
            """
            
            cursor.execute(update_query, (new_family_goal, new_family_goal, family_id))
            self.connection.commit()
            print(f"Family goal set to Rs {new_family_goal} for all family members.")
            return True

        except Error as e:
            print(f"Error updating family goal: {e}")
            self.connection.rollback()
            return False

    def update_savings_goal(self, new_goal, deadline):
        """Update savings goal using session-based user ID."""
        try:
            user_id = self.get_user_id()  # Get user ID from session
            family_id = self.get_family_id(user_id)  # Get family ID using user_id

            if not family_id:
                return False

            query = "SELECT * FROM savings_goals WHERE user_id = %s AND family_id = %s"
            cursor.execute(query, (user_id, family_id))
            existing_goal = cursor.fetchone()

            if not existing_goal:
                return False

            update_query = """
            UPDATE savings_goals 
            SET user_goal = %s, 
                user_target_amount = %s,
                deadline = %s
            WHERE user_id = %s AND family_id = %s
            """
            cursor.execute(update_query, (
                Decimal(str(new_goal)), 
                Decimal(str(new_goal)), 
                deadline,
                user_id, 
                family_id
            ))
            self.connection.commit()
            return True

        except (Error, ValueError) as e:
            print(f"Error updating savings goal: {e}")
            self.connection.rollback()
            return False

    def new_update_goal(self, new_user_goal, deadline):
        try:
            user_id = self.get_user_id()
            family_id = self.get_family_id(user_id)

            if not family_id:
                return False, "Could not find family for this user."

            query = "SELECT * FROM savings_goals WHERE user_id = %s AND family_id = %s"
            cursor.execute(query, (user_id, family_id))
            existing_goal = cursor.fetchone()

            if not existing_goal:
                return False, "No existing savings goal found for this user."

            update_query = """
            UPDATE savings_goals 
            SET user_goal = %s, 
                user_target_amount = %s,
                deadline = %s
            WHERE user_id = %s AND family_id = %s
            """
            cursor.execute(update_query, (
                Decimal(str(new_user_goal)), 
                Decimal(str(new_user_goal)), 
                deadline,
                user_id, 
                family_id
            ))
            self.connection.commit()
            return True, f"User goal updated to Rs {new_user_goal} successfully!"

        except (Error, ValueError) as e:
            self.connection.rollback()
            return False, f"Error updating savings goal: {e}"


    def new_update_family_goal(self, new_family_goal, deadline):
        try:
            user_id = self.get_user_id()
            family_id = self.get_family_id(user_id)

            if not family_id:
                return False, "Could not find family for this user."

            if not self.is_admin():
                return False, "Only admin can update family goal."

            update_query = """
            UPDATE savings_goals 
            SET family_goal = %s,
                family_target_amount = %s,
                deadline = %s
            WHERE family_id = %s
            """
            cursor.execute(update_query, (
                Decimal(str(new_family_goal)),
                Decimal(str(new_family_goal)),
                deadline,
                family_id
            ))
            self.connection.commit()
            return True, f"Family goal updated to Rs {new_family_goal} successfully!"

        except (Error, ValueError) as e:
            self.connection.rollback()
            return False, f"Error updating family goal: {e}"

    def create_savings_goal(self, user_goal, deadline, family_goal=None):
            user_id = self.get_user_id()
            family_id = self.get_family_id()

            if not family_id:
                return False

            if family_goal is not None and not self.is_admin():
                return False

            query = "INSERT INTO savings_goals (family_id, user_id, user_goal, user_target_amount, deadline) VALUES (%s, %s, %s, %s, %s)"
            values = (family_id, user_id, Decimal(user_goal), Decimal(user_goal), deadline)
            cursor.execute(query, values)
            connection.commit()
            return True
        

    
    def get_users_by_family(self, family_id):
        """
        Fetch all users belonging to a specific family.
        """
        try:
            query = "SELECT user_id, name FROM Users WHERE family_id = %s"
            cursor.execute(query, (family_id,))
            return cursor.fetchall()
        except Error as e:
            print(f"Database error fetching users by family ID: {e}")
            return []

    def create_joint_goal(self, user_ids, joint_goal_amount, deadline):
        try:
            family_id = self.get_family_id()
            joint_goal_amount = Decimal(joint_goal_amount)

            insert_joint_goal_query = """
            INSERT INTO joint_goals (joint_goal_amount, joint_target_amount, deadline) 
            VALUES (%s, %s, %s)
            """
            cursor.execute(insert_joint_goal_query, (joint_goal_amount, joint_goal_amount, deadline))
            joint_id = cursor.lastrowid

            for user_id in user_ids:
                insert_participant_query = """
                INSERT INTO joint_goal_participants (joint_id, user_id, contributed_amount)
                VALUES (%s, %s, 0)
                """
                cursor.execute(insert_participant_query, (joint_id, user_id))
            
            self.connection.commit()
            return True
        except Error as e:
            self.connection.rollback()
            return False


    def contribute_to_goal(self, contribution_type, amount):
        try:
            user_id = self.get_user_id()
            family_id = self.get_family_id(user_id)
            amount = Decimal(amount)

            if contribution_type == 'user':
                query = """
                UPDATE savings_goals SET user_target_amount = user_target_amount - %s,
                    usergoal_contributed_amount = usergoal_contributed_amount + %s
                WHERE family_id = %s AND user_id = %s
                """
                cursor.execute(query, (amount, amount, family_id, user_id))

            elif contribution_type == 'family':
                query = """
                UPDATE savings_goals SET family_target_amount = family_target_amount - %s
                WHERE family_id = %s
                """
                cursor.execute(query, (amount, family_id))

            self.connection.commit()
            return True
        except Error as e:
            self.connection.rollback()
            return False


    def contribute_to_joint_goal(self, amount):
        try:
            user_id = self.get_user_id()
            joint_id = session.get('joint_id')
            if not joint_id:
                return False

            amount = Decimal(amount)
            update_query = "UPDATE joint_goals SET joint_target_amount = joint_target_amount - %s WHERE joint_id = %s"
            cursor.execute(update_query, (amount, joint_id))
            
            update_participant_query = "UPDATE joint_goal_participants SET contributed_amount = contributed_amount + %s WHERE joint_id = %s AND user_id = %s"
            cursor.execute(update_participant_query, (amount, joint_id, user_id))
            
            self.connection.commit()
            return True
        except Error as e:
            self.connection.rollback()
            return False
        
    def display_savings_goal(self):
        """
        Display current savings goal details
        """
        try:
            user_id = int(input("Enter User ID: "))
            
            # Get family ID
            family_id = self.get_family_id(user_id)
            if not family_id:
                print("Could not find family for this user.")
                return

            # Fetch all goals for the family
            query = "SELECT * FROM savings_goals WHERE family_id = %s"
            cursor.execute(query, (family_id,))
            goals = cursor.fetchall()

            if goals:
                print("\n--- Family Savings Goals ---")
                for goal in goals:
                    print(f"\nUser ID: {goal['user_id']}")
                    print(f"User Goal: Rs{goal['user_goal']}")
                    print(f"User Target Remaining: Rs {goal['user_target_amount']}")
                    
                    # Only display family goal once
                    if goal == goals[0]:
                        print(f"Family Goal: Rs {goal['family_goal']}")
                        print(f"Family Target Remaining: Rs {goal['family_target_amount']}")
                        print(f"User Goal Contributed Amount: Rs {goal['usergoal_contributed_amount']}")
                        print(f"Family Goal Contributed Amount: Rs {goal['familygoal_contributed_amount']}")
                        print(f"Total Contributed Amount: Rs {goal['familygoal_contributed_amount']+goal['usergoal_contributed_amount']}")
                        print(f"Deadline: {goal['deadline']}")
            else:
                print("No savings goals found for this family.")

        except Error as e:
            print(f"Error displaying savings goal: {e}")
    def display_joint_goals(self, user_id):
        """
        Display all joint goals for a user
        """
        try:
            query = """
            SELECT 
                jg.joint_id,
                jg.joint_goal_amount,
                jg.joint_target_amount,
                jg.deadline,
                jgp.contributed_amount as user_contribution,
                GROUP_CONCAT(u.username) as participants,
                GROUP_CONCAT(jgp2.contributed_amount) as all_contributions
            FROM joint_goals jg
            JOIN joint_goal_participants jgp ON jg.joint_id = jgp.joint_id
            JOIN joint_goal_participants jgp2 ON jg.joint_id = jgp2.joint_id
            JOIN users u ON jgp2.user_id = u.user_id
            WHERE jgp.user_id = %s
            GROUP BY jg.joint_id, jgp.contributed_amount
            """
            cursor.execute(query, (user_id,))
            goals = cursor.fetchall()

            if not goals:
                print("No joint goals found for this user.")
                return

            print("\n=== Your Joint Goals ===")
            for goal in goals:
                print(f"\nJoint Goal ID: {goal['joint_id']}")
                print(f"Total Goal Amount: Rs {goal['joint_goal_amount']}")
                print(f"Remaining Target: Rs {goal['joint_target_amount']}")
                print(f"Your Contribution: Rs {goal['user_contribution']}")
                print(f"Deadline: {goal['deadline']}")
                
                # Display all participants and their contributions
                participants = goal['participants'].split(',')
                contributions = goal['all_contributions'].split(',')
                print("\nParticipants:")
                for participant, contribution in zip(participants, contributions):
                    print(f"- {participant}: Rs {contribution}")

        except Error as e:
            print(f"Error displaying joint goals: {str(e)}")
    
    def delete_user_goal(self, user_id):
        try:
            # query = "DELETE FROM savings_goals WHERE user_id = %s"
            query="UPDATE savings_goals SET user_goal=%s, user_target_amount=%s, usergoal_contributed_amount=%s WHERE user_id=%s"
            cursor.execute(query, (None,None,None,user_id,))
            self.connection.commit()
            return True
        except Exception as e:
            self.connection.rollback()
            raise Exception(f"Error deleting user goal: {e}")

    def delete_family_goal(self, family_id):
        """
        Delete all savings goals for a family.
        """
        try:
            # query = "DELETE FROM savings_goals WHERE family_id = %s"
            query="UPDATE savings_goals SET family_goal=%s, family_target_amount=%s, familygoal_contributed_amount=%s WHERE family_id=%s"
            cursor.execute(query, (None,None,None,family_id,))
            self.connection.commit()
        except Error as e:
            self.connection.rollback()
            raise Exception(f"Error deleting family goal: {e}")

    def delete_joint_goal(self, joint_id, user_id, leave_contributions):
        """
        Delete or adjust a joint goal based on user action.
        Args:
            joint_id: ID of the joint goal.
            user_id: ID of the user performing the action.
            leave_contributions: Flag to leave contributions (1) or withdraw (0).
        """
        try:
            if leave_contributions == 1:
                # Remove the user from the joint goal but keep contributions
                delete_query = "DELETE FROM joint_goal_participants WHERE joint_id = %s AND user_id = %s"
                cursor.execute(delete_query, (joint_id, user_id))
            else:
                # Refund contributions and remove the user
                refund_query = """
                    UPDATE joint_goals 
                    SET joint_target_amount = joint_target_amount + 
                        (SELECT contributed_amount 
                        FROM joint_goal_participants 
                        WHERE joint_id = %s AND user_id = %s)
                    WHERE joint_id = %s
                """
                cursor.execute(refund_query, (joint_id, user_id, joint_id))
                delete_query = "DELETE FROM joint_goal_participants WHERE joint_id = %s AND user_id = %s"
                cursor.execute(delete_query, (joint_id, user_id))

            # If no participants remain, delete the joint goal
            cursor.execute("SELECT COUNT(*) AS count FROM joint_goal_participants WHERE joint_id = %s", (joint_id,))
            result = cursor.fetchone()
            if result and result['count']<2:
                cursor.execute("DELETE FROM joint_goal_participants WHERE joint_id = %s", (joint_id,))
                cursor.execute("DELETE FROM joint_goals WHERE joint_id = %s", (joint_id,))

            self.connection.commit()
        except Error as e:
            self.connection.rollback()
            raise Exception(f"Error managing joint goal deletion: {e}")



    def track(self, user_id):
        """
        Track progress of user and family goals. 
        Prompts for new goals when target amounts are reached.
        """
        # Get family ID
        family_id = self.get_family_id(user_id)
        if not family_id:
            print("Could not find family for this user.")
            return

        # Check if the user's individual target is 0
        query = "SELECT user_id FROM savings_goals WHERE user_target_amount = 0"
        cursor.execute(query)
        res = cursor.fetchall()

        for i in res:
            if i['user_id'] == user_id:
                print("You have reached your saving goal! Please create a new goal.")
                try:
                    new_user_goal = float(input("Enter new User Goal Amount: "))
                    if new_user_goal <= 0:
                        raise ValueError("User goal must be greater than 0.")
                    deadline = input("Enter new deadline (YYYY-MM-DD): ")
                    datetime.datetime.strptime(deadline, "%Y-%m-%d")  # Validate date format
                    self.new_update_goal(user_id, new_user_goal, deadline)
                except ValueError as e:
                    print(f"Invalid input: {e}")
                    return

        # Check if the family's target is 0
        query1 = "SELECT family_id FROM savings_goals WHERE family_target_amount = 0"
        cursor.execute(query1)
        res1 = cursor.fetchall()
        for i in res1:
            if i['family_id'] == family_id:
                print("You have completed your family saving goal!")
                try:
                    new_family_goal = float(input("Enter new Family Goal Amount: "))
                    if new_family_goal <= 0:
                        raise ValueError("Family goal must be greater than 0.")
                    deadline = input("Enter new deadline (YYYY-MM-DD): ")
                    datetime.datetime.strptime(deadline, "%Y-%m-%d")  # Validate date format
                    success, message = self.new_update_family_goal(user_id, new_family_goal, deadline)
                    if success:
                        print("A new family goal has been set!")
                    else:
                        print(f"Failed to set a new family goal: {message}")
                except ValueError as e:
                    print(f"Invalid input: {e}")
                break

    def is_goal_zero(self, user_id, contribution_type):
        try:
            if contribution_type == "user":
                cursor.execute("SELECT user_goal FROM savings_goals WHERE user_id = %s", (user_id,))
            elif contribution_type == "family":
                cursor.execute("SELECT family_goal FROM savings_goals WHERE family_id = (SELECT family_id FROM users WHERE user_id = %s)", (user_id,))
            else:
                return True

            result = cursor.fetchone()
            return result and result[0] == 0
        except Exception as e:
            print(f"Error checking goal: {e}")
            return True
    def get_user_goal_info(self, user_id):
        """Get user's goal and current savings information"""
        try:
            query = """
            SELECT user_goal, user_target_amount, usergoal_contributed_amount,familygoal_contributed_amount 
            FROM savings_goals 
            WHERE user_id = %s
            """
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            if result:
                return {
                    'total_goal': result['user_goal'],
                    'remaining': result['user_target_amount'],
                    'usergoal_contributed_amount': result['usergoal_contributed_amount'],
                    'familygoal_contributed_amount': result['familygoal_contributed_amount']

                }
            return None
        except Error as e:
            print(f"Error getting user goal info: {e}")
            return None
    def create_investment(self, principal_amount, interest_rate):
        try:
            user_id = self.get_user_id()
            principal_amount = Decimal(principal_amount)
            interest_rate = Decimal(interest_rate)
            start_date = datetime.now().date()
            query = "INSERT INTO fixed_investment (user_id, principal_amount, interest_rate, start_date) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (user_id, principal_amount, interest_rate, start_date))
            self.connection.commit()
            return True
        except Error as e:
            self.connection.rollback()
            return False

    def display_investment(self):
        
        """
        Display investment details with calculated daily interest
        
        Args:
            user_id (int): User's ID
            
        Returns:
            tuple: (success_bool, data_dict or error_message)
        """
        try:
            # Validate user
            if not self.validate_user(user_id):
                return False, "Invalid user ID"
                
            # Get investment details
            query = """
            SELECT investment_id, principal_amount, interest_rate, start_date
            FROM fixed_investment
            WHERE user_id = %s
            """
            cursor.execute(query, (user_id,))
            investments = cursor.fetchall()
            
            if not investments:
                return False, "No investments found for this user"
                
            current_date = datetime.datetime.now().date()
            investment_details = []
            
            for inv in investments:
                # Calculate days since investment
                days_invested = (current_date - inv['start_date']).days
                
                # Calculate interest earned
                annual_interest = (inv['principal_amount'] * inv['interest_rate']) / Decimal('100')
                daily_interest = annual_interest / Decimal('365')
                total_interest_earned = daily_interest * Decimal(str(days_invested))
                
                # Get current month's days
                current_month_days = calendar.monthrange(current_date.year, current_date.month)[1]
                monthly_interest = annual_interest / Decimal('12')
                current_daily_interest = monthly_interest / Decimal(str(current_month_days))
                
                investment_details.append({
                    'investment_id': inv['investment_id'],
                    'principal_amount': float(inv['principal_amount']),
                    'interest_rate': float(inv['interest_rate']),
                    'start_date': inv['start_date'].strftime('%Y-%m-%d'),
                    'days_invested': days_invested,
                    'total_interest_earned': float(total_interest_earned),
                    'current_daily_interest': float(current_daily_interest)
                })
                
            return True, investment_details
            
        except Error as e:
            return False, f"Error displaying investment: {str(e)}"

    def delete_investment(self, user_id, investment_id=None):
        """
        Delete investment(s) for a user
        
        Args:
            user_id (int): User's ID
            investment_id (int, optional): Specific investment ID to delete
            
        Returns:
            tuple: (success_bool, message_string)
        """
        try:
            # Validate user
            if not self.validate_user(user_id):
                return False, "Invalid user ID"
                
            if investment_id:
                # Delete specific investment
                query = """
                DELETE FROM fixed_investment 
                WHERE user_id = %s AND investment_id = %s
                """
                cursor.execute(query, (user_id, investment_id))
            else:
                # Delete all investments for user
                query = "DELETE FROM fixed_investment WHERE user_id = %s"
                cursor.execute(query, (user_id,))
                
            if cursor.rowcount == 0:
                return False, "No investments found to delete"
                
            self.connection.commit()
            return True, "Investment(s) deleted successfully"
            
        except Error as e:
            self.connection.rollback()
            return False, f"Error deleting investment: {str(e)}"

def main():
    manager = SavingsGoalsManager()
    while True:
        print("\n--- Unified Family Finance Tracker ---")
        print("1. Create User Savings Goal")
        print("2. Create Joint Savings Goal")
        print("3. Contribute to Savings Goal")
        print("4. Contribute to Joint Goal")
        print("5. Display Family Savings Goals")
        print("6. Display Joint Goals")
        print("7. Update Savings Goal")
        print("8. Exit")

        choice = input("Enter your choice (1-8): ")

        try:
            if choice == '1':
                user_id = int(input("Enter User ID: "))
                if manager.is_admin(user_id):
                    user_goal = float(input("Enter User Goal Amount: "))
                    family_goal = float(input("Enter Family Goal Amount (optional, press enter to skip): ") or 0)
                    deadline = input("Enter Deadline (YYYY-MM-DD): ")
                    family_goal = family_goal if family_goal > 0 else None
                    manager.create_savings_goal(user_id, user_goal, deadline, family_goal)
                else:
                    user_goal = float(input("Enter User Goal Amount: "))
                    deadline = input("Enter Deadline (YYYY-MM-DD): ")
                    manager.create_savings_goal(user_id, user_goal, deadline)

            elif choice == '2':
                user_ids = []
                print("Enter User IDs (press Enter when done)")
                while True:
                    user_id = input("Enter User ID (or press Enter to finish adding users): ")
                    if not user_id:
                        break
                    user_ids.append(int(user_id))
                
                if len(user_ids) < 2:
                    print("At least two users are required for a joint goal.")
                    continue
                
                joint_goal = float(input("Enter Joint Goal Amount: "))
                deadline = input("Enter Deadline (YYYY-MM-DD): ")
                success, message = manager.create_joint_goal(user_ids, joint_goal, deadline)
                print(message)

            elif choice == '3':
                user_id = int(input("Enter User ID: "))
                contribution_type = input("Contribute to 'user' or 'family' goal: ").lower()
                amount = float(input("Enter contribution amount: "))
                success, message = manager.contribute_to_goal(user_id, contribution_type, amount)
                print(message)
                manager.track(user_id)

            elif choice == '4':
                user_id = int(input("Enter User ID: "))
                amount = float(input("Enter contribution amount: "))
                success, message = manager.contribute_to_joint_goal(user_id, amount)
                print(message)

            elif choice == '5':
                manager.display_savings_goal()

            elif choice == '6':
                user_id = int(input("Enter User ID: "))
                manager.display_joint_goals(user_id)

            elif choice == '7':
                user_id = int(input("Enter User ID: "))
                manager.update_savings_goal(user_id)

            elif choice == '8':
                print("Exiting the application.")
                break

            else:
                print("Invalid choice. Please try again.")

        except ValueError as e:
            print(f"Invalid input: {str(e)}")

if __name__ == "__main__":
    main()
