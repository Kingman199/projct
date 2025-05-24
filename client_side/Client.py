import time

class Client:
    def __init__(self, username, session_id, client_id):
        self.username = username
        self.session_id = session_id
        self.client_id = client_id
        self.time_since_login = time.time()
        self.friends = None
        self.notifications = None


    def update_login_time(self):
        """Update the login time to keep track of idle time."""
        self.time_since_login = time.time()

    def get_session_data(self):
        """Return essential session data."""
        return {
            'username': self.username,
            'session_id': self.session_id,
            'client_id': self.client_id,
            'time_since_login': self.time_since_login
        }

class Manager(Client):
    def __init__(self, username, session_id, client_id):
        super().__init__(username, session_id, client_id)
        self.role = "Manager"
        self.managed_workers = []


class Worker(Client):
    def __init__(self, username, session_id, client_id):
        super().__init__(username, session_id, client_id)
        self.role = "Worker"


class Guest(Client):
    def __init__(self, username, session_id, client_id):
        super().__init__(username, session_id, client_id)
        self.role = "Guest"