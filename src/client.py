import os
import requests
import json

# Server URL: export SERVER_URL=https://your-app.onrender.com for remote deploy
BASE_URL = os.environ.get("SERVER_URL", "http://127.0.0.1:2250").rstrip("/")

def main():
    print("Welcome to the Portal.")
    # Users have choice to login to Admin, Client or Exit system 
    while True:
        print("\nAre you: ")
        print("1. Admin")
        print("2. Client")
        print("3. Exit")
        try:
            role_choice = int(input("Enter choice: "))

            if role_choice == 1:
                admin_menu() # Admin section
            elif role_choice == 2:
                username,token = client_login() #Client login, get username and token to use client's funtion
                if username and token: #Proceed when login successful
                    client_menu(username, token)
            elif role_choice == 3:
                print("Exiting...")
                break
            else:
                print("Invalid choice. Please try again.")
        except ValueError:
            print("Please enter a valid number.")

# Admin function (Admin console)
def admin_menu():
    token = None
    username = None

    print("Welcome to the Admin Console.")

    while True:
        display_admin_menu()
        try:
            selection = int(input("Enter your choice: "))

            # Requires a valid token for any operation 
            if requires_admin(selection) and not validate_token(token, username):
                print("Permission denied. Please login as admin to use that function.")
                continue
            
            # Admin login
            if selection == 1: 
                username = input("Please enter your username: ")
                password = input("Please enter your password: ")
                if verify_password(username, password):
                    token = generate_token(username) #Generate token when successfully Login
                    print("Logged in successfully. Token generated!")
                else:
                    print("Invalid username or password.")
            # Adding a new user
            elif selection == 2:
                new_user = input("Please enter your username: ")
                email = input("Please enter your email: ")
                group = input(f"Enter group for {new_user}: ")
                security_level = input(f"Enter new security level (TOP_SECRET / SECRET / UNCLASSIFIED): ")
                # Create action for sending to admin_console on server side
                action = {"username": username , "token": token, "action": "add_user", "new_username": new_user, "email": email, "group": group,"security_level": security_level}
                print(requests.post(f"{BASE_URL}/admin_console", json=action).json().get("message"))
            # Modifying an existing user
            elif selection == 3:
                modi_user = input("Enter username to modify: ")
                new_group = input(f"Enter new group for {modi_user}: ")
                new_security_level = input(f"Enter new security level (TOP_SECRET / SECRET / UNCLASSIFIED): ")
                action = {"username": username , "token": token, "action": "modify_user", "modi_username": modi_user, "new_group": new_group, "new_security_level": new_security_level}
                print(requests.post(f"{BASE_URL}/admin_console", json=action).json().get("message"))
            # Deleting a user
            elif selection == 4:
                del_user = input("Enter username to delete: ")
                action = {"username": username , "token": token, "action": "delete_user", "delete_username": del_user}
                print(requests.post(f"{BASE_URL}/admin_console", json=action).json().get("message"))
            # Admin logout
            elif selection == 5:
                print(f"{username} logged out successfully! ")
                token = None
                username = None
                break
            # Exiting 
            elif selection == 6:
                print("Exiting...")
                exit(0)
            else:
                print("Invalid selection! Please choose again.")
        except ValueError:
            print("Please enter a valid number.")

def requires_admin(choice):
    return choice >= 2 and choice <= 4
# Admin menu display
def display_admin_menu():
    print("\nPlease select an operation:")
    print("1. Login")
    print("2. Add User")
    print("3. Modify User")
    print("4. Delete User")
    print("5. Logout")
    print("6. Exit")
    
# Client login: handling username, password and MFA authentication
def client_login():
    username = input("Enter your username: ")
    password = input("Enter your password: ")

    if verify_password(username, password):
        send_mfa_code(username) # Send MFA code to user email
        mfa_code = input("Enter MFA code sent to your email: ")
        if verify_mfa_code(username, mfa_code):
            token = generate_token(username) # Generate token after verify password and mfa code
            print("Logged in successfully!")
            return username, token
        else:
            print("Failed to login. Please check your MFA code.")
    else:
        print("Incorrect password.")
    
    return None, None

# Client menu: handling client's operations (expemses, timesheets, etc.)
def client_menu(username,token):
    while True:

        display_client_menu(username)
        
        try:
        
            selection = int(input("Enter your choice: "))
            operations = {
                1: audit_expenses,
                2: add_expenses,
                3: audit_timesheets,
                4: submit_timesheet,
                5: view_meeting_minutes,
                6: add_meeting_minutes,
                7: view_roster,
                8: roster_shift,
                9: "logout",
                10: "exit"
            }
            if selection in operations:
                if selection == 9:
                    print(f"{username} logged out successfully")
                    username = None
                    token = None
                    break
                elif selection == 10:
                    print("Exiting...")
                    exit(0)
                else:
                    result = operations[selection](username, token) # Call the relavant operation
                    print(result)
            else:
                print("Invalid selection! Please choose again.")
            
        except ValueError:
            print("Please enter a valid number.")

# Client menu display
def display_client_menu(username):
    print(f"\nWelcome, {username}")
    print("1. Audit Expenses")
    print("2. Add Expenses")
    print("3. Audit Timesheets")
    print("4. Submit Timesheets")
    print("5. View Meeting Minutes")
    print("6. Add Meeting Minutes")
    print("7. View Roster")
    print("8. Roster Shift")
    print("9. Logout")
    print("10. Exit")



#Help functions for server(API) requests and validation (Interacting with server side)

# Verify password via server
def verify_password(username, password):
    response = requests.post(f"{BASE_URL}/verify_password", json={"username": username, "password": password})
    return response.status_code == 200

# Verify MFA code via server
def verify_mfa_code(username, mfa_code):
    response = requests.post(f"{BASE_URL}/verify_mfa", json={"username": username, "mfa_code": mfa_code})
    return response.status_code == 200

# Generate and retrieve token via server
def generate_token(username):
    response = requests.post(f"{BASE_URL}/generate_token", json={"username": username})
    if response.status_code == 200:
        return response.json().get("token")
    return None

# Validate token via server
def validate_token(token, username):
    response = requests.post(f"{BASE_URL}/validate_token", json={"token": token})
    if response.status_code == 200:
        return True
    elif response.status_code == 401:
        print("Session expired! Please log in again to use those function.")
    return False

# Send MFA code via server
def send_mfa_code(username):
    response = requests.post(f"{BASE_URL}/send_mfa", json={"username": username})
    return response.status_code == 200

# Call audit expenses
def audit_expenses(username,token):
    if not validate_token(token, username):
        return ""
    response = requests.post(f"{BASE_URL}/audit_expenses", json={"username": username})
    if response.status_code == 404:
        return response.json().get("message")
    elif response.status_code == 403:
        return response.json().get("message")
    return response.json().get("expenses")

# Call to add expenses
def add_expenses(username, token):
    if not validate_token(token, username):
        return ""
    expense_data = input("Enter the expense details: ")
    # Send request to server with data in json format
    response = requests.post(f"{BASE_URL}/add_expense", json={"username": username,"expense_data": expense_data})
    if response.status_code == 403:
        return "Access denied"
    return response.json().get("message")

# Call to audit timesheets
def audit_timesheets(username,token):
    if not validate_token(token, username):
        return ""
    response = requests.post(f"{BASE_URL}/audit_timesheets", json={"username": username})
    if response.status_code == 404:
        return response.json().get("message")
    elif response.status_code == 403:
        return response.json().get("message")
    return response.json().get("timesheet")

# Call to submit timesheet
def submit_timesheet(username,token):
    if not validate_token(token, username):
        return ""
    timesheet_data = input("Enter the timesheet: ")
    response = requests.post(f"{BASE_URL}/submit_timesheet", json={"username": username,"timesheet_data": timesheet_data})
    if response.status_code == 403:
        return "Access denied"
    return response.json().get("message")

# Call to view meeting minutes
def view_meeting_minutes(username,token):
    if not validate_token(token, username):
        return ""
    response = requests.post(f"{BASE_URL}/view_meeting_minutes", json={"username": username})
    if response.status_code == 404:
        return response.json().get("message")
    elif response.status_code == 403:
        return response.json().get("message")
    return response.json().get("meeting_minutes")

# Call to add meeting minutes
def add_meeting_minutes(username,token):
    if not validate_token(token, username):
        return ""
    meeting_minutes_data = input("Enter the meeting minutes details: ")
    response = requests.post(f"{BASE_URL}/add_meeting_minutes", json={"username": username,"meeting_minutes_data": meeting_minutes_data})
    if response.status_code == 403:
        return response.json().get("message")
    return response.json().get("message")

# Call to view the roster
def view_roster(username,token):
    if not validate_token(token, username):
        return ""
    response = requests.post(f"{BASE_URL}/view_roster", json={"username": username})
    if response.status_code == 404:
        return response.json().get("message")
    elif response.status_code == 403:
        return response.json().get("message")
    return response.json().get("roster")

# Call to update roster shift
def roster_shift(username,token):
    if not validate_token(token, username):
        return ""
    roster_data = input("Enter the roster details: ")
    response = requests.post(f"{BASE_URL}/roster_shift", json={"username": username,"roster_data": roster_data})
    if response.status_code == 403:
        return response.json().get("message")
    return response.json().get("message")



if __name__ == "__main__":
    main()
