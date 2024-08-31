from flask import Flask, render_template, request
import sqlite3
import psutil
import socket

app = Flask(__name__)


# Database connection
def get_db_connection():
    conn = sqlite3.connect("example/Database_Example/users.db")
    conn.row_factory = sqlite3.Row  # Access rows by column names
    return conn


# Initialize the database schema if not exists
def init_db():
    with app.app_context():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            );
        """
        )
        conn.commit()
        conn.close()

def get_ip():
    interfaces = psutil.net_if_addrs()
    ethernet_ip = None
    wireless_ip = None

    for name, nit_address in interfaces.items():
        for address in nit_address:
            if address.family == socket.AF_INET:
               if "eth" in name.lower() or "en" in name.lower():
                  ethernet_i = address.address
               elif "wlan" in name.lower() or "wl" in name.lower():
                   wireless_ip = address.address
    if ethernet_ip:
       return ethernet_ip
    elif wireless_ip:
       return wireless_ip
    else:
       return "127.0.0.1"

def get_port():
    for port in range(8080,65535):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
             try:
                s.bind(("",port))
                return port
             except socket.error:
                continue
    raise RuntimeError("No available port found")

init_db()  # Call init_db to ensure the table is created when the app starts

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if user already exists
        cursor.execute("SELECT * FROM user WHERE email = ?", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            return "User already exists! Please log in."
        else:
            cursor.execute(
                "INSERT INTO user (name, email, password) VALUES (?, ?, ?)",
                (name, email, password),
            )
            conn.commit()
            conn.close()
            return "User created successfully! Please log in."

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        conn = get_db_connection()
        cursor = conn.cursor()

        # Find user by email and password
        cursor.execute(
            "SELECT * FROM user WHERE email = ? AND password = ?", (email, password)
        )
        user = cursor.fetchone()

        conn.close()

        if user:
            return f"Hi {user['name']}! You are logged in."
        else:
            return "Invalid email or password. Please try again."

    return render_template("login.html")


@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    if request.method == "GET":
        return render_template("change_password.html")
    elif request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        new_password = request.form["new_password"]
        conn = get_db_connection()
        cursor = conn.cursor()

        # Verify user exists by email and current password
        cursor.execute(
            "SELECT * FROM user WHERE email = ? AND password = ?", (email, password)
        )
        user = cursor.fetchone()

        if user:
            user_id = user["id"]

            # Update user's password
            cursor.execute(
                "UPDATE user SET password = ? WHERE id = ?", (new_password, user_id)
            )
            conn.commit()
            conn.close()
            return f"Password updated successfully for user: {user['name']}."

        else:
            conn.close()
            return "Invalid email or current password. Password not updated."

    # Handle other HTTP methods (PUT, DELETE, etc.) if necessary
    return "Method not allowed."


@app.route("/change_email", methods=["GET", "POST"])
def change_email():
    if request.method == "GET":
        return render_template("change_email.html")
    elif request.method == "POST":
        name = request.form["name"]
        password = request.form["password"]
        new_email = request.form["new_email"]
        conn = get_db_connection()
        cursor = conn.cursor()

        # Verify user exists by name and current password
        cursor.execute(
            "SELECT * FROM user WHERE name = ? AND password = ?", (name, password)
        )
        user = cursor.fetchone()

        if user:
            user_id = user["id"]

            # Check if new email already exists
            cursor.execute("SELECT * FROM user WHERE email = ?", (new_email,))
            existing_user = cursor.fetchone()

            if existing_user:
                conn.close()
                return "Email already in use. Please choose a different one."
            else:
                # Update user's email
                cursor.execute(
                    "UPDATE user SET email = ? WHERE id = ?", (new_email, user_id)
                )
                conn.commit()
                conn.close()
                return f"Email updated successfully for user: {user['name']}."

        else:
            conn.close()
            return "Invalid name or password. Email not updated."

    # Handle other HTTP methods (PUT, DELETE, etc.) if necessary
    return "Method not allowed."


@app.route("/delete_account", methods=["GET", "POST"])
def delete_account():
    if request.method == "GET":
        return render_template("delete_account.html")
    elif request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if user exists
        cursor.execute(
            "SELECT * FROM user WHERE name = ? AND email = ? AND password = ?",
            (name, email, password),
        )
        existing_user = cursor.fetchone()

        if existing_user:
            # Delete the user's data
            cursor.execute("DELETE FROM user WHERE id = ?", (existing_user["id"],))
            conn.commit()
            conn.close()
            return "Account Deleted!"
        else:
            conn.close()
            return "Account not found or incorrect credentials. No account deleted."

    # Handle other HTTP methods (PUT, DELETE, etc.) if necessary
    return "Method not allowed."


if __name__ == "__main__":
    ip = get_ip()
    port = get_port()
    app.run(host=ip, port=port, debug=False)
