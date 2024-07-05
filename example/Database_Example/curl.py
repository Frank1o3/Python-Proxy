import sqlite3

conn = sqlite3.connect("example/Database_Example/Database.db")


# Function to add a new user to the database
def add_user(name, email, password):
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO user (name, email, password)
        VALUES (?, ?, ?)
    """,
        (name, email, password),
    )
    conn.commit()
    conn.close()


# Function to read a user by their ID
def read_user(user_id):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user


# Function to update a user's information
def update_user(user_id, name, email, password):
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE user
        SET name = ?, email = ?, password = ?
        WHERE id = ?
    """,
        (name, email, password, user_id),
    )
    conn.commit()
    conn.close()


# Function to delete a user by their ID
def delete_user(user_id):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()


# Function to check if a user exists by their email
def user_exists(email):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    return user is not None


def find_user_by_email_password(email, password):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM user WHERE email = ? AND password = ?", (email, password)
    )
    user = cursor.fetchone()
    conn.close()
    return user
