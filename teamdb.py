import sqlite3
from sqlite3 import Error
import os


def create_connection(db_file):
    """ Create a database connection to a SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(f"SQLite version: {sqlite3.version}")
        return conn
    except Error as e:
        print(e)
    return conn


def create_table(conn, create_table_sql):
    """ Create a table from the create_table_sql statement """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)


def main():
    database = "team_ems.db"

    sql_create_users_table = """ CREATE TABLE IF NOT EXISTS users (
                                    uid INTEGER PRIMARY KEY,
                                    name TEXT NOT NULL,
                                    role TEXT,
                                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                    enrolled INTEGER DEFAULT 0,
                                    attended INTEGER DEFAULT 0,
                                    last_attended_at TIMESTAMP
                                ); """

    # Create a database connection
    conn = create_connection(database)

    # Create table
    if conn is not None:
        create_table(conn, sql_create_users_table)
        print("Table 'users' created successfully.")
        conn.close()
    else:
        print("Error! Cannot create the database connection.")


if __name__ == '__main__':
    main()
