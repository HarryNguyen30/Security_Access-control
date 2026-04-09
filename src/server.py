"""
This is our HTTP server, to run, just install Flask using the pip tool and run this file with `python server.py`.
In this, we provide some example functions showing what Flask can do, then the functions you should add authentication
and access control to.
"""

import os
import bcrypt
import string
import random
import requests
import time
from flask import Flask, request, redirect, url_for, jsonify

app = Flask(__name__)

_SRC_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.normpath(os.path.join(_SRC_DIR, "..", "data"))


def _data_file(name):
    return os.path.join(_DATA_DIR, name)


@app.get("/")
def index():
    return jsonify(
        {
            "service": "SENG2250 A3 — Flask auth & Biba access control",
            "status": "ok",
            "docs": "POST JSON to /verify_password, /send_mfa, /verify_mfa, /generate_token, etc.",
        }
    )


@app.get("/health")
def health():
    return jsonify({"status": "healthy"}), 200

# Security Levels
SECURITY_LEVELS = {
    "TOP_SECRET": 3,
    "SECRET": 2,
    "UNCLASSIFIED": 1
}

# Data structures for storing user details, tokens, MFA codes
users = {}
user_tokens = {}
token_timestamps = {}
user_mfa_codes = {}


#Generate a root user (Admin)
def initialize_server(): 
    # Generate a random password for root user, and hashing before storing
    random_password = generate_random_password(8)
    hashed_password = bcrypt.hashpw(random_password.encode(), bcrypt.gensalt())
    print(f"Generated root password: {random_password}")

    # Check users file, if it exists loading existing users
    if os.path.exists(_data_file("users.txt")):
        load_users_from_file()

        if "root" in users:
            users["root"]["password"] = hashed_password
        else:
            users["root"] = {
                "username": "root",
                "email": "seng2250a@gmail.com",
                "password": hashed_password,
                "group": "admin",
                "security_level": SECURITY_LEVELS["TOP_SECRET"],
            }
    else:
        users["root"] = {
                "username": "root",
                "email": "seng2250a@gmail.com",
                "password": hashed_password,
                "group": "admin",
                "security_level": SECURITY_LEVELS["TOP_SECRET"],
            }

    save_user_to_file()

#### Admin functionalities ####

# Admin console that performs actions based on admin input. Handling: add, modify, delete users 
@app.route("/admin_console", methods=["POST"])
def admin_console():
    data = request.get_json()
    username = data.get("username")
    token = data.get("token")

    # Validate token
    if username not in user_tokens or user_tokens[username] != token:
        return jsonify({"message": "Invalid or expired token!"}), 403
    
    # Check if the user belongs to admin group
    if users[username]["group"].lower() != "admin":
        return jsonify({"message": "Access denied. Admins only!"}), 403 
    
    # Perform action action based on admin's request
    action = data.get("action")
    if action == "add_user":
        return add_user()
    elif action == "modify_user":
        return modify_user()
    elif action == "delete_user":
        return delete_user()
    else:
        return jsonify({"message": "Invalid action!"}), 400

# Add a new user by the admin
def add_user():
    # Add a new user with specified username, email, group, and security level
    data = request.get_json()
    username = data.get("new_username")
    email = data.get("email")
    group = data.get("group")
    security_level = data.get("security_level").upper()

    # Ensure the user does not exist
    if username in users:
        return jsonify({"message": "User already exists!"}), 400
    
    # Generate a random password for root user, and hashing before storing
    random_password = generate_random_password(8)
    hashed_password = bcrypt.hashpw(random_password.encode(), bcrypt.gensalt())

    # Store the user's data
    users[username] = {
        "username": username,
        "email": email,
        "password": hashed_password,
        "group": group,
        "security_level": SECURITY_LEVELS[security_level],
    }

    # Send the new user's credentials via email
    send_simple_message(email,
   f"Welcome to the system of SENG2250, {username}",
   f"Dear {username},\nPlease find your account details below.\nUsername: {username}\nPassword: {random_password}")
    
    save_user_to_file()

    return jsonify({"message": "User added successfully! Email with credentials sent!"})

# Modify an exiting user by admin
def modify_user():
    # Modify group and security level
    data = request.get_json()
    username = data.get("modi_username")
    new_group = data.get("new_group")
    new_security_level = data.get("new_security_level")

    if username == "root":
        return jsonify({"message": "Modification of root user is not allowed."}), 403
    # Check if the user exists
    if username not in users:
        return jsonify({"message": "User not found"}), 404
    
    # Validate security level input
    if new_security_level.upper() not in SECURITY_LEVELS:
        return jsonify({"message": "Invalid security level provided"}), 400
    
    # Update user's group and security level
    users[username]["group"] = new_group
    users[username]["security_level"] = SECURITY_LEVELS[new_security_level.upper()]
    save_user_to_file()

    return jsonify({"message": "User modified successfully!"})

# Delete a user by admin
def delete_user():
    data = request.get_json()

    username = data.get("delete_username")
    
    # Check if the user exists
    if username not in users:
        return jsonify({"message": "User not found"}), 404
    
    # Remove the user from the system
    del users[username]
    user_tokens.pop(username, None) # Remove user's token
    user_mfa_codes.pop(username, None) # Remove user's mfa code
    save_user_to_file()
    return jsonify({"message": "User deleted successfully!"})

#### General functionalities ####

# Verify user password
@app.route('/verify_password', methods=['POST'])
def verify_password():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if username not in users:
        return jsonify({"message": "User not found!"}), 404
    
    # Verify the provided password matches the stored hasded password
    user = users[username]
    if bcrypt.checkpw(password.encode(), user["password"]):
        return jsonify({"message": "Password verified!"})

    return jsonify({"message": "Incorrect password"}), 401

# Send MFA code the the user's email
@app.route('/send_mfa', methods=['POST'])
def send_mfa_code():
    data = request.get_json()
    username = data.get("username")
    mfa_code = generate_mfa_code(6)
    user_mfa_codes[username] = mfa_code
    send_simple_message(users[username]["email"], "MFA Verification", f"Your MFA code is: {mfa_code}")
    return jsonify({"message": "Email with MFA code sent!"})

# Verify MFA code entered by user
@app.route('/verify_mfa', methods=['POST'])
def verify_mfa_code():
    data = request.get_json()
    username = data.get("username")
    mfa_code = data.get("mfa_code")

    if username not in users:
        return jsonify({"message": "User not found!"}), 404
    
    user = users[username]
    # Verify if the entered MFA matches the stored one
    if user_mfa_codes.get(username) == mfa_code:
        return jsonify({"success": True}),200
    return jsonify({"success": False}), 403

# Generate token for user
@app.route('/generate_token', methods=['POST'])
def generate_token():
    data = request.get_json()
    username = data.get("username")

    if username not in users:
        return jsonify({"message": "User not found!"}), 404
    
    # Generate a random token and store it
    token = generate_token_string(12)
    user_tokens[username] = token
    token_timestamps[token] = time.time() * 1000
    return jsonify({"token": token})

# Validate an existing token
@app.route('/validate_token', methods=['POST'])
def validate_token():
    data = request.get_json()
    token = data.get("token")

    if token not in token_timestamps:
        return jsonify({"message": "Token expired!"}), 401
    
    token_time = token_timestamps[token]
    time_now = time.time() * 1000
    # Token validity for 15 mins
    if (time_now -token_time) > (15 * 60 * 1000):
        del token_timestamps[token]
        return jsonify({"message": "Token expired!"}), 401
    return jsonify({"message": "Token is valid!"})


#### Endpoint functionalities ####

@app.route("/audit_expenses", methods=["POST"])
def audit_expenses():
    try:
        username = request.json.get('username')
        user_security_level = users[username]["security_level"]

        # Resource security level is provided on Table 1 in Assignment 3
        # Implementing Biba model
        if not can_read(user_security_level, SECURITY_LEVELS["TOP_SECRET"]):
            return jsonify({"message": "Access denied"}), 403
        
        # Check file exists or not, and return data in file
        expense_data = ensure_file_exists(_data_file("expenses.txt"))

        if not expense_data:
            return jsonify({"message": "No expenses found"}), 404
        
        return jsonify({"expenses": expense_data}), 200
    
    except KeyError:
        return jsonify({"message": "User not found!"}), 404
    except Exception as e:
        print(f"Error in audit_expenses: {e}")
        return jsonify({"message": "An error occurred while auditing expenses"}), 500

@app.route("/add_expense", methods=["POST"])
def add_expense():
    try:
        data = request.get_json()
        username = data.get('username')
        expense_data = data.get('expense_data')

        # Check blank input
        if not expense_data or not expense_data.strip():
            return jsonify({"message": "Expense data cannot be blank!"}), 400
        
        # Get user security level
        user_security_level = users[username]["security_level"]
        # Implementing Biba model
        if not can_write(user_security_level, SECURITY_LEVELS["TOP_SECRET"]):
            return jsonify({"message": "Access denied"}), 403
        # Check file exists or not
        ensure_file_exists(_data_file("expenses.txt"))

        # Add data to file
        with open(_data_file("expenses.txt"), "a") as f:
            f.write('\n'+ expense_data )
        return jsonify({"message": "Expense added"}), 200
    
    except KeyError:
        return jsonify({"message": "User not found!"}), 404
    except Exception as e:
        print(f"Error in add_expense: {e}")
        return jsonify({"message": "An error occurred while adding expenses"}), 500


@app.route("/audit_timesheets", methods=["POST"])
def audit_timesheets():
    try: 
        username = request.json.get('username')

        user_security_level = users[username]["security_level"]

        if not can_read(user_security_level, SECURITY_LEVELS["TOP_SECRET"]):
            return jsonify({"message": "Access denied"}), 403
        
        timesheet_data = ensure_file_exists(_data_file("timesheets.txt"))

        if not timesheet_data:
            return jsonify({"message": "No timesheet found"}), 404
        
        return jsonify({"timesheet": timesheet_data}), 200
    except KeyError:
        return jsonify({"message": "User not found!"}), 404
    except Exception as e:
        print(f"Error in audit_timesheets: {e}")
        return jsonify({"message": "An error occurred while auditing the timesheet"}), 500
 

@app.route("/submit_timesheet", methods=["POST"])
def submit_timesheet():
    try: 
        data = request.get_json()
        username = data.get("username")
        timesheet_data = data.get('timesheet_data')

        if not timesheet_data or not timesheet_data.strip():
            return jsonify({"message": "Timesheet data cannot be blank!"}), 400

        user_security_level = users[username]["security_level"]

        if not can_write(user_security_level, SECURITY_LEVELS["TOP_SECRET"]):
            return jsonify({"message": "Access denied"}), 403
        
        ensure_file_exists(_data_file("timesheets.txt"))

        with open(_data_file("timesheets.txt"), "a") as f:
            f.write('\n' + timesheet_data)

        return jsonify({"message": "Timesheet submitted"}), 200
    except KeyError:
        return jsonify({"message": "User not found!"}), 404
    except Exception as e:
        print(f"Error in submit_timesheet: {e}")
        return jsonify({"message": "An error occurred while submiting the timesheet"}), 500



@app.route("/view_meeting_minutes", methods=["POST"])
def view_meeting_minutes():
    try: 
        username = request.json.get('username')

        user_security_level = users[username]["security_level"]

        if not can_read(user_security_level, SECURITY_LEVELS["SECRET"]):
            return jsonify({"message": "Access denied"}), 403
        
        meeting_minutes_data = ensure_file_exists(_data_file("meeting_minutes.txt"))

        if not meeting_minutes_data:
            return jsonify({"message": "No meeting minute found"}), 404
        
        return jsonify({"meeting_minutes": meeting_minutes_data}), 200
    except KeyError:
        return jsonify({"message": "User not found!"}), 404
    except Exception as e:
        print(f"Error in view_meeting_minutes: {e}")
        return jsonify({"message": "An error occurred while viewing meeting minutes"}), 500



@app.route("/add_meeting_minutes", methods=["POST"])
def add_meeting_minutes():
    try: 
        data = request.get_json()
        username = data.get("username")
        meeting_minutes_data = data.get('meeting_minutes_data')

        if not meeting_minutes_data or not meeting_minutes_data.strip():
            return jsonify({"message": "Meeting minutes data cannot be blank!"}), 400
        
        user_security_level = users[username]["security_level"]
        if not can_write(user_security_level, SECURITY_LEVELS["SECRET"]):
            return jsonify({"message": "Access denied"}), 403
        
        ensure_file_exists(_data_file("meeting_minutes.txt"))

        with open(_data_file("meeting_minutes.txt"), "a") as f:
            f.write('\n'+ meeting_minutes_data )

        return jsonify({"message": "Meeting minutes submitted"}), 200
    except KeyError:
        return jsonify({"message": "User not found!"}), 404
    except Exception as e:
        print(f"Error in add_meeting_minutes: {e}")
        return jsonify({"message": "An error occurred while adding the meeting minutes"}), 500


@app.route("/view_roster", methods=["POST"])
def view_roster():
    try: 
        username = request.json.get('username')

        user_security_level = users[username]["security_level"]
        if not can_read(user_security_level, SECURITY_LEVELS["UNCLASSIFIED"]):
            return jsonify({"message": "Access denied"}), 403
        
        if not os.path.exists(_data_file("roster.txt")):
            print("No roster file found, creating one.")
            with open(_data_file("roster.txt"), "w") as f:
                pass

        with open(_data_file("roster.txt"), "r") as f:
            roster_data = f.read()

        if not roster_data:
            return jsonify({"roster": "No roster found"}), 404
        
        return jsonify({"roster": roster_data}), 200
    except KeyError:
        return jsonify({"message": "User not found!"}), 404
    except Exception as e:
        print(f"Error in view_roster: {e}")
        return jsonify({"message": "An error occurred while viewing the roster"}), 500



@app.route("/roster_shift", methods=["POST"])
def roster_shift():
    try: 
        data = request.get_json()
        username = data.get("username")
        roster_data = data.get('roster_data')

        if not roster_data or not roster_data.strip():
            return jsonify({"message": "Roster data cannot be blank!"}), 400
        
        user_security_level = users[username]["security_level"]
        if not can_write(user_security_level, SECURITY_LEVELS["UNCLASSIFIED"]):
            return jsonify({"message": "Access denied"}), 403
        
        if not os.path.exists(_data_file("roster.txt")):
            print("No rosters file found, creating one.")
            with open(_data_file("roster.txt"), "w") as f:
                pass

        with open(_data_file("roster.txt"), "a") as f:
            f.write('\n' + roster_data )

        return jsonify({"message": "Shift rosted"}), 200
    except KeyError:
        return jsonify({"message": "User not found!"}), 404
    except Exception as e:
        print(f"Error in roster_shift: {e}")
        return jsonify({"message": "An error occurred while rostering shift"}), 500

#Help function
# Generates a random password in given length
def generate_random_password(length):
    char = string.ascii_letters + string.digits
    password = ''.join(random.choice(char) for i in range (length))
    return password

# Generate a random MFA code
def generate_mfa_code(length):
    mfa_code = ''.join(random.choice(string.digits) for i in range (length))
    return mfa_code

# Generate a random token string
def generate_token_string(length):
    char = string.ascii_letters + string.digits + string.punctuation
    token = ''.join(random.choice(char) for i in range (length))
    return token

# Send email via Mailgun (set MAILGUN_API_KEY, MAILGUN_DOMAIN, MAILGUN_FROM in production)
def send_simple_message(to_email, subject, text):
    api_key = os.environ.get("MAILGUN_API_KEY")
    domain = os.environ.get("MAILGUN_DOMAIN")
    from_addr = os.environ.get("MAILGUN_FROM")
    if not api_key or not domain:
        print(f"[email skipped — set MAILGUN_* env] To: {to_email} | {subject}\n{text}")
        return None
    if not from_addr:
        from_addr = f"SENG2250 <noreply@{domain}>"
    return requests.post(
        f"https://api.mailgun.net/v3/{domain}/messages",
        auth=("api", api_key),
        data={
            "from": from_addr,
            "to": [to_email],
            "subject": subject,
            "text": text,
        },
        timeout=30,
    )

#Ensure file exists, if it doesn't, create new one
def ensure_file_exists(file_path):
    """Ensure that the file exists and return its contents or create an empty one if necessary."""
    try:
        if not os.path.exists(file_path):
            print(f"No file found at {file_path}, creating one.")
            with open(file_path, 'w') as f:
                pass  # Creates an empty file

        with open(file_path, 'r') as f:
            return f.read().strip()  # Return contents, empty if file is blank
        
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None  # Return None if there's an error

# Save user details    
def save_user_to_file():
    with open(_data_file("users.txt"), "w") as f:
        for username, user_info in users.items():
            f.write(f"{username}: {user_info}\n")

# Load user details
def load_users_from_file():
    with open(_data_file("users.txt"), "r") as f:
        for line in f:
            username, user_info_str = line.strip().split(": ", 1)
            user_info = eval(user_info_str)
            users[username] = user_info

### Based on Biba access control model        
#No read down
def can_read(user_security_level, resource_security_level):
    return user_security_level <= resource_security_level
#No write up
def can_write(user_security_level, resource_security_level):
    return user_security_level >= resource_security_level

def _startup():
    os.makedirs(_DATA_DIR, exist_ok=True)
    initialize_server()


_startup()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "2250"))
    host = os.environ.get("HOST", "127.0.0.1")
    app.run(host=host, port=port)

