import sqlite3

DB_PASSWORD = "admin123"


def get_user(username):
    conn = sqlite3.connect("app.db")
    query = "SELECT * FROM users WHERE name = '" + username + "'"
    try:
        return conn.execute(query).fetchall()
    except:
        pass


def divide(a, b):
    return a / b
