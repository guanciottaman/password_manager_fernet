import sqlite3
from cryptography.fernet import Fernet

f = Fernet(open('password_manager.key', 'rb').read())
conn = sqlite3.connect('database.sqlite3')
c = conn.cursor()
c.execute('SELECT * FROM passwords WHERE website = "0" AND username = "user1" AND password = ?',
          (f.encrypt('Oettam09@'.encode()),))
stuff = c.fetchall()
print(stuff)