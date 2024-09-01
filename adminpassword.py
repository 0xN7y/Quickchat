import sqlite3

def dbcon():
    conn = sqlite3.connect('datap.db')
    conn.row_factory = sqlite3.Row
    return conn


print("\n\t Admin password chager\n\n")
np = input("Enter new admin password: ")

conn = dbcon()
conn.execute('UPDATE admin SET password = ? WHERE username ="admin"', (np,))
conn.commit()

print("\n[+] updated admin password  ")