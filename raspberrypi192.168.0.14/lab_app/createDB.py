import sqlite3


conn = sqlite3.connect('userdb.db')
c = conn.cursor()


c.execute(""" CREATE TABLE USERS (
            USERNAME TEXT,
            FIRSTNAME TEXT,
            LASTNAME TEXT,
            EMAIL TEXT,
            PASSWORD TEXT,
            ROLE TEXT,
            CONSTRAINT USERS_PK PRIMARY KEY (EMAIL),
            CONSTRAINT USERS_UK UNIQUE (USERNAME)
            )""")

conn.commit()
conn.close()