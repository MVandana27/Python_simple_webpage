from werkzeug.security import check_password_hash
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import mysql.connector
from werkzeug.security import generate_password_hash


app = Flask(__name__)
app.secret_key = "d#f3!gT9@7kLmZqX!2vW8*p$L"

# login credentials for user and admin
users = {
    "admin": "admin@123",
    "user": "user@123"
}

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Root@123',
    'database': 'mydb'
}

# Function to get a database connection


def get_db_connection():
    return mysql.connector.connect(**db_config)


@app.route("/")
def home():
    return redirect(url_for('login'))

# login page route


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Check hardcoded users
        if username in users and users[username] == password:
            session['username'] = username
            return redirect(url_for("admin_dashboard" if username == "admin" else "user_dashboard"))

        # Check DB users
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            # Check password
            if check_password_hash(user['password'], password):
                session['username'] = user['username']
                if user['role'] == "admin":
                    return redirect(url_for("admin_dashboard"))
                elif user['role'] == "user":
                    return redirect(url_for("user_dashboard"))
                else:
                    return render_template("login.html", error="Unknown user role.")
            else:
                return render_template("login.html", error="Incorrect password.")
        else:
            return render_template("login.html", error="User not found.")

    return render_template("login.html")


# to delete a mobile number in the database


@app.route("/delete/<int:number_id>", methods=["POST"])
def delete_number(number_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "DELETE FROM mobile_numbers WHERE id = %s", (number_id,))
        conn.commit()
    except Exception as e:
        print(f"Error deleting number: {e}")
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('dashboard'))

# to edit a mobile number in the database


@app.route("/edit/<int:number_id>", methods=["POST"])
def edit_number(number_id):
    new_number = request.form["number"]
    if not new_number.startswith("+91"):
        new_number = "+91" + new_number

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE mobile_numbers SET number = %s WHERE id = %s", (new_number, number_id))
        conn.commit()
    except Exception as e:
        print(f"Error updating number: {e}")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for("dashboard"))


# admin dashboard route to manage mobile numbers
@app.route("/admin", methods=["GET", "POST"])
def admin_dashboard():
    if session.get('username') != 'admin':
        return redirect(url_for('login'))

    status = None
    color = None
    mobile_value = ''

    if request.method == "POST":
        mobile_value = request.form.get("mobile")

        if mobile_value and mobile_value.isdigit() and len(mobile_value) == 10:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT number FROM mobile_numbers WHERE number = %s", (mobile_value,))
            existing = cursor.fetchone()

            if existing:
                status = "This mobile number already exists."
                color = "danger"
            else:
                cursor.execute(
                    "INSERT INTO mobile_numbers (number) VALUES (%s)", (mobile_value,))
                conn.commit()
                status = "Mobile number added successfully!"
                color = "success"

            cursor.close()
            conn.close()
        else:
            status = "Please enter a valid 10-digit number."
            color = "warning"

    # Always fetch the list of numbers to display
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, number FROM mobile_numbers ORDER BY id DESC")
    numbers = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("admin.html", numbers=numbers, status=status, color=color, mobile_value=mobile_value)


@app.route('/submit', methods=['POST'])
def submit_number():
    raw_number = request.form['number'].strip()

    # Ensure number starts with +91
    if not raw_number.startswith('+91'):
        if raw_number.startswith('91'):
            number = '+' + raw_number
        else:
            number = '+91' + raw_number
    else:
        number = raw_number

    # Connect to DB and check for duplicates
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM mobile_numbers WHERE number = %s", (number,))
    exists = cursor.fetchone()

    if exists:
        flash("Number already registered.", "warning")
    else:
        cursor.execute(
            "INSERT INTO mobile_numbers (number) VALUES (%s)", (number,))
        conn.commit()
        flash("Number added successfully.", "success")

    cursor.close()
    conn.close()
    return redirect(url_for('dashboard'))

# Dashboard route for admin to view and manage mobile numbers


@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, number FROM mobile_numbers ORDER BY id DESC")
    numbers = cursor.fetchall()
    cursor.close()
    conn.close()
    print(numbers)

    return render_template('dashboard.html', numbers=numbers)

# user dashboard route


@app.route("/debug_user/<username>")
def debug_user(username):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return jsonify(user) if user else "User not found", 200 if user else 404


@app.route("/user", methods=["GET", "POST"])
def user_dashboard():
    if session.get('username') != 'user':
        return redirect(url_for('login'))

    status = None
    color = None
    mobile_value = ''
    number_exists = False

    if request.method == "POST":
        mobile_value = request.form.get("mobile")

        if mobile_value and mobile_value.isdigit() and len(mobile_value) == 10:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT number FROM mobile_numbers")
            stored_numbers = [row[0] for row in cursor.fetchall()]
            cursor.close()
            conn.close()

            if mobile_value in stored_numbers:
                status = "This mobile number is already registered."
                color = "danger"
                number_exists = True
            else:
                status = "This is a new mobile number."
                color = "success"
                number_exists = False
        else:
            status = "Please enter a valid 10-digit mobile number."
            color = "warning"

    return render_template(
        "user.html",
        status=status,
        color=color,
        mobile_value=mobile_value,
        number_exists=number_exists
    )

# logout route to clear session


@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))


# route to create a new user (admin only)
@app.route("/create_user", methods=["GET", "POST"])
def create_user():
    if 'username' not in session or session['username'] != 'admin':
        return redirect(url_for('login'))  # only admin can access

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]  # admin or user

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                (username, hashed_password, role)
            )
            conn.commit()
            message = "User created successfully!"
        except Exception as e:
            message = f"Error: {e}"
        finally:
            cursor.close()
            conn.close()

        return render_template("create_user.html", message=message)

    return render_template("create_user.html")


if __name__ == "__main__":
    app.run(debug=True)
