from flask import Flask, render_template, request
import netifaces as ni
import sqlite3

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


if __name__ == "__main__":
    ip = ni.ifaddresses(ni.interfaces()[1])[2][0]["addr"]
    app.run(host=ip, port=8081, debug=False)
