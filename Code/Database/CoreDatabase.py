import os
import sqlite3 as sql

dir_path = os.path.dirname(os.path.realpath(__file__))
connection = sql.connect(dir_path + "/Resources/ChrDatabase.db")
cursor = connection.cursor()


def int_input(prompt):
    """
    Repeatedly asks for an input until an integer is entered.
    :param prompt: the question an input is required for
    :type prompt: str
    :return: the integer input
    """
    output = None
    while output is None:
        try:
            output = int(input(prompt))
        except ValueError:
            print("The input entered was not an integer")
    return output


def float_input(prompt):
    """
    Repeatedly asks for an input until a float is entered.
    :param prompt: the question an input is required for
    :type prompt: str
    :return: the float input
    """
    output = None
    while output is None:
        try:
            output = float(input(prompt))
        except ValueError:
            print("The input entered was not a float")
    return output


def complete_setup():
    """
    Commits and closes the database connection, ensuring all edits are saved.
    """
    connection.commit()
    connection.close()


def view_tables():
    """
    Prints off the data of each table in the database.
    """
    cursor.execute("SELECT name FROM sqlite_master WHERE type = 'table';")
    tables = cursor.fetchall()
    output = ""
    counter = 0
    for table in sorted(tables):
        output += table[0] + ", "
        counter += 1
        if counter == 6:
            counter = 0
            output = output[:-2] + "\n"
    print(output)


def get_id(name, table):
    """
    Gets the id of a row from their table and name.
    :param name: the name of the row to be found
    :type name: str
    :param table: the table the row is located in
    :type table: str
    :return: the integer value of the data's id
    """
    name = name.replace("'", "''")
    cursor.execute("SELECT " + table[0].lower() + table[1:] + "Id from " + table + " WHERE "
                   + table[0].lower() + table[1:] + "Name='" + name + "'")
    try:
        return int(cursor.fetchone()[0])
    except TypeError:
        raise Exception("NoneType error with element name " + str(name) + " and table " + str(table))


def get_name(row_id, table):
    """
    Gets the name of a row from their table and id.
    :param row_id: the id of the row to be found
    :type row_id: int
    :param table: the table the row is located in
    :type table: str
    :return: the integer value of the data's id
    """
    cursor.execute("SELECT " + table[0].lower() + table[1:] + "Name from " + table + " WHERE "
                   + table[0].lower() + table[1:] + "Id=" + str(row_id))
    try:
        return cursor.fetchone()[0]
    except TypeError:
        raise Exception("NoneType error with element id " + str(row_id) + " and table " + str(table))


def get_id_from_table(table):
    """
    Converts a table string into an sql statement retrieving it's id.
    :param table: the name of the table to convert
    :type table: str
    :return: a string that, if called as an SQL statement, retrieves all id's from the table
    """
    return "SELECT " + table_to_id(table) + " FROM " + table


def table_to_id(table):
    """
    Converts a table string into it's id.
    :param table: the name of the table to convert
    :type table: str
    :return: a string that states the id name of the table
    """
    if len(table) > 0:
        tableId = table[:1].lower() + table[1:] + "Id"
    else:
        tableId = ""
    return tableId


def insert(sql_table_call, data):
    """
    Inserts data into a database, for code simplification.
    :param sql_table_call: part of the sql call, in the format <table>(<column>, <column>, ...)
    :type sql_table_call: str
    :param data: the data to insert into the database
    :type data: tuple
    """
    totalCall = f"INSERT INTO {sql_table_call} VALUES("
    for x in range(len(data)):
        totalCall += "?, "
    totalCall = totalCall[:-2] + ");"
    cursor.execute(totalCall, data)


def highest_id(table):
    """
    Gets the highest used id for a table, for code simplification.
    :param table: the table to get an id for
    :type table: str
    :return: the integer id value
    """
    cursor.execute("SELECT COUNT(*) FROM " + table)
    return cursor.fetchone()[0]
