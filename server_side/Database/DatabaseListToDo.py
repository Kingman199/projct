

class DatabaseListToDo:

    def __init__(self, conn):
        self.conn = conn
        self.createDb()

    def createDb(self):
        # Create Projects table if it doesn't exist
        self.conn.execute('''CREATE TABLE IF NOT EXISTS LISTS
                                     (TaskID INTEGER PRIMARY KEY AUTOINCREMENT,
                                      TaskName TEXT NOT NULL,
                                      IsChecked BOOLEAN,
                                      ClientID INTEGER,
                                      FOREIGN KEY (ClientID) REFERENCES CLIENTS(ID)
                                      )''')
        print("LIST_TO_DO table created successfully")


    def add_list_item(self, item):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO LISTS (TaskName, IsChecked) VALUES (?, ?)", (item, False))
        self.conn.commit()

    def update_list_checked(self, item, isCheck):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE LISTS SET IsChecked=? WHERE TaskName=?", (isCheck, item))
        self.conn.commit()

    def del_list_item(self, item):
        cursor = self.conn.cursor()
        query = "DELETE FROM LISTS WHERE TaskName=?"
        cursor.execute(query, (item,))
        self.conn.commit()

    def read_list(self):
        cursor = self.conn.cursor()
        query = "SELECT TaskName, IsChecked FROM LISTS"
        cursor.execute(query)
        # Fetch all rows from the query result
        rows = cursor.fetchall()
        result = ""
        print("\n\n\t\tLIST TO Do")
        print("-----------------------------")
        # Print or return the list of names
        for row in rows:
            print(row[0], row[1])
            result += f"{row[0]}:{row[1]}, "

        print("-----------------------------")
        # Close the cursor if done
        cursor.close()
        return result
