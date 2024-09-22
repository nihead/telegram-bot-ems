import sqlite3
from sqlite3 import Error
import os


def create_connection():
    """ Create a database connection to a SQLite database """
    conn = None
    c = None
    try:
        conn = sqlite3.connect("team_ems.db")
        c = conn.cursor()
        return conn, c
    except Error as e:
        print(e)
        return conn, c


def create_table(conn, create_table_sql):
    """ Create a table from the create_table_sql statement """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)

def is_db():
    return os.path.isfile("./team_ems.db")


def table_exists(table_name):
    # Connect to the SQLite database
    conn = sqlite3.connect("team_ems.db")
    cursor = conn.cursor()

    # Query to check if the table exists in the database
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))

    # Fetch one result, if exists
    table = cursor.fetchone()

    # Close the connection
    conn.close()

    # Return True if table exists, else False
    return table is not None


def insert_new_user(user, conn = None) -> bool:
    """ Insert a new user into the users table """
    sql = ''' INSERT INTO users(uid, name, role)
              VALUES(?,?,?) '''
    try:
        if not conn:
            print(f"Connection makes {conn}")
            conn = sqlite3.connect("team_ems.db")
        cur = conn.cursor()
        cur.execute(sql, user)
        conn.commit()
        return True
    except Error as e:
        print(f"Error occurred {e}")
        return False
    finally:
        conn.close()

def read_all():
    conn, c = create_connection()
    ###
    c.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = c.fetchall()
    print(tables)
    ###

    # curser = conn.cursor()
    c.execute("SELECT * FROM users")
    return c.fetchall()


def db_init():
    if not is_db():
        db_init()
    else:
        print("Db found")


def main():
    # Tables
    tables = [""" CREATE TABLE IF NOT EXISTS users (
                                                uid INTEGER PRIMARY KEY,
                                                name TEXT NOT NULL,
                                                role TEXT,
                                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                                enrolled INTEGER DEFAULT 0,
                                                attended INTEGER DEFAULT 0,
                                                last_attended_at TIMESTAMP
                                            );""",
              """ CREATE TABLE IF NOT EXISTS schedules (
                                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                                        place TEXT,
                                        from_time TIME,
                                        to_time TIME,
                                        team_qty INTEGER,
                                        reserve_qty INTEGER,
                                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                    ); """,
              """ CREATE TABLE IF NOT EXISTS team_list (
                                                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                      uid INTEGER,
                                                      sid INTEGER,
                                                      on_team BOOLEAN,
                                                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                                      FOREIGN KEY (uid) REFERENCES users(uid),
                                                      FOREIGN KEY (sid) REFERENCES schedules(id)
                                                  ); """,
              ]
    try:
        conn, c = create_connection()
        for table in tables:
            c.execute(table)
        admin = insert_new_user((498123938, 'noHead', 'admin'))
    except Error as e:
        print("Error! Cannot create the database connection.")
        print(e)
    finally:
        conn.close()


if __name__ == '__main__':
    if not is_db():
        db_init()
    print(read_all())
