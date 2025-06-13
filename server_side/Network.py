import socket
import select

from Security.Asymmetric import Asymmetric
from Security.Encryption import *

# ADDR = ('127.0.0.1', 8085)
ADDR = ('0.0.0.0', 8085)
# ADDR = ('10.168.63.240', 8085)

class Network:
    def __init__(self, dataBase):
        self.dataBase = dataBase
        self.enc = Encryption()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(ADDR)
        self.server_socket.listen(5)
        # self.server_socket.setblocking(False)

        self.clients = {}  # Dictionary to store active clients
        print(f"Server started on {ADDR}")
        self.run_server()

    # region   ====================     KEY EXCHANGE     ====================
    def key_exchange(self,client_socket):
        asym = Asymmetric()
        # Send RSA public key to the client
        client_socket.send(asym.binPubKey)
        # Receive the encrypted AES key from the client
        enc_aes_key = client_socket.recv(1024)
        aes_key = asym.cipher_rsa.decrypt(enc_aes_key)
        print("AES KEY=", aes_key)

        # Create a new Encryption instance for this client
        enc = Encryption()
        enc.setKey(aes_key)
        self.enc.setKey(aes_key)
        return enc
    # endregion
    def run_server(self):
        """Main loop to handle multiple clients using `select`."""
        self.sockets_list = [self.server_socket]

        while True:
            read_sockets, _, exception_sockets = select.select(self.sockets_list, [], self.sockets_list)

            for sock in read_sockets:
                if sock == self.server_socket:
                    client_socket, client_address = self.server_socket.accept()
                    # KEY EXCHANGE
                    enc = self.key_exchange(client_socket)
                    client_socket.setblocking(False)

                    self.sockets_list.append(client_socket)

                    self.clients[client_socket] = {
                        "address": client_address,
                        "key": enc.key,
                        "enc": enc
                    }
                    print(f"New connection from {client_address}")
                else:
                    try:
                        message = self.receive(sock)
                        if message is None:
                            continue

                        # print(f"Received: {message}")
                        if message.startswith("HELLO_"):
                            user_id = message.split("_")[1]
                            print(f"User {user_id} successfully authenticated.")
                        else:
                            self.handle_message(sock, message)

                    except Exception as e:
                        print(f"Error receiving data: {e}")
                        self.disconnect_client(sock, self.sockets_list)

    def handle_message(self, client_socket, message):
        import json
        """Process client requests for multiple types of commands."""
        # try:
        # region Clients
        if message.startswith("SIGNIN"):
            username, password = message.split(' ', 1)[1].split('#')

            success, client_id, role = self.dataBase.login(username, password)
            print(f"Login result: {success}, Client ID: {client_id}")  # Debug

            if success:
                response = f"User exists. ID:{client_id};ROLE:{role}"
                self.send(client_socket, response)

                if client_socket in self.clients:
                    self.clients[client_socket].update({
                        "name": username,
                    })
            else:
                self.send(client_socket, "Username not found")


        elif message.startswith("SIGNUP"):
            try:
                items = message.split(' ')[1].split('#')
                username, email, password = items
                print(f"[DEBUG]: {items}")
            except ValueError:
                self.send(client_socket, "Invalid signup format.")
                return

            success = self.dataBase.tables["clients"].addClient(username, password, email)
            if not success:
                self.send(client_socket, "Username or email already exists.")
                return
            self.send(client_socket, f"User registered successfully!")
            # success, client_id, role = self.dataBase.login(username, password)
            # if success:
            #     self.clients[client_socket] = username
            #     self.send(client_socket, f"User registered successfully! ID:{client_id};ROLE:{role}")
            # else:
            #     self.send(client_socket, "Registration failed.")
        # endregion

        # region Friends
        elif message.startswith("ADD_FRIEND_REQUEST"):
            items = message.split('#', 1)[1].split('.', 1)
            sender_id = int(items[0])
            receiver_id = int(items[1])
            print(f"DEBUG: Processing friend request from {sender_id} to {receiver_id}")
            email_data = self.dataBase.tables["clients"].getUserEmailById(receiver_id)
            success = self.dataBase.tables["clients"].addFriendRequest(sender_id, email_data)

            if success:
                self.send(client_socket, "Success")
            else:
                self.send(client_socket, "Failed to send friend request")

        elif message.startswith("DECLINE_FRIEND_REQUEST#"):
            ids = message.split("#")[1]
            sender_id, receiver_id = map(int, ids.split("."))

            result = self.dataBase.tables["clients"].declineFriendRequest(sender_id, receiver_id)
            if result:
                self.send(client_socket,"Friendship declined")
            else:
                self.send(client_socket, "Failed to decline")

        elif message.startswith("GET_USER_EMAIL"):
            receiver_id = message.split("#",1)[1].strip()
            email_data = self.dataBase.tables["clients"].getUserEmailById(int(receiver_id))
            if email_data:
                self.send(client_socket, f"{email_data}")  # Send back user ID and username
            else:
                self.send(client_socket, "User not found")

        elif message.startswith("GET_USER_BY_EMAIL"):
            receiver_email = message.split("#", 1)[1].strip()
            print(f"SYSTEM: Looking up user by email: {receiver_email}")

            # Query the database for the user’s ID based on email
            user_data = self.dataBase.tables["clients"].getUserByEmail(receiver_email)

            if user_data:
                user_id, username = user_data  # Unpack user ID and username
                self.send(client_socket, f"{user_id}#{username}")  # Send back user ID and username
            else:
                self.send(client_socket, "User not found")

        elif message.startswith("GET_PENDING_REQUESTS"):
            import json
            data = message.split("#", 1)[1].strip()  # Extract payload and remove extra spaces
            try:
                # Try parsing as JSON first
                payload = json.loads(data)
                receiver_email = payload.get("email")  # Use .get() to prevent KeyError
                print(f"DEBUG: receiver_email: {receiver_email}")
            except json.JSONDecodeError:
                # If it's not JSON, assume it's a direct email
                receiver_email = data if "@" in data else None
            if not receiver_email:
                self.send(client_socket, 'error')
                return
            # Fetch pending friend requests from the database
            pending_requests = self.dataBase.tables["clients"].getPendingRequests(receiver_email)
            # print(pending_requests)

            self.send(client_socket, json.dumps(pending_requests))  # Send back as JSON

        elif message.startswith("CONFIRM_FRIENDSHIP"):
            sender_id, receiver_id = message.split("#")[1].split(".", 1)
            try:
                success = self.dataBase.tables["clients"].addFriend(int(sender_id), int(receiver_id))
                if success:
                    print(f"SYSTEM: Friendship added: {sender_id} ↔ {receiver_id}")
                    self.send(client_socket, "Friendship confirmed")
                else:
                    print(f"SYSTEM: Failed to confirm friendship between {sender_id} and {receiver_id}")
                    self.send(client_socket, "Failed to confirm friendship")
            except Exception:
                print("ERROR: sender_id is undefined!")
                self.send(client_socket, "Failed to confirm friendship")

        elif message.startswith("GET_FRIENDS"):
            import json
            # try:
            data = message.split("#", 1)[1] if "#" in message else "{}"
            payload = json.loads(data)  # Avoids parsing errors on empty input
            receiver_id = int(payload.get("client_id", 0))
            active_users = set(map(int, payload.get("active_users", [])))  # Ensure conversion to integers
            if receiver_id == 0:
                raise ValueError("Invalid client_id received")
            friends_data = self.dataBase.tables["clients"].listFriends(receiver_id, active_users)
            print(f"friends_data: {friends_data}")
            self.send(client_socket, json.dumps(friends_data))  # Send back as JSON
        # endregion

        # region Workers
        elif message.startswith("GET_WORKERS"):
            manager_id = int(message.split('#')[1])
            workers = self.dataBase.tables["clients"].get_workers(manager_id)
            # print(workers)
            self.send(client_socket, json.dumps(workers))

        elif message.startswith("SEND_REQUEST_WORKER"):
            import json
            data = message.split("#", 1)[1] if "#" in message else "{}"
            manager_id, worker_email = data.split('.', 1)
            # w_id, w_username = self.dataBase.tables["clients"].getUserByEmail(worker_email)
            self.dataBase.tables["clients"].addWorkerRequest(int(manager_id), worker_email)
        elif message.startswith("ADD_WORKER"):
            import json
            data = message.split("#", 1)[1] if "#" in message else "{}"
            manager_id, worker_email = data.split('.', 1)
            # w_id, w_username = self.dataBase.tables["clients"].getUserByEmail(worker_email)
            self.dataBase.tables["clients"].addWorkerRequest(int(manager_id), worker_email)
        # endregion

        # region Projects
        elif message.startswith("GIVE PROJECTS"):
            import json
            id = message.lower().split('#')[1]

            projects, shared_projects = self.dataBase.tables["projects"].allProjects(int(id))
            print(f"projects#{projects}\n/{shared_projects}")

            self.send(client_socket,
                      f"projects#{json.dumps(projects)}/{json.dumps(shared_projects)}")

        elif message.startswith("ADD_ITEM"):
            data = message.lower().split('#', 1)
            id = int(data[1])
            # print(id)
            projects = self.dataBase.tables["projects"].addProject("New Project", "Describe your project here.", id)
            # self.send(client_socket, f"projects#{projects}")

        elif message.startswith("DUPLICATE_ITEM"):
            # data = message.lower().split('#', 1)
            ids = message.split('#', 1)[1].split('.', 1)
            # print(ids)
            for _ in ids:
                _ = int(_)

            projects = self.dataBase.tables["projects"].duplicateProject(ids[1], ids[0])
            self.send(client_socket, f"projects#{projects}")

        elif message.startswith("SHARE_PROJECT") or message.startswith("ASSIGN_PROJECT"):
            ids = message.split('#', 1)[1].split('.', 2)
            # print(ids)
            for _ in ids:
                _ = int(_)
            self.dataBase.tables["projects"].addSharedProject(ids[0], ids[1], ids[2])
            if "ASSIGN_PROJECT" in message:
                self.send(client_socket,
                          f"assigned successfully")
        # endregion

        elif message.startswith("UPDATE "):
            import ast
            try:
                items = message.split(' ', 1)
                information = items[1].split("$", 1)
                subject = information[0].strip()  # e.g., "projects"
                # print("Subject:", subject)

                ids = information[1].split('#', 1)[0].split('.')
                client_id = int(ids[0])
                project_id = int(ids[1])

                changes = ast.literal_eval(items[1].split('#')[1].strip())  # Correct parsing
                print("Changes: ---\n", changes)

                if subject == "projects":
                    name = changes.get("name", "")
                    desc = changes.get("description", "")

                    print(
                        f"SYSTEM: Updating project with Name: {name}, Description: {desc}, Client ID: {client_id}, Project ID: {project_id}")

                    # if subject not in self.dataBase.tables:
                    #     print("Available tables:", self.dataBase.tables.keys())  # Debugging step
                    #     raise KeyError(subject)

                    self.dataBase.tables[subject].update_project(project_id, name, desc, client_id)

                elif subject == "tasks":
                    task_details = ast.literal_eval(changes)  # Safer dictionary parsing

                    list_items = [
                        int(task_details.get("TaskID", 0)),
                        task_details.get("TaskName", ""),
                        task_details.get("Priority", ""),
                        task_details.get("Status", ""),
                        task_details.get("StatusColor", ""),
                        task_details.get("PriorityColor", ""),
                        task_details.get("Owner(s)", ""),
                        task_details.get("DueDate", ""),
                        task_details.get("Tags", ""),
                        int(task_details.get("Progress", 0)),
                        project_id
                    ]

                    self.dataBase.tables["tasks"].update_item(list_items)

                self.send(client_socket, "Item updated successfully")

            except (IndexError, ValueError, KeyError) as e:
                print(f"Error: {e}")
                self.send(client_socket, f"Failed to update item: {e}")

            except Exception as e:
                print(f"Unexpected error during update: {e}")
                self.send(client_socket, "Failed to update item due to an unexpected error.")

        elif message.startswith("DELETE"):
            data = message.lower().split('#', 1)
            ids = data[1].split('.')
            ids = [int(i) for i in ids]
            # c_id = ids[0]
            # p_id = ids[1]
            subject = data[0].split(' ')[1]
            # self.dataBase.deleteProject(c_id, p_id)
            self.dataBase.delete(subject, ids)
            # print(f"{subject[:-1]}")
            self.send(client_socket, f"The {subject[:-1]} has deleted successfully")

        elif message.startswith("GIVE"):
            items = message.lower().split(' ', 1)[1].split('#')
            ids = items[0].split('.')
            c_id = int(ids[0])
            p_id = int(ids[1])
            name = items[1]
            list_ = self.dataBase.read_list_by_ID(c_id, p_id, name)
            self.send(client_socket, f"{list_}")

        #region Sprints

        elif message.startswith("UPDATE_SPRINT"):
            import json
            items = message.split('#', 1)
            print(items)

            data = items[1].split("$", 1)

            sprint_details = json.loads(data[1])
            print(sprint_details)
            ID = int(sprint_details.get("SprintID", 0))  # Convert to integer
            SprintName = sprint_details.get("SprintName", "")
            SprintColor = sprint_details.get("SprintColor", "")

            list_items = [
                ID, SprintName, SprintColor
            ]

            self.dataBase.tables["tasks"].update_sprint(list_items)

        elif message.startswith("ADD_SPRINT"):
            import json
            #    "ADD_SPRINT#{client_id}.{projectId}${new_sprint}"
            items = message.split('#', 1)
            print(items)

            data = items[1].split("$", 1)

            ids = data[0].split('.')
            print(ids)
            c_id = int(ids[0])
            p_id = int(ids[1])
            # item = data[1].strip("{}").strip()
            # sprint_id = int(ids[0])

            task_details = json.loads(data[1])
            # print(task_details)
            ID = int(task_details.get("SprintID", 0))  # Convert to integer
            SprintName = task_details.get("SprintName", "")
            SprintColor = task_details.get("SprintColor", "")

            list_items = [
                ID, SprintName, SprintColor
            ]
            print(list_items)
            self.dataBase.tables["tasks"].add_sprint_with_task(list_items, p_id, c_id)

        elif message.startswith("DEL_SPRINT"):
            p_id, s_id = message.split('#', 1)[1].split('.')
            print("DELETE SPRINT")
            self.dataBase.tables["tasks"].delete_sprint(int(s_id), int(p_id))

        #endregion

        # region Tasks
        elif message.startswith("UPDATE_TASK"):
            import json

            data = message.split("$", 1)

            # Fix JSON formatting issues
            item = data[1].strip()  # Remove leading/trailing spaces
            item = item.replace("'", '"')  # Convert single to double quotes for JSON
            item = item.replace(": None", ": null")  # Replace Python None with JSON null

            print("Fixed JSON string:", item)  # Debugging

            try:
                # Convert fixed string to dictionary
                task_details = json.loads(item)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
                task_details = {}  # Fallback to an empty dictionary

            print("Parsed task_details:", task_details)

            # Extract values from task_details dictionary
            ID = int(task_details.get("TaskID", 0))  # Convert to integer
            TaskName = task_details.get("TaskName", "")
            Status = task_details.get("Status", "")
            status_color = task_details.get("StatusColor", "")
            Priority = task_details.get("Priority", "")
            priority_color = task_details.get("PriorityColor", "")
            Owners = task_details.get("Owners", "")  # Fixed: No need for ('Owner(s)')
            DueDate = task_details.get("DueDate")
            Tags = task_details.get("Tags", "")
            Progress = int(task_details.get("Progress", 0))  # Convert to integer

            if DueDate == "null":  # Convert string null to Python None
                DueDate = None

            # Create a list of items to update the database
            list_items = [
                ID, TaskName, Priority, Status, status_color,
                priority_color, Owners, DueDate, Tags, Progress
            ]
            # print("Final list_items:", list_items)

            # Update the database
            self.dataBase.tables["tasks"].update_item(list_items)
            print("Task updated successfully:", list_items)

            # Send confirmation back through the socket
            self.send(client_socket, f"Task no.{ID} has been updated")


        elif message.startswith("DEL_TASK"):
            item = message.split(' ', 1)[1]
            print(item)
            self.dataBase.del_list_item(item)
            self.send(client_socket, f"{item} has deleted")

        # elif message.startswith("SWAP"):
        #     import json
        #     tasksID = message.split('#', 1)[1].split('*')
        #     targetID, draggable = tasksID[0], tasksID[1]
        #     # Call the function to swap task positions
        #     message = self.dataBase.updataDrag(targetID, draggable)
        #     # Serialize the message to JSON and encode it
        #     serialized_message = json.dumps(message).encode('utf-8')
        #     # Send the serialized message
        #     self.send(client_socket, serialized_message)

        elif message.startswith("ADD_TASK"):
            items = message.split('#', 1)[1].split('.')
            # print(items)

            t_id, taskName = items[3].split('$', 1)
            c_id = int(items[0])
            p_id = int(items[1])
            s_id = int(items[2])
            t_id = int(t_id)
            self.dataBase.addTask(c_id, p_id, s_id, t_id, taskName)

            self.send(client_socket, "New empty task has created")

        # endregion

        elif message.startswith("END"):
            print("ENDDDDE")
            self.disconnect_client(client_socket, self.sockets_list)
        else:
            self.send(client_socket, "Unknown command")

    def send(self, client, message):
        try:
            if client:
                # Encrypt the message
                # self.enc.key = key
                enc = self.clients[client]["enc"]
                encrypted_message = enc.encrypt_message(message)
                total_length = len(encrypted_message)
                total_length_bytes = total_length.to_bytes(4, byteorder='big')
                client.send(total_length_bytes+encrypted_message)
            else:
                print("Socket not connected. Attempting to reconnect...")
        except Exception as e:
            print(f"Error sending message: {e}")

    def receive(self, sock):
        try:
            raw_length = sock.recv(4)  # Read first 4 bytes (message length)
            if not raw_length:
                self.disconnect_client(sock, self.sockets_list)
                return None

            message_length = int.from_bytes(raw_length, byteorder='big')
            buffer = sock.recv(message_length)  # Read full message
            if not buffer:
                self.disconnect_client(sock, self.sockets_list)
                return None
            # Check if the message is encrypted (must be at least 16 bytes)
            enc = self.clients[sock]["enc"]
            if len(buffer) >= 16:
                try:
                    message = enc.decrypt_message(buffer)
                except ValueError as e:
                    print(f"Decryption error: {e}")
                    return None  # Ignore if decryption fails
            else:
                message = buffer.decode('utf-8')  # Handle plaintext messages

            return message
        except Exception as e:
            print(f"Receive error: {e}")
            self.disconnect_client(sock, self.sockets_list)
            return None

    def disconnect_client(self, client_socket, sockets_list):
        """Disconnect a client."""
        try:
            client_info = self.clients.get(client_socket)
            name = client_info.get("name") if client_info else None
            print(f"Client {name or client_socket} disconnected.")
        except Exception as e:
            print(f"[ERROR] Failed to log disconnect message: {e}")
            self.shut()
        finally:
            try:
                if client_socket in sockets_list:
                    sockets_list.remove(client_socket)
            except Exception as e:
                print(f"[WARN] Could not remove socket from list: {e}")

            try:
                if client_socket in self.clients:
                    del self.clients[client_socket]
            except Exception as e:
                print(f"[WARN] Could not delete client from clients: {e}")

            try:
                client_socket.close()
            except Exception as e:
                print(f"[WARN] Could not close client socket: {e}")

    def shut(self):
        self.server_socket.close()
        # except Exception as e:
        #     sockets_list.remove(client_socket)
        #     del self.clients[client_socket]
        #     client_socket.close()
#


# if __name__ == '__main__':
#     Network(DatabaseParent())
