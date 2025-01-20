import mysql.connector
from mysql.connector import Error
import datetime
from decimal import Decimal

class SavingsGoalsManager:
    def __init__(self):
        try:
            # Establish database connection
            self.connection = mysql.connector.connect(
                host='localhost',
                database='projectufft',
                user='root',
                password='Anju@123',
                use_pure=True  # This helps with Decimal handling
            )
            self.cursor = self.connection.cursor(dictionary=True)
        except Error as e:
            print(f"Error connecting to MySQL Platform: {e}")
            raise

    def validate_user(self, user_id):
        """
        Validate if user exists and get user details
        """
        try:
            query = "SELECT * FROM Users WHERE user_id = %s"
            self.cursor.execute(query, (user_id,))
            user = self.cursor.fetchone()
            return user
        except Error as e:
            print(f"Database error during user validation: {e}")
            return None

    def is_admin(self, user_id):
        """
        Check if the user is an admin of the family
        """
        try:
            query = "SELECT role FROM Users WHERE user_id = %s"
            self.cursor.execute(query, (user_id,))
            user = self.cursor.fetchone()
            return user and user['role'].lower() == 'hof'
        except Error as e:
            print(f"Database error checking admin status: {e}")
            return False

    def get_family_id(self, user_id):
        """
        Get the family ID for a given user
        """
        try:
            query = "SELECT family_id FROM Users WHERE user_id = %s"
            self.cursor.execute(query, (user_id,))
            user = self.cursor.fetchone()
            return user['family_id'] if user else None
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
            
            self.cursor.execute(update_query, (new_family_goal, new_family_goal, family_id))
            self.connection.commit()
            print(f"Family goal set to ${new_family_goal} for all family members.")
            return True

        except Error as e:
            print(f"Error updating family goal: {e}")
            self.connection.rollback()
            return False

    def update_savings_goal(self, user_id):
        
        """
        Update savings goal for a user
        
        Args:
            user_id (int): ID of the user updating the goal
        
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            # Get family ID
            family_id = self.get_family_id(user_id)
            if not family_id:
                print("Could not find family for this user.")
                return False

            # Check if a goal exists for this user
            query = "SELECT * FROM savings_goals WHERE user_id = %s AND family_id = %s"
            self.cursor.execute(query, (user_id, family_id))
            existing_goal = self.cursor.fetchone()
            
            if not existing_goal:
                print("No existing savings goal found for this user.")
                return False

            # Determine update type
            update_type = input("Do you want to update 'user' or 'family' goal? ").lower()

            if update_type == 'user':
                # Regular user can update their own goal
                new_user_goal = float(input("Enter new User Goal Amount: "))
                
                # Confirm user goal update
                confirm = input(f"Confirm updating your goal from ${existing_goal['user_goal']} to ${new_user_goal}? (yes/no): ").lower()
                if confirm != 'yes':
                    print("Goal update cancelled.")
                    return False

                # Update user goal
                update_query = """
                UPDATE savings_goals 
                SET user_goal = %s, 
                    user_target_amount = %s 
                WHERE user_id = %s AND family_id = %s
                """
                self.cursor.execute(update_query, (
                    Decimal(str(new_user_goal)), 
                    Decimal(str(new_user_goal)), 
                    user_id, 
                    family_id
                ))
                print(f"User goal updated to ${new_user_goal} successfully!")

            elif update_type == 'family':
                # Only admin can update family goal
                if not self.is_admin(user_id):
                    print("Only admin can update family goal.")
                    return False

                new_family_goal = float(input("Enter new Family Goal Amount: "))
                
                # Confirm family goal update
                confirm = input(f"Confirm updating family goal from ${existing_goal['family_goal']} to ${new_family_goal}? (yes/no): ").lower()
                if confirm != 'yes':
                    print("Goal update cancelled.")
                    return False

                # Update family goal for all family members
                self.update_family_goal_for_family(family_id, new_family_goal)
                print(f"Family goal updated to ${new_family_goal} successfully!")

            else:
                print("Invalid goal type. Choose 'user' or 'family'.")
                return False

            self.connection.commit()
            return True

        except (Error, ValueError) as e:
            print(f"Error updating savings goal: {e}")
            self.connection.rollback()
            return False
    def new_update_goal(self, user_id, new_user_goal, deadline):
        try:
            family_id = self.get_family_id(user_id)
            if not family_id:
                return False, "Could not find family for this user."

            query = "SELECT * FROM savings_goals WHERE user_id = %s AND family_id = %s"
            self.cursor.execute(query, (user_id, family_id))
            existing_goal = self.cursor.fetchone()
    
            if not existing_goal:
                return False, "No existing savings goal found for this user."

            update_query = """
            UPDATE savings_goals 
            SET user_goal = %s, 
                user_target_amount = %s,
                deadline = %s
            WHERE user_id = %s AND family_id = %s
            """
            self.cursor.execute(update_query, (
                Decimal(str(new_user_goal)), 
                Decimal(str(new_user_goal)), 
                deadline,
                user_id, 
                family_id
            ))
            self.connection.commit()
            return True, f"User goal updated to ${new_user_goal} successfully!"

        except (Error, ValueError) as e:
            self.connection.rollback()
            return False, f"Error updating savings goal: {e}"

    def new_update_family_goal(self, user_id, new_family_goal, deadline):
        try:
            family_id = self.get_family_id(user_id)
            if not family_id:
                return False, "Could not find family for this user."

            if not self.is_admin(user_id):
                return False, "Only admin can update family goal."

            # Update family goal including deadline
            update_query = """
            UPDATE savings_goals 
            SET family_goal = %s,
                family_target_amount = %s,
                deadline = %s
            WHERE family_id = %s
            """
            self.cursor.execute(update_query, (
                Decimal(str(new_family_goal)),
                Decimal(str(new_family_goal)),
                deadline,
                family_id
            ))
            self.connection.commit()
            return True, f"Family goal updated to ${new_family_goal} successfully!"

        except (Error, ValueError) as e:
            self.connection.rollback()
            return False, f"Error updating family goal: {e}"
    def create_savings_goal(self, user_id, user_goal, deadline, family_goal=None):
        """
        Create a new savings goal for a user
        """
        try:
            # Validate user
            user = self.validate_user(user_id)
            if not user:
                print("Invalid User ID")
                return False
            if user_goal <= 0:
                print("Saving goal cannot be zero or negative!")
                return False
            
            # Get family ID
            family_id = user['family_id']

            # Convert user goal to Decimal
            user_goal = Decimal(str(user_goal))

            # Only admin can set a new family goal
            if family_goal is not None and not self.is_admin(user_id):
                print("Only admin can create family goals")
                return False

            # Check if a goal already exists for this user
            query = "SELECT * FROM savings_goals WHERE user_id = %s AND family_id = %s"
            self.cursor.execute(query, (user_id, family_id))
            existing_goal = self.cursor.fetchone()
        
            if existing_goal:
                print("A savings goal for this user already exists.")
                return False

            # Check for existing family goal in the family
            query = "SELECT family_goal, family_target_amount FROM savings_goals WHERE family_id = %s AND family_goal IS NOT NULL LIMIT 1"
            self.cursor.execute(query, (family_id,))
            existing_family_goal = self.cursor.fetchone()

            # Determine which family goal to use
            final_family_goal = None
            final_family_target = None

            if self.is_admin(user_id) and family_goal is not None:
                # Admin is setting a new family goal
                final_family_goal = Decimal(str(family_goal))
                final_family_target = final_family_goal
            elif existing_family_goal:
                # Use existing family goal for new member
                final_family_goal = existing_family_goal['family_goal']
                final_family_target = existing_family_goal['family_target_amount']

            # Insert new savings goal
            if final_family_goal is not None:
                query = """
                INSERT INTO savings_goals 
                (family_id, user_id, user_goal, family_goal, 
                user_target_amount, family_target_amount, usergoal_contributed_amount,  familygoal_contributed_amount, deadline) 
                VALUES (%s, %s, %s, %s, %s, %s, 0, 0, %s)
                """
                values = (family_id, user_id, user_goal, final_family_goal, 
                        user_goal, final_family_target, deadline)
            
                # If admin is setting a new family goal, update it for all existing members
                if self.is_admin(user_id) and family_goal is not None:
                    self.update_family_goal_for_family(family_id, family_goal)
            else:
                # No family goal exists
                query = """
                INSERT INTO savings_goals 
                (family_id, user_id, user_goal, 
                user_target_amount, usergoal_contributed_amount,  familygoal_contributed_amount, deadline) 
                VALUES (%s, %s, %s, %s, 0, 0, %s)
                """
                values = (family_id, user_id, user_goal,
                        user_goal, deadline)
        
            self.cursor.execute(query, values)
            self.connection.commit()
            print("Savings goal created successfully!")
            return True

        except Error as e:
            print(f"Error creating savings goal: {e}")
            self.connection.rollback()
            return False
    def joint_savings_goals(self,user_id_1,user_id_2,joint_goal):
        """
        Create a joint savings goal for 2 users
        """
        try:
            # Validate user
            user_list=[user_id_1,user_id_2]
            # for user_id in user_list:
            user1 = self.validate_user(user_id_1)
            user2 = self.validate_user(user_id_2)
            if not user1 or not user2:
                print("Invalid User ID")
                return False
            if joint_goal <= 0:
                print("Saving goal cannot be zero or negative!")
                return False
            
            # Get family ID
            if user1['family_id']!=user2['family_id']:
                print("Both users are not from same family")
                return False
            family_id = user1['family_id']
            # Convert user goal to Decimal
            joint_goal = Decimal(str(joint_goal))
            check_query = """
            SELECT * 
            FROM savings_goals 
            WHERE joint_goal IS NOT NULL 
              AND (user_id = %s OR user_id = %s)
            """
            self.cursor.execute(check_query, (user_id_1, user_id_2))
            j_check=self.cursor.fetchone()
            if j_check:
                print("A joint goal already exists for these users")
                return False
            query = """
                UPDATE savings_goals 
                SET joint_goal = %s
                WHERE user_id=%s or user_id=%s
                """
            self.cursor.execute(query,(joint_goal,user_id_1,user_id_2,))
            self.connection.commit()
            print("Joint savings goal successfully created.")
            return True
        except Error as e:
            print(f"Error creating joint goal: {e}")
            self.connection.rollback()
            return False
    def contribute_to_goal(self, user_id, contribution_type, amount):
        """
        Contribute to either user or family goal with detailed error handling.
        """
        try:
            # Get family ID for the user
            family_id = self.get_family_id(user_id)
            if not family_id:
                return False, "Could not find family for this user."

            # Convert the contribution amount to Decimal to ensure precision
            amount = Decimal(str(amount))
            if amount <= 0:
                return False, "Contribution amount must be greater than zero."

            # Fetch current savings goal for the user
            query = "SELECT * FROM savings_goals WHERE family_id = %s AND user_id = %s"
            self.cursor.execute(query, (family_id, user_id))
            goal = self.cursor.fetchone()

            if not goal:
                return False, "No savings goal found for this user in the family."

            # Handle user contribution
            if contribution_type == 'user':
                new_user_target = goal['user_target_amount'] - amount
                if new_user_target < 0:
                    remaining = goal['user_target_amount']
                    return False, f"Contribution exceeds remaining target! Maximum allowed contribution is ${remaining}"

                # Update the user's savings goal
                update_query = """
                UPDATE savings_goals 
                SET user_target_amount = %s, 
                    usergoal_contributed_amount = usergoal_contributed_amount + %s 
                WHERE family_id = %s AND user_id = %s
                """
                self.cursor.execute(update_query, (new_user_target, amount, family_id, user_id))

            # Handle family contribution
            elif contribution_type == 'family':
                if goal['family_target_amount'] is None:
                    return False, "A family goal has not yet been created by your admin!"
                
                new_family_target = goal['family_target_amount'] - amount
                if new_family_target < 0:
                    remaining = goal['family_target_amount']
                    return False, f"Contribution exceeds family target! Maximum allowed contribution is ${remaining}"

                # Update the family target for all users in the same family
                update_query_family_target = """
                UPDATE savings_goals 
                SET family_target_amount = %s
                WHERE family_id = %s
                """
                self.cursor.execute(update_query_family_target, (new_family_target, family_id))

                # Update the contributing user's current amount towards the family goal
                update_query_user_contribution = """
                UPDATE savings_goals 
                SET familygoal_contributed_amount = familygoal_contributed_amount + %s
                WHERE family_id = %s AND user_id = %s
                """
                self.cursor.execute(update_query_user_contribution, (amount, family_id, user_id))

            else:
                return False, "Invalid contribution type. Choose 'user' or 'family'."

            # Commit the transaction to save changes
            self.connection.commit()
            return True, "Contribution successful!"

        except (Error, ValueError) as e:
            self.connection.rollback()
            return False, f"Error processing contribution: {str(e)}"

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
            self.cursor.execute(query, (family_id,))
            goals = self.cursor.fetchall()

            if goals:
                print("\n--- Family Savings Goals ---")
                for goal in goals:
                    print(f"\nUser ID: {goal['user_id']}")
                    print(f"User Goal: ${goal['user_goal']}")
                    print(f"User Target Remaining: ${goal['user_target_amount']}")
                    
                    # Only display family goal once
                    if goal == goals[0]:
                        print(f"Family Goal: ${goal['family_goal']}")
                        print(f"Family Target Remaining: ${goal['family_target_amount']}")
                        print(f"User Goal Contributed Amount: ${goal['usergoal_contributed_amount']}")
                        print(f"Family Goal Contributed Amount: ${goal['familygoal_contributed_amount']}")
                        print(f"Total Contributed Amount: ${goal['familygoal_contributed_amount']+goal['usergoal_contributed_amount']}")
                        print(f"Deadline: {goal['deadline']}")
            else:
                print("No savings goals found for this family.")

        except Error as e:
            print(f"Error displaying savings goal: {e}")
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
        self.cursor.execute(query)
        res = self.cursor.fetchall()

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
        self.cursor.execute(query1)
        res1 = self.cursor.fetchall()
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
                self.cursor.execute("SELECT user_goal FROM savings_goals WHERE user_id = %s", (user_id,))
            elif contribution_type == "family":
                self.cursor.execute("SELECT family_goal FROM savings_goals WHERE family_id = (SELECT family_id FROM users WHERE user_id = %s)", (user_id,))
            else:
                return True

            result = self.cursor.fetchone()
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
            self.cursor.execute(query, (user_id,))
            result = self.cursor.fetchone()
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


def main():
    manager = SavingsGoalsManager()
    while True:
        print("\n--- Unified Family Finance Tracker ---")
        print("1. Create User Savings Goal")
        print("2. Create Joint Savings Goal")
        print("3. Contribute to Savings Goal")
        print("4. Display Family Savings Goals")
        print("5. Update Savings Goal")
        print("6. Exit")

        choice = input("Enter your choice (1-6): ")

        try:
            if choice == '1':
                user_id = int(input("Enter User ID: "))
                
                # Check if user is admin
                if manager.is_admin(user_id):
                    user_goal = float(input("Enter User Goal Amount: "))
                    family_goal = float(input("Enter Family Goal Amount (optional, press enter to skip): ") or 0)
                    deadline = input("Enter Deadline (YYYY-MM-DD): ")
                    
                    # If family goal is 0, pass None
                    family_goal = family_goal if family_goal > 0 else None
                    manager.create_savings_goal(user_id, user_goal, deadline, family_goal)
                else:
                    user_goal = float(input("Enter User Goal Amount: "))
                    deadline = input("Enter Deadline (YYYY-MM-DD): ")
                    manager.create_savings_goal(user_id, user_goal, deadline)
            elif choice == '2':
                user_id_1 = int(input("Enter the first User ID: "))
                user_id_2 = int(input("Enter the second User ID: "))
                joint_goal=int(input("Enter the Joint Goal Amount: "))
                manager.joint_savings_goals(user_id_1,user_id_2,joint_goal)
            elif choice == '3':
                user_id = int(input("Enter User ID: "))
                contribution_type = input("Contribute to 'user' or 'family' goal: ").lower()
                amount = float(input("Enter contribution amount: "))
                
                manager.contribute_to_goal(user_id, contribution_type, amount)
                manager.track(user_id)

            elif choice == '4':
                manager.display_savings_goal()

            elif choice == '5':
                user_id = int(input("Enter User ID: "))
                manager.update_savings_goal(user_id)

            elif choice == '6':
                print("Exiting the application.")
                break

            else:
                print("Invalid choice. Please try again.")

        except ValueError:
            print("Invalid input. Please enter valid numbers.")

if __name__ == "__main__":
    main()
