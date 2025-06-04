import sqlite3
import hashlib

class DatabaseClients:
    def __init__(self, conn):
        self.conn = conn
        self.createDb()

    def createDb(self):
        # region Clients TABLE

        self.conn.execute('''CREATE TABLE IF NOT EXISTS CLIENTS
                             (ID INTEGER PRIMARY KEY AUTOINCREMENT,
                              Username TEXT NOT NULL UNIQUE,
                              PASSW TEXT NOT NULL,
                              EMAIL TEXT NOT NULL UNIQUE,
                              ROLE_ID INTEGER DEFAULT 1,
                              MANAGER_ID INTEGER,
                              FOREIGN KEY (ROLE_ID) REFERENCES ROLES(ID_ROLE)
                              )''')
        print("CLIENTS table created successfully")
        # endregion

        #region Friends TABLE
        self.conn.execute('''CREATE TABLE IF NOT EXISTS FRIENDS
                             (ID INTEGER PRIMARY KEY AUTOINCREMENT,
                              ClientID INTEGER NOT NULL,
                              FriendID INTEGER NOT NULL,
                              ProjectID INTEGER,  -- Shared project ID 
                              FOREIGN KEY (ClientID) REFERENCES CLIENTS(ID),
                              FOREIGN KEY (FriendID) REFERENCES CLIENTS(ID),
                              FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID) ON DELETE CASCADE,
                              UNIQUE (ClientID, FriendID, ProjectID)
                              )''')
        print("FRIENDS table created successfully")

        self.conn.execute('''CREATE TABLE IF NOT EXISTS FRIEND_REQUESTS (
                                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                                SenderID INTEGER NOT NULL,
                                ReceiverEmail TEXT NOT NULL,
                                Status TEXT DEFAULT 'Pending',
                                FOREIGN KEY (SenderID) REFERENCES CLIENTS(ID)
                            )''')
        print("FRIEND_REQUESTS table created successfully")
        # endregion

        self.conn.execute('''CREATE TABLE IF NOT EXISTS ROLES (
                                ID_ROLE INTEGER PRIMARY KEY AUTOINCREMENT,
                                NAME TEXT NOT NULL UNIQUE
                            );''')

        # Check if the table has any rows
        cursor = self.conn.execute("SELECT COUNT(*) FROM ROLES")
        count = cursor.fetchone()[0]

        if count == 0:
            self.conn.execute("INSERT INTO ROLES (NAME) VALUES (?)", ("Guest",))
            self.conn.execute("INSERT INTO ROLES (NAME) VALUES (?)", ("Worker",))
            self.conn.execute("INSERT INTO ROLES (NAME) VALUES (?)", ("Manager",))
            self.conn.commit()
        # ID	NAME
        # 1	    Guest
        # 2 	Worker
        # 3	    Manager
        print("Role table created successfully")

        # region Workers TABLE
        self.conn.execute('''CREATE TABLE IF NOT EXISTS WORKERS (
                                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                                    ManagerID INTEGER NOT NULL,
                                    WorkerID INTEGER NOT NULL,
                                    ProjectID INTEGER,  -- Optional, same idea as friends
                                    FOREIGN KEY (ManagerID) REFERENCES CLIENTS(ID),
                                    FOREIGN KEY (WorkerID) REFERENCES CLIENTS(ID),
                                    FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID) ON DELETE CASCADE,
                                    UNIQUE (ManagerID, WorkerID, ProjectID)
                                );''')
        print("WORKERS table created successfully")
        # endregion

        # region Worker Requests TABLE
        self.conn.execute('''CREATE TABLE IF NOT EXISTS WORKER_REQUESTS (
                                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                                    SenderID INTEGER NOT NULL,
                                    ReceiverEmail TEXT NOT NULL,
                                    Status TEXT DEFAULT 'Pending',
                                    FOREIGN KEY (SenderID) REFERENCES CLIENTS(ID)
                                );''')
        print("WORKER_REQUESTS table created successfully")
        # endregion

    # region CLIENTS
    def addClient(self, username, passw, email):
        passw_hash = hashlib.sha256(passw.encode()).hexdigest()
        query = '''
                        SELECT CLIENTS.ID
                        FROM CLIENTS
                        WHERE CLIENTS.Username = ? AND CLIENTS.EMAIL = ?
                    '''
        cursor = self.conn.execute(query, (username, email))
        data = cursor.fetchone()
        if not data:
            query = "INSERT INTO CLIENTS (Username, PASSW, EMAIL) VALUES (?, ?, ?)"
            try:
                self.conn.execute(query, (username, passw_hash, email))
                self.conn.commit()
            except Exception as e:
                print(e)
                return False
            print(f"User {username} registered successfully")
            return True
        else:
            print(f"Username '{username}' or email '{email}' already exists")
            return False

    def loginClient(self, username, passw):
        passw_hash = hashlib.sha256(passw.encode()).hexdigest()
        query = '''
                SELECT CLIENTS.ID, ROLES.NAME
                FROM CLIENTS
                JOIN ROLES ON CLIENTS.ROLE_ID = ROLES.ID_ROLE
                WHERE CLIENTS.Username = ? AND CLIENTS.PASSW = ?
            '''
        cursor = self.conn.execute(query, (username, passw_hash))
        data = cursor.fetchone()
        if data:
            client_id, role = data
            print(f"User {username} logged in successfully with ID {client_id} and Role {role}")
            return True, client_id, role
        print("Login failed: Invalid username or password")
        return False, None, None

    # endregion

    # region FRIENDS
    def addFriend(self, client_id, friend_id):
        if client_id == friend_id:
            print("❌ You cannot add yourself as a friend")
            return False

        try:
            # Check if the friendship already exists
            check_query = """SELECT 1 FROM FRIENDS WHERE (ClientID = ? AND FriendID = ?) OR (ClientID = ? AND FriendID = ?)"""
            cursor = self.conn.execute(check_query, (client_id, friend_id, friend_id, client_id))
            if cursor.fetchone():
                print(f"⚠️ Friendship already exists between {client_id} and {friend_id}")
                return False  # Friendship already exists

            # Insert mutual friendship
            insert_query = "INSERT INTO FRIENDS (ClientID, FriendID) VALUES (?, ?)"
            self.conn.execute(insert_query, (client_id, friend_id))
            self.conn.execute(insert_query, (friend_id, client_id))  # Make it mutual

            # Delete the pending friend request
            delete_query = """DELETE FROM FRIEND_REQUESTS 
                              WHERE SenderID = ? AND ReceiverEmail = (SELECT EMAIL FROM CLIENTS WHERE ID = ?)"""
            self.conn.execute(delete_query, (client_id, friend_id))
            self.conn.commit()

            print(f"✅ Friendship added: {client_id} ↔ {friend_id}")
            return True
        except sqlite3.IntegrityError:
            print(f"⚠️ Friendship insertion failed due to IntegrityError for {client_id} and {friend_id}")
            return False

    def removeFriend(self, client_id, friend_username):
        # Retrieve the friend's ID based on their username
        query = "SELECT ID FROM CLIENTS WHERE Username=?"
        cursor = self.conn.execute(query, (friend_username,))
        data = cursor.fetchone()
        if data:
            friend_id = data[0]
            # Remove the friendship relation
            query = "DELETE FROM FRIENDS WHERE ClientID=? AND FriendID=?"
            self.conn.execute(query, (client_id, friend_id))
            self.conn.commit()
            print(f"Friend '{friend_username}' removed successfully")
        else:
            print(f"User '{friend_username}' does not exist")

    def addFriendRequest(self, sender_id, receiver_email):
        # Trim whitespace and convert to lowercase
        receiver_email = receiver_email.strip().lower()
        print(f"Searching for email: '{receiver_email}' in lowercase.")

        # Debug: Display all emails in the database for comparison
        print("Looking for email in CLIENTS table.")
        query = "SELECT ID, EMAIL FROM CLIENTS"
        cursor = self.conn.execute(query)
        all_emails = cursor.fetchall()
        print("Emails in the database:")
        for row in all_emails:
            print(f"Stored email: '{row[1]}' (ID: {row[0]})")

        # Use LOWER() on both sides for case-insensitive comparison
        query = "SELECT ID FROM CLIENTS WHERE LOWER(EMAIL) = LOWER(?)"
        print(f"Executing query: {query} with email: {receiver_email}")
        cursor = self.conn.execute(query, (receiver_email,))
        data = cursor.fetchone()

        if data:
            receiver_id = data[0]
            print(f"Found user with ID: {receiver_id} for email: '{receiver_email}'")

            # Check if the request already exists
            query = '''SELECT ID FROM FRIEND_REQUESTS 
                       WHERE SenderID=? AND ReceiverEmail=? AND Status='Pending' '''
            cursor = self.conn.execute(query, (sender_id, receiver_email))
            if cursor.fetchone():
                print("Friend request already sent")
                return False

            # Insert the friend request
            query = '''INSERT INTO FRIEND_REQUESTS (SenderID, ReceiverEmail, Status)
                       VALUES (?, ?, 'Pending')'''
            self.conn.execute(query, (sender_id, receiver_email))
            self.conn.commit()
            print("Friend request stored successfully")
            return True
        else:
            print(f"No user found with that email: '{receiver_email}'")
            return False

    def acceptFriendRequest(self, sender_id, receiver_email):
        receiver_email = receiver_email.strip().lower()
        query = "SELECT ID, Username FROM CLIENTS WHERE LOWER(EMAIL) = LOWER(?)"
        cursor = self.conn.execute(query, (receiver_email,))
        data = cursor.fetchone()

        if data:
            receiver_id, receiver_username = data

            # Store both friendships (bidirectional)
            self.addFriend(sender_id, receiver_username)
            self.addFriend(receiver_id, sender_id)

            # Mark request as accepted
            query = '''UPDATE FRIEND_REQUESTS 
                       SET Status='Accepted' 
                       WHERE SenderID=? AND LOWER(ReceiverEmail)=LOWER(?)'''
            self.conn.execute(query, (sender_id, receiver_email))
            self.conn.commit()

            print(f"Friend request accepted! {receiver_username} added to friend list.")
            return receiver_username
        return None

    def listFriends(self, client_id, online_users):
        import os
        try:
            query = '''SELECT c.ID, c.Username, c.Email
                       FROM FRIENDS f
                       JOIN CLIENTS c ON f.FriendID = c.ID
                       WHERE f.ClientID = ?'''
            cursor = self.conn.execute(query, (client_id,))
            friends = cursor.fetchall()

            if not friends:
                return {"friends": []}  # No friends found
                # Check if custom avatar exists for this friend

            friends_list = []
            for friend in friends:
                friend_id, username, email = friend
                avatar_path = f"static/profile_pics/{username}/avatar.png"
                if os.path.exists(avatar_path):
                    profile_pic = f"/static/profile_pics/{username}/avatar.png"
                else:
                    profile_pic = f"/static/profile_pics/{friend_id}.png"
                friends_list.append({
                    "id": friend_id,
                    "username": username,
                    "email": email,
                    "profile_pic": profile_pic,
                    "online": friend_id in online_users
                })

            return {"friends": friends_list}  # Return JSON-compatible dictionary
        except Exception as e:
            print(f"❌ ERROR in listFriends: {e}")
            return {"error": "Internal Server Error"}

    def getUserByEmail(self, email):
        email = email.strip().lower()  # Ensure case-insensitive matching
        query = "SELECT ID, Username FROM CLIENTS WHERE LOWER(EMAIL) = LOWER(?) COLLATE NOCASE"
        cursor = self.conn.execute(query, (email,))
        data = cursor.fetchone()

        if data:
            return data[0], data[1]  # Return (ID, Username)
        return None

    def getUserEmailById(self, id):
        query = "SELECT EMAIL FROM CLIENTS WHERE ID = ?"
        cursor = self.conn.execute(query, (id,))
        data = cursor.fetchone()

        if data:
            print(f"DEBUG: Database returned {data} (Type: {type(data[0])})")  # ADD THIS
            return str(data[0])  # Ensure it's always a string
        return None

    def getPendingFriendRequests(self, receiver_email):
        """
        Returns a list of pending friend requests for the receiver_email.
        Each item in the list is a dictionary with 'sender_id' and 'sender_username'.
        """
        # Ensure email is trimmed and lowercase for consistent matching
        receiver_email = receiver_email.strip().lower()
        query = """SELECT SenderID 
                   FROM FRIEND_REQUESTS 
                   WHERE LOWER(ReceiverEmail) = LOWER(?) AND Status = 'Pending'"""
        cursor = self.conn.execute(query, (receiver_email,))
        results = cursor.fetchall()

        pending_requests = []
        for row in results:
            sender_id = row[0]
            # Get the sender's username from the CLIENTS table
            query2 = "SELECT Username FROM CLIENTS WHERE ID = ?"
            cursor2 = self.conn.execute(query2, (sender_id,))
            sender_data = cursor2.fetchone()
            if sender_data:
                sender_username = sender_data[0]
                pending_requests.append({
                    "type": "friend request",
                    "sender_id": sender_id,
                    "sender_username": sender_username
                })
        print(f"\n\n\n{pending_requests}")
        return pending_requests
    # endregion


    # region WORKERS
    def addWorker(self, owner_id, worker_email):
        worker_email = worker_email.strip().lower()

        # 1. Find worker by email
        query = "SELECT ID FROM CLIENTS WHERE LOWER(EMAIL) = LOWER(?)"
        cursor = self.conn.execute(query, (worker_email,))
        data = cursor.fetchone()

        if not data:
            print(f"❌ No user found with email '{worker_email}'")
            return False

        worker_id = data[0]

        if owner_id == worker_id:
            print("❌ You cannot add yourself as a worker")
            return False

        # 2. Check if already a worker
        query = "SELECT 1 FROM WORKERS WHERE OwnerID = ? AND WorkerID = ?"
        cursor = self.conn.execute(query, (owner_id, worker_id))
        if cursor.fetchone():
            print("⚠️ This person is already your worker")
            return False
        # query = "SELECT 1 FROM CLIENTS WHERE MANAGER_ID = ? AND ID = ?"
        # cursor = self.conn.execute(query, (owner_id, worker_id))
        # if cursor.fetchone():
        #     print("⚠️ This person is already your worker")
        #     return False
        print()
        # 3. Add to WORKERS
        query = "INSERT INTO WORKERS (OwnerID, WorkerID) VALUES (?, ?)"
        self.conn.execute(query, (owner_id, worker_id))
        self.conn.commit()

        print(f"✅ Worker added: {owner_id} ➡ {worker_id}")
        return True

    def removeWorker(self, owner_id, worker_username):
        # Retrieve the worker's ID based on their username
        query = "SELECT ID FROM CLIENTS WHERE Username=?"
        cursor = self.conn.execute(query, (worker_username,))
        data = cursor.fetchone()
        if data:
            worker_id = data[0]
            # Remove the worker relation
            query = "DELETE FROM WORKERS WHERE OwnerID=? AND WorkerID=?"
            self.conn.execute(query, (owner_id, worker_id))
            self.conn.commit()
            print(f"Worker '{worker_username}' removed successfully")
        else:
            print(f"User '{worker_username}' does not exist")

    def addWorkerRequest(self, sender_id, receiver_email):
        # Trim whitespace and convert to lowercase
        receiver_email = receiver_email.strip().lower()
        print(f"Searching for email: '{receiver_email}' in lowercase (Worker Request).")

        # Debug: Display all emails in the database for comparison
        print("Looking for email in CLIENTS table (for Worker Request).")
        query = "SELECT ID, EMAIL FROM CLIENTS"
        cursor = self.conn.execute(query)
        all_emails = cursor.fetchall()
        print("Emails in the database:")
        for row in all_emails:
            print(f"Stored email: '{row[1]}' (ID: {row[0]})")

        # Use LOWER() on both sides for case-insensitive comparison
        query = "SELECT ID FROM CLIENTS WHERE LOWER(EMAIL) = LOWER(?)"
        print(f"Executing query: {query} with email: {receiver_email}")
        cursor = self.conn.execute(query, (receiver_email,))
        data = cursor.fetchone()

        if data:
            receiver_id = data[0]
            print(f"Found user with ID: {receiver_id} for email: '{receiver_email}'")

            # Check if the request already exists
            query = '''SELECT ID FROM WORKER_REQUESTS 
                       WHERE SenderID=? AND ReceiverEmail=? AND Status='Pending' '''
            cursor = self.conn.execute(query, (sender_id, receiver_email))
            if cursor.fetchone():
                print("Worker request already sent")
                return False

            # Insert the worker request
            query = '''INSERT INTO WORKER_REQUESTS (SenderID, ReceiverEmail, Status)
                       VALUES (?, ?, 'Pending')'''
            self.conn.execute(query, (sender_id, receiver_email))
            self.conn.commit()
            print("Worker request stored successfully")
            return True
        else:
            print(f"No user found with that email: '{receiver_email}'")
            return False

    def getPendingWorkerRequests(self, receiver_email):
        """
        Returns a list of pending worker requests for the receiver_email.
        Each item is a dictionary with 'sender_id' and 'sender_username'.
        """
        receiver_email = receiver_email.strip().lower()
        query = """SELECT SenderID 
                   FROM WORKER_REQUESTS 
                   WHERE LOWER(ReceiverEmail) = LOWER(?) AND Status = 'Pending'"""
        cursor = self.conn.execute(query, (receiver_email,))
        results = cursor.fetchall()

        pending_requests = []
        for row in results:
            sender_id = row[0]
            # Get the sender's username from the CLIENTS table
            query2 = "SELECT Username FROM CLIENTS WHERE ID = ?"
            cursor2 = self.conn.execute(query2, (sender_id,))
            sender_data = cursor2.fetchone()
            if sender_data:
                sender_username = sender_data[0]
                pending_requests.append({
                    "type": "work request",
                    "sender_id": sender_id,
                    "sender_username": sender_username
                })
        print(f"\n\n\n{pending_requests}")
        return pending_requests

    def acceptWorkerRequest(self, sender_id, receiver_email):
        receiver_email = receiver_email.strip().lower()
        query = "SELECT ID, Username FROM CLIENTS WHERE LOWER(EMAIL) = LOWER(?)"
        cursor = self.conn.execute(query, (receiver_email,))
        data = cursor.fetchone()

        if data:
            receiver_id, receiver_username = data

            # Store worker relationship
            self.addWorker(sender_id, receiver_username)

            # Mark request as accepted
            query = '''UPDATE WORKER_REQUESTS 
                       SET Status='Accepted' 
                       WHERE SenderID=? AND LOWER(ReceiverEmail)=LOWER(?)'''
            self.conn.execute(query, (sender_id, receiver_email))
            self.conn.commit()

            print(f"Worker request accepted! {receiver_username} added to worker list.")


            return receiver_username
        return None


    def get_workers(self, manager_id):
        query = '''
            SELECT C.ID, C.Username, C.Email, R.NAME,
                (
                    -- Count distinct project IDs owned OR shared with the worker
                    SELECT COUNT(DISTINCT P.ProjectID)
                    FROM (
                        SELECT ProjectID FROM Projects WHERE ClientID = C.ID
                        UNION
                        SELECT ProjectID FROM FRIENDS WHERE ClientID = C.ID
                    ) P
                ) AS project_count
            FROM CLIENTS C
            JOIN ROLES R ON C.ROLE_ID = R.ID
            WHERE C.ROLE_ID = 2 AND C.MANAGER_ID = ?
        '''

        cursor = self.conn.execute(query, (manager_id,))
        workers = []

        for row in cursor.fetchall():
            worker_id, username, email, role, project_count = row
            workers.append({
                "id": worker_id,
                "username": username,
                "email": email,
                "role": role,
                "project_count": project_count
            })

        return workers
    # endregion

    def getPendingRequests(self, email):
        return [{"friends": [self.getPendingFriendRequests(email)],
             "workers": [self.getPendingWorkerRequests(email)]}]

    def closeDb(self):
        self.conn.close()
