import time

class Client:
    def __init__(self, username, session_id, client_id):
        self.username = username
        self.session_id = session_id
        self.client_id = client_id
        self.time_since_login = time.time()
        self.friends = None
        self.notifications = None


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