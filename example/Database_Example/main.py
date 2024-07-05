from flask import Flask, render_template, request
import netifaces as ni
import sqlite3


def get_ip_addresses():
    interfaces = ni.interfaces()
    non_loopback_interfaces = [
        interface for interface in interfaces if not interface.startswith("lo")
    ]
    ip_addresses = []
    for interface in non_loopback_interfaces:
        addrs = ni.ifaddresses(interface)
        ipv4_addrs = addrs.get(ni.AF_INET, [])
        ip_addresses.extend(ipv4_addrs)
    return ip_addresses

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


if __name__ == "__main__":
    ip = get_ip_addresses()[0]["addr"]
    app.run(host=ip, port=8082, debug=False)
