# John Nguyen
# nguyenj1949@gmail.com
# 6/14/2024
# Spring 2024 CNE370
# Connects to one or both databases, executes queries and prints results about zipcodes and total wages
# This code runs on the Host OS and pulls database information from a virtual machine

import mysql.connector


# Database connection info
def connect_to_db():
    con = mysql.connector.connect(
        user='maxuser',
        password='maxpwd',
        host='10.0.0.36',  # Use VM IP
        port='4000'  # Specify port
    )
    return con


# Executes each query in 'queries' using given cursor and prints results with message
def print_results(cursor, queries, message):
    print(message)
    for query in queries:
        cursor.execute(query)
        results = cursor.fetchall()
        for row in results:
            print(row[0])
        print()  # Line break


# Executes query to find largest zipcode from zipcodes_one database and prints results
def query_1(cursor):
    query = "SELECT MAX(Zipcode) AS largest_zipcode FROM zipcodes_one.zipcodes_one"
    cursor.execute(query)
    result = cursor.fetchone()
    print(f"Largest zipcode in zipcodes_one: {result[0]}")


# Executes queries and returns zipcodes from both databases in Kentucky
def query_2():
    queries = [
        "SELECT Zipcode FROM zipcodes_one.zipcodes_one WHERE State = 'KY';",
        "SELECT Zipcode FROM zipcodes_two.zipcodes_two WHERE State = 'KY';"
    ]
    message = "List of Zipcodes from both databases in Kentucky"
    return queries, message


# Executes queries and returns zipcodes between 40000 and 41000 from both databases
def query_3():
    queries = [
        "SELECT Zipcode FROM zipcodes_one.zipcodes_one WHERE Zipcode BETWEEN 40000 AND 41000;",
        "SELECT Zipcode FROM zipcodes_two.zipcodes_two WHERE Zipcode BETWEEN 40000 AND 41000;"
    ]
    message = "List of Zipcodes from both databases between 40000 and 41000"
    return queries, message


# Executes queries and returns total wages from both databases in Pennsylvania
def query_4():
    queries = [
        "SELECT TotalWages FROM zipcodes_one.zipcodes_one WHERE State = 'PA';",
        "SELECT TotalWages FROM zipcodes_two.zipcodes_two WHERE State = 'PA';"
    ]
    message = "List of TotalWages from both databases in Pennsylvania"
    return queries, message


def main():
    conn = connect_to_db()
    cursor = conn.cursor()

    # Execute query 1
    query_1(cursor)

    # Perform queries 2, 3 and 4 and print results
    queries, message = query_2()
    print_results(cursor, queries, message)

    queries, message = query_3()
    print_results(cursor, queries, message)

    queries, message = query_4()
    print_results(cursor, queries, message)

    # Close cursor and connection
    cursor.close()
    conn.close()


if __name__ == "__main__":
    main()
    
