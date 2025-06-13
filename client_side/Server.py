import threading, mimetypes, uuid, json, base64, re
from Client import *
from flask import Flask, jsonify, request, render_template, session, redirect, url_for, send_file, has_request_context
from ConnectionWithDatabase import ConnectionWithDatabase
from flask_session import Session
from datetime import datetime
from typing import Optional

# region Handle Friend Requests in Real-Time
from flask_socketio import SocketIO, emit, join_room, leave_room
from functools import wraps

app = Flask(__name__, static_folder="static")
mimetypes.add_type('text/javascript', '.js')


# Force Flask to recognize JS as module-compatible

clients = {}  # Store multiple user connections
clients_list = []  # Store multiple user connections
# session_id: ConnectionWithDatabase, [Client()]
client = None

# region Session
app.config["SECRET_KEY"] = "supersecretkey"  # Must be set when SESSION_USE_SIGNER is True
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = "./flask_session_data"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True
Session(app)
# endregion

@app.route('/static/js/Tasks/DueDate_Task.js')
def serve_due_date_task():
    return send_file('static/js/Tasks/DueDate_Task.js', mimetype='text/javascript')

def role_required(*allowed_roles):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            session_id = session.get("session_id")
            client = clients.get(session_id)["client"]
            if not client or getattr(client, 'role', None) not in allowed_roles:
                return redirect(url_for('404'))  # Or some error page
            return f(*args, **kwargs)
        return decorated_function
    return wrapper

@app.before_request
def session_check():
    session.modified = True  # Keeps the session active for permanent sessions

    allowed_routes = ['login', 'static']
    if request.endpoint in allowed_routes:
        return

    if "time_since_login" in session:
        current_time = time.time()
        if current_time - session["time_since_login"] > 300:  # 5 minutes
            session.clear()
            return redirect(url_for('login'))
        else:
            session["time_since_login"] = current_time  # reset on activity

# endregion

# Initialize Flask-SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")  # Keep Flask as primary

# endregion

def run_socketio():
    socketio.run(app, host='0.0.0.0', port=5001, debug=False, use_reloader=False, allow_unsafe_werkzeug=True)



@app.route('/')
def home():
    return render_template('home.html')

import os
@app.route('/login', methods=['GET', 'POST'])
def login():
    global clients, client

    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['password']

            temp_session_id = str(uuid.uuid4())
            connection = ConnectionWithDatabase(temp_session_id)

            if not connection.connected:
                return render_template('login.html', error="Database connection failed.")

            connection.send(f"SIGNIN {username}#{password}")
            response = connection.receive()
            if "ENDED" in response:
                return render_template("404.html", error="Hold on, buddy. Something is off...\nPlease 'wait' for the updates"), 404
            print("Login response:", response)

            if response and "User exists" in response:
                # Disconnect existing session
                if username in clients_list:
                    print(f"User {username} already logged in. Disconnecting old session.")
                    old_session_id = next((sid for sid, data in clients.items()
                                           if data.get("client") and data["client"].username == username), None)
                    if old_session_id:
                        clients[old_session_id]["connection"].close()
                        clients.pop(old_session_id, None)
                        clients_list.remove(username)

                # Parse ID and role
                parts = response.split(';')
                client_id = parts[0].split('ID:')[1].strip()
                role = parts[1].split('ROLE:')[1].strip()

                connection.send(f"GET_USER_EMAIL#{client_id}")
                email = connection.receive().strip()
                avatar_path = f'static/profile_pics/{username}/avatar.png'

                # Determine which picture path to use
                if os.path.exists(avatar_path):
                    # Use the user's custom avatar
                    pic_path = f"/static/profile_pics/{username}/avatar.png"
                else:
                    # Fallback to a default or client-specific image
                    pic_path = f"/static/profile_pics/{client_id}.png"

                # Set session
                session.update({
                    "username": username,
                    "password": password,
                    "session_id": temp_session_id,
                    "client_id": client_id,
                    "role": role,
                    "pic": pic_path,
                    "email": email
                })

                # Insert temporary client entry
                clients[temp_session_id] = {
                    "connection": connection,
                    "client": None
                }

                # Initialize client with role
                new_client = Role(role)
                clients[temp_session_id]["client"] = new_client
                session["time_since_login"] = new_client.time_since_login
                clients_list.append(username)


                return redirect(url_for('projects_view', session_id=temp_session_id))
            else:
                connection.close()
                return render_template('login.html', error="Invalid username or password.")

        except Exception as e:
            import traceback
            print("🔥 Exception in /login:", e)
            traceback.print_exc()
            return render_template('login.html', error="Internal Server Error. Please try again.")

    return render_template('login.html')

def Role(role):
    # Create the appropriate Client object
    if role == "Manager":
        session["workers"] = fetch_workers_for_manager(session["client_id"])
        client_ = Manager(session["username"], session["session_id"], session["client_id"])
        client_.managed_workers = session["workers"]
        return client_
    elif role == "Worker":
        return Worker(session["username"], session["session_id"], session["client_id"])
    elif role == "Guest":
        return Guest(session["username"], session["session_id"], session["client_id"])
    else:
        return Client(session["username"], session["session_id"], session["client_id"])


@app.route('/projects')
def projects_view():
    try:
        if "session_id" not in session or "client_id" not in session:
            return redirect(url_for("login"))  # Redirect to login if session is missing


        # Pull session_id from URL first
        session_id = request.args.get("session_id") or session.get("session_id")

        client_id = clients[session_id]["client"].client_id
        connection = clients[session_id]["connection"]
        connection.send(f"GIVE PROJECTS#{client_id}")
        proj = connection.receive()
    except Exception:
        return render_template("404.html",
                               error="Hold on, buddy. Something is off...\nPlease 'wait' for the updates"), 404
    if "ENDED" in proj:
        return render_template("404.html", error="Hold on, buddy. Something is off...\nPlease 'wait' for the updates"), 404
    print("Raw received data:", proj)
    try:
        # if "Unknown command" in raw_proj:
        #     return "Error: Server did not recognize the request.", 500
        projects, share_project = proj.split('#', 1)[1].split('/', 1)
        # Ensure JSON format
        projects = json.loads(projects)  # Parse JSON properly
        share_projects = json.loads(share_project)  # Parse JSON properly
    except (json.JSONDecodeError, IndexError) as e:
        print(f"JSON decoding error: {e}")
        return f"Error decoding project data: {e}", 500
    print(f"Shared Projects:  {share_projects}")
    session["projects"] = projects
    session["shared_projects"] = share_projects
    session["notifications"] = get_notifications()


    friend_list  = friends()
    print("FRIENDS", friend_list)
    return render_template(
        "projects.html",
        projects=session["projects"],
        shared_projects=session["shared_projects"],
        notifications=session["notifications"],
        session_id=session_id
    )


@app.route('/edit_project/<int:project_id>', methods=['POST'])
def edit_project(project_id):
    # Pull session_id from URL first
    session_id = request.args.get("session_id") or session.get("session_id")

    updated_data = request.json
    print(f"Log: {updated_data}")
    client_id = clients[session_id]['client'].client_id
    connection = clients[session_id]["connection"]
    connection.send(f"UPDATE projects${client_id}.{project_id}#{updated_data}")
    message = clients[session_id]["connection"].receive()
    print(message)
    project = None
    for i in range(len(session["projects"])):
        if session["projects"][i]["id"] == project_id:
            session["projects"][i]["name"] = updated_data["name"]
            session["projects"][i]["description"] = updated_data["description"]
            project = session["projects"][i]

    print(session["projects"])
    return jsonify({'message': 'Project updated', 'project': project}), 200


@app.route('/add_project', methods=['POST'])
def add_project():
    # Pull session_id from URL first
    session_id = request.args.get("session_id") or session.get("session_id")

    data = request.get_json()
    project_type = data.get("type", "new")
    # session_id = session["session_id"]
    # client_id = session["client_id"]
    client_id = clients[session_id]["client"].client_id

    connection = clients[session_id]["connection"]
    # Tell the server to add a project
    if project_type == "new":
        connection.send(f"ADD_ITEM projects#{client_id}")
        message = connection.receive()
        if "ENDED" in message:
            return render_template("404.html", error="Hold on, buddy. Something is off...\nPlease 'wait' for the updates"), 404
        print(message)

        new_project = {
            'id': data['id'],
            'name': data['name'],
            'description': data['description']
        }
        session["projects"].append(new_project)
        return jsonify(new_project)


    elif project_type == "duplicate":
        print("Duplicating project...")
        original_project_id = data.get("original_project_id")
        print(f"Original project ID: {original_project_id}")
        original_project = next((p for p in session["projects"] if p["id"] == original_project_id), None)

        if not original_project:
            print("Error: Original project not found")
            return jsonify({"error": "Original project not found"}), 404

        connection.send(f"DUPLICATE_ITEM projects#{client_id}.{original_project_id}")
        response = connection.receive()
        if "ENDED" in response:
            return render_template("404.html", error="Hold on, buddy. Something is off...\nPlease 'wait' for the updates"), 404
        print(f"Server response: {response}")
        duplicated_project = {

            'id': data['id'],
            'name': original_project['name'] + " (Copy)",
            'description': original_project['description']
        }
        print(f"Duplicated project: {duplicated_project}")
        session["projects"].append(duplicated_project)

        return jsonify(duplicated_project)


@app.route('/delete_project', methods=['POST'])
def delete_project():
    data = request.json
    project_id = data.get('project_id')
    session_id = data.get("session_id") or session.get("session_id")

    if not session_id or session_id not in clients:
        return jsonify({'error': 'Invalid session'}), 400

    client_id = clients[session_id]["client"].client_id
    clients[session_id]["connection"].send(f"DELETE projects#{client_id}.{project_id}")
    print(clients[session_id]["connection"].receive())

    # Update session
    session["projects"] = [p for p in session.get("projects", []) if str(p['id']) != str(project_id)]

    return jsonify({'message': 'Project deleted'}), 200



@app.route("/project/<string:project_name>")
def project_dashboard(project_name):
    # Pull session_id from URL first
    session_id = request.args.get("session_id") or session.get("session_id")
    if not session_id:
        return render_template("404.html", error="You made a mistake, buddy"), 404
    project_name = project_name.strip()  # Normalize input

    # Combine owned and shared projects
    all_projects = session.get("projects", []) + session.get("shared_projects", [])
    print("All projects (normalized):", [p["name"].strip().lower() for p in all_projects])

    # Find project (case-insensitive and trimmed match)
    project = next(
        (p for p in all_projects if p["name"].strip().lower() == project_name.lower()),
        None
    )

    if project:
        print("Project found:", project)  # Debugging

        project_id = project["id"]
        session["project_id"] = project_id

        try:
            # Get all sprints for the project
            sprints_data = get_sprints(project_id)
            session["sprints"] = sprints_data

            # Ensure sprints is a list (Jinja requires an iterable)
            if isinstance(sprints_data, dict):
                sprints_data = [sprints_data]

            print(session["sprints"])
        except Exception as e:
            print(f"Error fetching tasks for project {project_id}: {e}")
            return render_template('404.html', error="Error")


        return render_template(
            "HomeTasks_.html",
            project_name= project_name,
            project_id= project_id,
            sprints= sprints_data[::-1],
            projects=session["projects"],
            shared_projects=session["shared_projects"],
            session_id = session_id
        )

    else:
        print(f"Project '{project_name}' not found in projects list.")
        return render_template("404.html", project_name=project_name), 404



# region --------------- SPRINTS ---------------

import json
import ast

def clean_nonbreaking_spaces(obj):
    if isinstance(obj, dict):
        return {k: clean_nonbreaking_spaces(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nonbreaking_spaces(i) for i in obj]
    elif isinstance(obj, str):
        return obj.replace('\xa0', ' ').strip()
    return obj

def get_sprints(project_id):
    clients[session["session_id"]]["connection"].send(
        f"GIVE {session['client_id']}.{project_id}#sprints"
    )
    response = clients[session["session_id"]]["connection"].receive()

    print(f"Raw task data received: {response}")

    # Remove byte-string wrapper if present
    if response.startswith("b'") or response.startswith('b"'):
        response = response[2:-1]

    # Fallback: Try to interpret Python literal
    try:
        data = ast.literal_eval(response)
    except Exception as e:
        print(f"Failed to parse Python literal: {e}")
        return "Error parsing tasks", 500

    # Convert to JSON-safe string
    try:
        cleaned_data = clean_nonbreaking_spaces(data)
        return cleaned_data
    except Exception as e:
        print(f"Error during cleanup: {e}")
        return "Error processing tasks", 500



# Update Sprint Color Route
import copy


@app.route('/update_sprint', methods=['POST'])
def update_sprint():
    try:
        data = request.get_json()
        sprint_id = data.get("SprintID")
        project_id = data.get("project_id")
        sprint_name = data.get("SprintName")
        sprint_color = data.get("SprintColor")

        if sprint_id is None:
            return jsonify({"success": False, "error": "SprintID is required"}), 400

        sprints = session.get("sprints", [])
        sprint = next((t for t in sprints if int(t.get("SprintID", -1)) == int(sprint_id)), None)
        if sprint is None:
            return jsonify({"success": False, "error": "Sprint not found"}), 404

        tasks = copy.deepcopy(sprint.get("Tasks", []))
        sprint["Tasks"] = None
        updated_fields = {}

        if sprint_color is not None:
            sprint["SprintColor"] = sprint_color
            updated_fields["SprintColor"] = sprint_color

        if sprint_name and sprint_name != sprint["SprintName"]:
            if len(sprint_name) > 2:
                sprint["SprintName"] = sprint_name.replace(u'\xa0', ' ').strip()
                updated_fields["SprintName"] = sprint_name
            else:
                return jsonify({"success": False, "error": "Sprint name too short"}), 400

        if updated_fields:
            # If you still want to send custom connection updates (optional)
            if "session_id" in session and session["session_id"] in clients:
                clients[session["session_id"]]["connection"].send(
                    f"UPDATE_SPRINT#{sprint_id}${json.dumps(sprint)}"
                )

            room_name = f"project_{project_id}"
            socketio.emit("sprint_updated", {
                "sprint_id": sprint_id,
                "updated_by": session.get("username"),
                "updated_fields": updated_fields,
                "project_id": project_id
            }, room=room_name)

        sprint["Tasks"] = tasks
        session["tasks"] = tasks

        return jsonify({"status": "success"})

    except Exception as e:
        print("Exception:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500

# TODO: Add the sockeio.emit for adding sprint
@app.route('/add_sprint', methods=['POST'])
def add_sprint():
    try:
        data = request.get_json()
        existing_colors = {sprint["SprintColor"] for sprint in session["sprints"]}


        # Generate a unique random color
        import random
        def generate_unique_color():
            while True:
                color = "#{:06x}".format(random.randint(0, 0xFFFFFF))
                if color not in existing_colors:
                    return color

        sprint_color = generate_unique_color()

        sprint_id = str(len(session["sprints"]) + 1)  # Simple auto-increment for demo
        new_sprint = {
            "SprintID": sprint_id,
            "SprintName": data.get("SprintName", f"Sprint {sprint_id}"),
            "SprintColor": sprint_color,
            "Tasks": []
        }
        projectId = data.get("ProjectID")
        print(new_sprint)
        # connection.send(f"ADD_SPRINT#{session["project_id"]}.{task_id}${taskName}")
        clients[session["session_id"]]["connection"].send(f"ADD_SPRINT#{session['client_id']}.{projectId}${json.dumps(new_sprint)}")

        username = session.get("username", "unknown")
        socketio.emit("sprint_added",
                      {"project_id": projectId,
                       "sprint": new_sprint,
                       "added_by": username},
                      room=f"project_{projectId}",
                      namespace="/")


        session["sprints"].append(new_sprint)
        return jsonify({"success": True, "sprint": new_sprint})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/delete_sprint/<sprint_id>', methods=['DELETE'])
def delete_sprint(sprint_id):
    print(f"Received request to delete sprint {sprint_id}")
    try:
        original_sprints = session.get("sprints", [])
        print("Original sprints:", original_sprints)

        new_sprints = [s for s in original_sprints if str(s["SprintID"]) != str(sprint_id)]

        if len(original_sprints) == len(new_sprints):
            print("Sprint not found")
            return jsonify({"success": False, "message": "Sprint not found."}), 404

        session["sprints"] = new_sprints
        print("Sprint deleted")

        project_id = session.get("project_id")
        session_id = session.get("session_id")
        username   = session.get("username") or "unknown"
        connection = clients[session_id]["connection"]

        if session_id in clients:
            connection.send(f"DEL_SPRINT#{project_id}.{sprint_id}")

        # ✅ Socket.IO broadcast to all clients in the project room
        socketio.emit("sprint_deleted",
                      {"project_id": project_id,
                       "sprint_id": sprint_id,
                       "deleted_by": username},
                      room=f"project_{project_id}",
                      namespace="/")

        return jsonify({"success": True, "deletedSprintId": sprint_id}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500



# endregion

#region Share With Friends

@app.route('/share_project', methods=['POST'])
def share_project():
    # Pull session_id from URL first
    session_id = request.args.get("session_id") or session.get("session_id")

    # Parse the JSON request body.
    data = request.get_json()
    if not data:
        return jsonify(success=False, error="Invalid JSON data."), 400

    project_id = data.get('project_id')
    friend_id = data.get('friend_id')
    client =  clients[session_id]["client"]
    # Validate required parameters.
    if not project_id or not friend_id:
        return jsonify(success=False, error="Missing project_id or friend_id."), 400

    # Retrieve the current user's friends list from the session.
    friends = session.get('friends') or client.friends or []
    # Check if the friend_id exists in the session's friends list.
    friend_found = any(str(friend['id']) == str(friend_id) for friend in friends)
    if not friend_found:
        return jsonify(success=False, error="Friend not found in your session."), 404

    client_id = clients[session_id]["client"].client_id
    clients[session_id]["connection"].send(f"SHARE_PROJECT#{client_id}.{friend_id}.{project_id}")


    print(f"Project {project_id} has been shared with friend {friend_id}.")

    return jsonify(success=True), 200

#endregion

        # region ------------- HOME  TASKS -------------

import json

@app.route("/delete_task", methods=["POST"])
def delete_task():
    global client_id
    data = request.get_json()
    task_id = data.get('task_id')
    project_id = data.get('project_id')  # Get project_id from the frontend
    session['project_id'] = project_id
    session['task_id'] = task_id
    sprint_id = 0
    username = session["username"]
    print(task_id)
    sprint_name = ""
    # Locate the task
    for sprint in session.get("sprints", []):
        for task in sprint.get("Tasks"):
            if task["TaskID"] == int(task_id):
                sprint_name = sprint["SprintName"]
                sprint_id = sprint["SprintID"]
                sprint["Tasks"].remove(task)
                break

    clients[session["session_id"]]["connection"].send(f"DELETE tasks#{session['project_id']}.{session['task_id']}")
    response = clients[session["session_id"]]["connection"].receive()

    if "successfully" in response:
        # Emit deletion to all clients
        socketio.emit("delete_task", {
            "task_id": task_id,
            "deleted_by": username,
            "sprint_name": sprint_name,
            "sprint_id" : sprint_id
        }, room=f"project_{project_id}")
        return jsonify({'status': 'success', 'message': 'Task deleted successfully'}), 200
    else:
        return jsonify({'status': 'error', 'message': 'Task not found'}), 404

# TODO: Make sure the sockeio.emit works for adding task
@app.route("/add_task", methods=["POST"])
def add_task():
    new_task = request.json
    sprint_id = new_task.get("SprintID")
    task_name = new_task.get("TaskName", "Untitled Task")
    username = session["username"]
    connection = clients[session["session_id"]]["connection"]

    sprints_data = session.get("sprints", [])
    if isinstance(sprints_data, str):
        try:
            sprints_data = json.loads(sprints_data)
        except json.JSONDecodeError:
            sprints_data = []
    # Find the sprint matching the SprintID
    matching_sprint = next(
        (s for s in session.get("sprints", []) if str(s["SprintID"]) == str(sprint_id)),
        None
    )
    if matching_sprint:
        session["tasks"] = matching_sprint.get("Tasks", [])
    else:
        session["tasks"] = []  # fallback

    sprint_name = ""
    if session["tasks"]:
        for sprint in session.get("sprints", []):
            print(f"Checking Sprint: {sprint}")
            if sprint.get("SprintID") == sprint_id:
                sprint_name = sprint["SprintName"]
                session["tasks"] = sprint.get("Tasks", [])
                print("Sprint tasks found:", session["tasks"])
                break

    task_id = 1 if not session["tasks"] else max(task.get("TaskID", 0) for task in session["tasks"]) + 1
    new_task["TaskID"] = task_id

    # Ensure default values
    new_task["StatusColor"] = STATUS_COLORS.get(new_task.get("Status", "In Progress"), "#d0ebff")
    new_task["PriorityColor"] = PRIORITY_COLORS.get(new_task.get("Priority", "Medium"), "#9ca3af")
    new_task["Progress"] = 0  # Default progress
    new_task["Owners"] = None
    new_task["Tags"] = "None"
    # Append the new task to session["tasks"]
    session["tasks"].append(new_task)
    for sprint in session.get("sprints", []):
        print(f"Checking Sprint: {sprint}")
        if sprint.get("SprintID") == sprint_id:
            sprint["Tasks"] = session["tasks"]
            print("Sprint tasks found:", session["tasks"])
            break
    try:
        client_id = session.get("client_id")
        project_id = session.get("project_id")

        if not client_id or not project_id:
            raise ValueError("Missing client_id or project_id in session.")

        connection.send(f"ADD_TASK#{client_id}.{project_id}.{sprint_id}.{task_id}${task_name}")
        response = connection.receive()
        print(f"Received response: {response}")

    except Exception as e:
        print(f"Connection error: {e}")
        return jsonify({"status": "error", "message": "Failed to add task"}), 500

    socketio.emit("task_added", {
        "new_task": new_task,
        "added_by": username,
        "sprint_id": sprint_id,
        "sprint_name": sprint_name,
        "project_id" : project_id
    }, room=f"project_{project_id}")
    # print(new_task)
    new_task["project_id"] = project_id
    return jsonify({"status": "success", "newTask": new_task})

@app.route("/update_task", methods=["POST"])
def update_task():
    try:
        session_id = session["session_id"]
        connection = clients[session_id]["connection"]
        if not connection.connected:
            return render_template("404.html",
                                   error="Hold on, buddy. Something is off...\nPlease 'wait' for the updates"), 404

        update_data = request.json
        task_id = update_data.get("ID")
        status = update_data.get("Status")
        priority = update_data.get("Priority")
        sprint_id = update_data.get("SprintID")
        task_name = update_data.get("TaskName", "").strip()

        project_id = update_data.get("project_id") or session.get("project_id")
        username = session.get("username")
        if not task_id or not sprint_id or not project_id:
            return jsonify({"status": "error", "message": "Task ID, Sprint ID, and Project ID are required"}), 400

        print("Update data received:", update_data)
        print("Session sprints:", session.get("sprints", []))

        sprint_name = ""
        task = None
        # region Locate the task
        for sprint in session.get("sprints", []):
            if int(sprint.get("SprintID")) == int(sprint_id):
                sprint_name = sprint["SprintName"]
                for t in sprint.get("Tasks", []):
                    if int(t.get("TaskID")) == int(task_id):
                        task = t
                        break

        if not task:
            return jsonify({"status": "error", "message": "Task not found"}), 404
        # endregion

        # region Updating
        # Track changes for logging
        change_log = []

        # Validate and update task name
        if task_name:
            if task["TaskName"] != task_name:
                change_log.append(f"Task name changed from '{task['TaskName']}' to '{task_name}'")
                task["TaskName"] = task_name

        # Validate and update status
        if status and task["Status"] != status:
            change_log.append(f"Status changed from '{task['Status']}' to '{status}'")
            task["Status"] = status
            if "StatusColor" in update_data:  # Ensure frontend provides correct status color
                task["StatusColor"] = update_data["StatusColor"]
        # Validate and update priority
        if priority and task["Priority"] != priority:
            change_log.append(f"Priority changed from '{task['Priority']}' to '{priority}'")
            task["Priority"] = priority
            if "PriorityColor" in update_data:  # Ensure frontend provides correct priority color
                task["PriorityColor"] = update_data["PriorityColor"]

        due_date = update_data.get("DueDate")
        # Validate and update due date
        if due_date and task.get("DueDate") != due_date:
            change_log.append(f"Due date changed from '{task.get('DueDate', 'None')}' to '{due_date}'")
            task["DueDate"] = due_date

        print(type(due_date))
        if due_date:
            task = updatePlus(task, update_data)
        # endregion

        socketio.emit("task_updated", {
            "project_id": project_id,
            "sprint_id": sprint_id,
            "updated_task": task,
            "changes": change_log,
            "updated_by": username,
            "sprint_name": sprint_name
        }, room=f"project_{project_id}")

        print(f"Updated Task: {task}")

        # Update the session with the modified task
        for sprint in session.get("sprints", []):
            if int(sprint["SprintID"]) == int(sprint_id):
                for i, task_ in enumerate(sprint["Tasks"]):
                    if int(task_["TaskID"]) == int(task["TaskID"]):
                        sprint["Tasks"][i] = task  # Directly update task
                        session.modified = True
                        break

        print("Change log:", change_log)

        # Print updated sprint tasks
        for sprint in session.get("sprints", []):
            print(f"Tasks in Sprint {sprint['SprintID']}: {sprint.get('Tasks', [])}")

        # TODO: if the date is close to the DueDate, the system would add a notification to the user about it.

        # Notify the client through WebSocket
        if session.get("session_id") in clients:
            try:
                clients[session["session_id"]]["connection"].send(f"UPDATE_TASK${task}")
                response = clients[session["session_id"]]["connection"].receive()  # No timeout parameter
                print("WebSocket response:", response)
            except Exception as e:
                print(f"WebSocket error: {e}")

        return jsonify({"status": "success", "updated_task": task, "changes": change_log})
    except Exception:
            return render_template("404.html", error="You made a mistake, buddy"), 404

def updatePlus(task, update_data):
    today = datetime.today()
    new_due_date_str = update_data.get("DueDate")
    current_due_date_obj = parse_due_date(task.get("DueDate"))
    new_due_date_obj = parse_due_date(new_due_date_str) if new_due_date_str else None

    # Only update if DueDate is different
    if new_due_date_obj and current_due_date_obj != new_due_date_obj:
        task["DueDate"] = new_due_date_obj.strftime("%d/%m/%Y")  # Store in same format

    due_date = parse_due_date(task.get("DueDate"))  # re-parse just to be safe
    days_left = (due_date - today).days if due_date else None
    print("Days left =", days_left)
    # --- Priority --- #
    if not update_data.get("Priority"):
        task["Priority"] = infer_priority(due_date, today)
        task["PriorityColor"] = PRIORITY_COLORS.get(task["Priority"], "#9ca3af")
    elif task["Priority"] != update_data["Priority"]:
        task["Priority"] = update_data["Priority"]
        if "PriorityColor" in update_data:
            task["PriorityColor"] = update_data["PriorityColor"]

    # --- Status --- #
    if not update_data.get("Status"):
        task["Status"] = infer_status(due_date, today)
        task["StatusColor"] = STATUS_COLORS.get(task["Status"], "#d1d5db")
    elif task["Status"] != update_data["Status"]:
        task["Status"] = update_data["Status"]
        if "StatusColor" in update_data:
            task["StatusColor"] = update_data["StatusColor"]

    # --- Progress --- #
    if "Progress" in update_data:
        try:
            task["Progress"] = int(update_data["Progress"])
        except (ValueError, TypeError):
            task["Progress"] = 0
    else:
        task["Progress"] = infer_progress(task["Status"], due_date, today)
    align_priority_with_status(task, days_left)
    return task

# region   Extra functions
def parse_due_date(due_str: Optional[str]) -> Optional[datetime]:
    if not due_str:
        return None
    try:
        return datetime.strptime(due_str.strip(), "%d/%m/%Y")
    except (ValueError, TypeError):
        return None
def infer_priority(due_date: Optional[datetime], today: datetime) -> str:
    if due_date is None:
        return "Missing"

    days_left = (due_date - today).days
    if days_left <= 2:
        return "Critical"
    elif days_left <= 5:
        return "High"
    elif days_left <= 10:
        return "Medium"
    else:
        return "Low"
def infer_status(due_date: Optional[datetime], today: datetime) -> str:
    if due_date is None:
        return "Future Plan"

    days_left = (due_date - today).days
    if days_left < 0:
        return "Stuck"
    elif days_left <= 2:
        return "Working On It"
    elif days_left <= 5:
        return "In Progress"
    elif days_left <= 10:
        return "Future Plan"
    else:
        return "Ready to Start"
def align_priority_with_status(task: dict, days_left: Optional[int]):
    status = task.get("Status")
    priority = task.get("Priority")

    if status == "Future Plan" and priority in ["Critical", "High"]:
        task["Priority"] = "Low"
        task["PriorityColor"] = PRIORITY_COLORS["Low"]
    elif status == "Stuck" and priority in ["Low", "Best Effort"]:
        task["Priority"] = "High"
        task["PriorityColor"] = PRIORITY_COLORS["High"]
    elif status == "Ready to Start" and priority == "Critical":
        if days_left is None or days_left > 2:
            task["Priority"] = "High"
            task["PriorityColor"] = PRIORITY_COLORS["High"]
def infer_progress(status: str, due_date: Optional[datetime], today: datetime) -> int:
    if status == "Done":
        return 100
    elif status in ["Pending Deploy", "Waiting for Review"]:
        return 90
    elif status in ["In Tests", "Updating"]:
        return 75
    elif status == "In Progress":
        if due_date:
            days_total = (due_date - today).days
            if days_total > 0:
                return max(25, min(75, 100 - int((days_total / 10) * 100)))
        return 50
    elif status == "Working On It":
        return 30
    elif status == "Ready to Start":
        return 0
    elif status == "Stuck":
        return 10
    else:
        return 0
# endregion




#
# @app.route("/update_task", methods=["POST"])
# def update_task():
#     update_data = request.json
#     task_id = update_data.get("ID")
#     # project_id = update_data.get("project_id")
#     sprint_id = update_data.get("SprintID")  # Get sprint ID
#     task_name = update_data.get("TaskName", "").strip()
#     status = update_data.get("Status")
#     priority = update_data.get("Priority")
#     color = update_data.get("BC")  # Background color for Status/Priority
#
#
#     if not task_id or not session["project_id"] or not sprint_id:
#         print("__1__")
#         return jsonify({"status": "error", "message": "Task ID, Sprint ID, and Project ID are required"}), 400
#
#     session["tasks"] = []
#
#
#     if "tasks" not in session or not isinstance(session["tasks"], list):
#         print("__2__")
#         return jsonify({"status": "error", "message": "No tasks found in session"}), 500
#
#     try:
#         task_id = int(task_id)
#         sprint_id = int(sprint_id)
#     except ValueError:
#         print("__3__")
#         return jsonify({"status": "error", "message": "Invalid Task or Sprint ID"}), 400
#
#     # Locate the sprint
#     # Locate the sprint
#     sprint = next((s for s in session["sprints"] if s["SprintID"] == sprint_id), None)
#     if not sprint:
#         print("__4__")
#         return jsonify({"status": "error", "message": "Sprint not found"}), 404
#
#     # Locate the task inside the sprint
#     task = next((t for t in sprint["Tasks"] if int(t["TaskID"]) == task_id), None)
#     if not task:
#         print("__5__")
#         return jsonify({"status": "error", "message": "Task not found"}), 404
#
#     change_log = []
#
#     if task_name and task.get("TaskName") != task_name:
#         change_log.append(f"Task name: '{task.get('TaskName')}' -> '{task_name}'")
#         task["TaskName"] = task_name
#
#     if status and task.get("Status") != status:
#         change_log.append(f"Status: '{task.get('Status')}' -> '{status}'")
#         task["Status"] = status
#         task["StatusColor"] = color
#
#     if priority and task.get("Priority") != priority:
#         change_log.append(f"Priority: '{task.get('Priority')}' -> '{priority}'")
#         task["Priority"] = priority
#         task["PriorityColor"] = color
#
#
#
#     # session.modified = True
#     connection.send(f"UPDATE_TASK#{session['client_id']}.{session['project_id']}.{sprint_id}${json.dumps(task)}")
#     print(task)
#     response = connection.receive()
#     print(response)
#     return jsonify({"status": "success", "updated_task": task, "changes": change_log})






# @app.route("/update_task", methods=["POST"])
# def update_task():
#     global client_id
#     """Update an existing task based on TaskID."""
#     update_data = request.json  # Get data from the request
#     task_id = update_data.get("ID")  # Unique TaskID to identify the task
#     project_id = update_data.get("project_id")  # Include project_id
#
#     if not task_id or not project_id:
#         return jsonify({"status": "error", "message": "Task ID and Project ID are required"}), 400
#
#     # Find the task with the matching TaskID
#     task = next((t for t in tasks if t["TaskID"] == task_id), None)
#
#     if not task:
#         return jsonify({"status": "error", "message": "Task not found"}), 404
#
#     # Track changes for logging
#     change_log = []
#     for key, new_value in update_data.items():
#         if key in task and task[key] != new_value:
#             change_log.append(f"{key}: '{task[key]}' -> '{new_value}'")
#             task[key] = new_value
#
#     # Handle status and priority color updates
#     if "Status" in update_data:
#         new_status = update_data["Status"]
#         new_status_color = STATUS_COLORS.get(new_status, "#d1d5db")  # Default color
#         if task.get("StatusColor") != new_status_color:
#             change_log.append(f"StatusColor: '{task.get('StatusColor')}' -> '{new_status_color}'")
#             task["StatusColor"] = new_status_color
#
#     if "Priority" in update_data:
#         new_priority = update_data["Priority"]
#         new_priority_color = PRIORITY_COLORS.get(new_priority, "#9ca3af")  # Default color
#         if task.get("PriorityColor") != new_priority_color:
#             change_log.append(f"PriorityColor: '{task.get('PriorityColor')}' -> '{new_priority_color}'")
#             task["PriorityColor"] = new_priority_color
#
#     # Handle background color update
#     if "BC" in update_data:
#         new_background_color = update_data["BC"]
#         current_background_color = task.get("background_color", "#d1d5db")  # Default neutral color
#         if new_background_color != current_background_color:
#             change_log.append(f"BackgroundColor: '{current_background_color}' -> '{new_background_color}'")
#             task["background_color"] = new_background_color
#
#     # Send the updated task to the connection
#     connection.send(f"UPDATE_TASK#{client_id}.{project_id}${task}")
#     response = connection.receive()
#     print(response)
#     # Log updates
#     print(f"Task Updated: {task}")
#     print(f"Change Log: {', '.join(change_log)}")
#     updated_task = task
#
#     # Return the updated task and changes
#     return jsonify({"status": "success", "updated_task": updated_task, "changes": change_log})


# Color mappings for status and priority
STATUS_COLORS = {
    "Ready to Start": "#d0ebff",
    "In Progress": "#facc15",
    "Waiting for Review": "#cfe2ff",
    "Updating": "#dbeafe",
    "Pending Deploy": "#e8e4d3",
    "Done": "#d1fae5",
    "Future Plan": "#baf5e0",
    "Working On It": "#e9d5ff",
    "Stuck": "#fca5a5",
    "In Tests": "#d9f99d",
    "": "#d1d5db",
}

PRIORITY_COLORS = {
    "Critical": "#f87171",
    "High": "#facc15",
    "Medium": "#bfdbfe",
    "Low": "#d1fae5",
    "Best Effort": "#e5e7eb",
    "Missing": "#9ca3af",
}

# endregion


import json

def get_notifications():
    print("Notification_1")
    if "email" not in session or not session["email"]:
        # Retrieve user email if not in session
        session_id = session["session_id"]
        clients[session_id]["connection"].send(f"GET_USER_EMAIL#{session.get('client_id')}")
        response = clients[session_id]["connection"].receive()
        if "ENDED" in response:
            return render_template("404.html",
                                   error="Hold on, buddy. Something is off...\nPlease 'wait' for the updates"), 404
        if not response or "User not found" in response:
            print("User not found in database.")
            return []  # Return empty list if user is not found

        session["email"] = response.strip()
        print(f"Email for client {session.get('client_id')} retrieved: {response}")

    # Retrieve pending requests (friends + workers)
    clients[session["session_id"]]["connection"].send(f"GET_PENDING_REQUESTS#{session['email']}")
    response = clients[session["session_id"]]["connection"].receive().strip()
    print("Raw received data Notification_2:", repr(response))  # Debugging output

    try:
        data = json.loads(response)  # ✅ Correct JSON parsing
    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}")
        return []

    notifications = []

    # New structure: list with a single dictionary containing "friends" and "workers"
    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        data_obj = data[0]

        # Handle friend requests
        if "friends" in data_obj and isinstance(data_obj["friends"], list):
            # Flatten in case of nested list
            flat_friends = [item for sublist in data_obj["friends"] if isinstance(sublist, list) for item in sublist]
            for friend_request in flat_friends:
                sender = friend_request.get('sender_username', 'Unknown')
                sender_id = friend_request.get('sender_id', 'Unknown')
                notif_type = friend_request.get('type', 'unknown')

                message = f"You have a new {notif_type} from {sender}"
                print("Formatted notification message:", message)

                friend_request["message"] = message
                notifications.append(friend_request)

        # Handle worker requests
        if "workers" in data_obj and isinstance(data_obj["workers"], list):
            flat_workers = [item for sublist in data_obj["workers"] if isinstance(sublist, list) for item in sublist]
            for worker_request in flat_workers:
                sender = worker_request.get('sender_username', 'Unknown')
                sender_id = worker_request.get('sender_id', 'Unknown')
                notif_type = worker_request.get('type', 'unknown')

                message = f"You have a new {notif_type} from {sender}"
                print("Formatted notification message:", message)

                worker_request["message"] = message
                notifications.append(worker_request)

    else:
        print("Unexpected response format.")
        return []

    print(f"Total notifications: {notifications}")
    return notifications


def friends():
    try:
        session_id = request.args.get("session_id") or session.get("session_id")
        client_id = clients[session_id]["client"].client_id
        connection = clients.get(session_id)["connection"]

        payload = json.dumps({"client_id": client_id, "active_users": list(connected_users.keys())})
        print("PAYLOAD", payload)
        if list(connected_users.keys()):
            connection.send(f"GET_FRIENDS#{payload}")
            response = connection.receive()
            friends_data = json.loads(response)

            if not isinstance(friends_data, dict) or "friends" not in friends_data:
                return []

            friends_list = friends_data["friends"]
            if not isinstance(friends_list, list):
                return []

            for friend in friends_list:
                friend["online"] = str(friend["id"]) in connected_users
            return friends_list
    except Exception:
        return []
        # if not session["friends"]:
        #     session["friends"] = friends_list
        #     clients[session_id]["client"].friends = friends_list
#region FRIENDS
@app.route("/get_friends", methods=["GET"])
def get_friends():
    # Pull session_id from URL first
    session_id = request.args.get("session_id") or session.get("session_id")

    if not session_id or "client_id" not in session:
        return render_template("404.html",
                               error="Hold on, buddy. Something is off...\nPlease wait for the updates"), 404
    try:
        client_id = clients[session_id]["client"].client_id
    except Exception:
        return render_template("404.html",
                                   error="Hold on, buddy. Something is off...\nPlease 'wait' for the updates"), 404
    connection = clients.get(session_id)["connection"]
    if not connection:
        return render_template("404.html", error="Hold on, buddy. Something is off...\nPlease 'wait' for the updates"), 404

    payload = json.dumps({"client_id": client_id, "active_users": list(connected_users.keys())})
    if len(list(connected_users.keys())) > 0:
        connection.send(f"GET_FRIENDS#{payload}")
        response = connection.receive()
        if "ENDED" in response:
            return render_template("404.html",
                                   error="Hold on, buddy. Something is off...\nPlease 'wait' for the updates"), 404
    else:
        return jsonify({"friends": []})
    # try:
    #     if not session["friends"]:
    #
    #         if not response:
    #
    # except

    try:
        friends_data = json.loads(response)

        if not isinstance(friends_data, dict) or "friends" not in friends_data:
            return jsonify({"error": "Invalid response format"}), 500

        friends_list = friends_data["friends"]
        if not isinstance(friends_list, list):
            return jsonify({"error": "Invalid response format"}), 500

        for friend in friends_list:
            friend["online"] = str(friend["id"]) in connected_users
        session["friends"] = friends_list
        clients[session_id]["client"].friends = friends_list
        return jsonify({"friends": [friend for friend in friends_list if friend["id"] != client_id]})

    except json.JSONDecodeError:
        return jsonify({"error": "Failed to parse JSON response"}), 500
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/send_friend_request", methods=["POST"])
def send_friend_request():
    # Pull session_id from URL first
    session_id = request.args.get("session_id") or session.get("session_id")

    if "client_id" not in session or "username" not in session:
        return jsonify({"error": "User not logged in"}), 401

    try:
        data = request.get_json()
        receiver_email = data.get("receiver_email")
        sender_id = clients[session_id]["client"].client_id
        sender_username = session["username"]

        print(f"📨 Sending friend request from {sender_id} ({sender_username}) to {receiver_email}")

        connection = clients.get(session_id)["connection"]
        if not connection:
            print("❌ Database connection missing!")
            return jsonify({"error": "Database connection not found"}), 500

        connection.send(f"GET_USER_BY_EMAIL#{receiver_email}")
        response = connection.receive()
        if "ENDED" in response:
            return render_template("404.html", error="Hold on, buddy. Something is off...\nPlease 'wait' for the updates"), 404
        if not response or "User not found" in response:
            return jsonify({"error": "User not found"}), 404

        try:
            receiver_id, receiver_username = response.strip().split("#")
        except ValueError:
            print(f"⚠️ Unexpected response format: {response}")
            return jsonify({"error": "Invalid response from database"}), 500

        print(f"✅ Found receiver: ID={receiver_id}, Username={receiver_username}")

        # Ensure sender_id is valid before proceeding
        if not sender_id or sender_id == "undefined":
            return jsonify({"error": "Invalid sender_id"}), 400

        # Send friend request command
        connection.send(f"ADD_FRIEND_REQUEST#{sender_id}.{receiver_id}")

        add_response = connection.receive()
        if "ENDED" in response:
            return render_template("404.html", error="Hold on, buddy. Something is off...\nPlease 'wait' for the updates"), 404

        if "Success" in add_response.strip():
            # Emit a WebSocket notification
            socketio.emit(f"friend_request_{receiver_id}", {
                "message": f"You have a new friend request from {sender_username}!",
                "sender_id": sender_id,
                "sender_username": sender_username
            }, room=receiver_id)
            # session["notifications"] =

            return jsonify({"success": "Friend request sent!"})
        else:
            return jsonify({"error": "Failed to send friend request"}), 500

    except Exception as e:
        print(f"⚠️ Error in send_friend_request: {str(e)}")
        return jsonify({"error": "Internal Server Error"}), 500

@app.route("/accept_friend_request", methods=["POST"])
def accept_friend_request():
    session_id = request.args.get("session_id") or session.get("session_id")

    if "client_id" not in session:
        return jsonify({"error": "User not logged in"}), 401

    try:
        data = request.get_json()
        sender_id = data.get("sender_id")
        status = data.get("status")
        receiver_id = clients[session_id]["client"].client_id

        if not sender_id or not status:
            return jsonify({"error": "Invalid request"}), 400

        connection = clients[session_id]["connection"]
        if not connection:
            return jsonify({"error": "Database connection not found"}), 500

        password = data.get("password")

        if status == "accepted":
            if password != session.get("password"):  # Validate password
                return jsonify({"success": False, "error": "Incorrect password"}), 403

            connection.send(f"CONFIRM_FRIENDSHIP#{sender_id}.{receiver_id}")
            confirm_response = connection.receive().strip()

            if "ENDED" in confirm_response:
                return render_template("404.html",
                                       error="Hold on, buddy. Something is off...\nPlease 'wait' for the updates"), 404

            if confirm_response == "Friendship confirmed":
                return jsonify({"success": "Friend request accepted!"})
            else:
                return jsonify({"error": "Friendship confirmation failed"}), 500

        elif status == "denied":
            connection.send(f"DECLINE_FRIEND_REQUEST#{sender_id}.{receiver_id}")
            decline_response = connection.receive().strip()

            if "ENDED" in decline_response:
                return render_template("404.html",
                                       error="Session ended. Try again later."), 404

            if decline_response == "Friendship declined":
                return jsonify({"success": "Friend request denied!"})
            else:
                return jsonify({"error": "Could not decline request"}), 500

        return jsonify({"error": "Invalid status"}), 400

    except Exception as e:
        print(f"Error in accept_friend_request: {str(e)}")
        return jsonify({"error": "Internal Server Error"}), 500
# @app.route("/accept_friend_request", methods=["POST"])
# def accept_friend_request():
#     # Pull session_id from URL first
#     session_id = request.args.get("session_id") or session.get("session_id")
#
#     if "client_id" not in session:
#         print("Unauthorized request - No session found")
#         return jsonify({"error": "User not logged in"}), 401
#
#     try:
#         data = request.get_json()
#         sender_id = data.get("sender_id")
#         status = data.get("status")
#         receiver_id = clients[session_id]["client"].client_id
#
#         if not sender_id or not status:
#             return jsonify({"error": "Invalid request"}), 400
#
#         print(f"Processing request from {sender_id} by {receiver_id}")
#
#         connection = clients[session_id]["connection"]
#         if not connection:
#             return jsonify({"error": "Database connection not found"}), 500
#         password = data.get("password")
#
#         if status == "accepted":
#             if password != session.get("password"):  # Verify session password
#                 return jsonify({"success": False, "error": "Incorrect password"}), 403
#             connection.send(f"CONFIRM_FRIENDSHIP#{sender_id}.{receiver_id}")
#             confirm_response = connection.receive()
#             if "ENDED" in confirm_response:
#                 return render_template("404.html",
#                                        error="Hold on, buddy. Something is off...\nPlease 'wait' for the updates"), 404
#             if confirm_response.strip() == "Friendship confirmed":
#                 return jsonify({"success": "Friend request accepted!"})
#             else:
#                 return jsonify({"error": "Friendship confirmation failed"}), 500
#
#         elif status == "denied":
#             return jsonify({"success": "Friend request denied!"})
#
#         return jsonify({"error": "Invalid status"}), 400
#
#     except Exception as e:
#         print(f"Error in accept_friend_request: {str(e)}")
#         return jsonify({"error": "Internal Server Error"}), 500

@socketio.on("new_friend_request")
def notify_receiver(data):
    # Pull session_id from URL first
    session_id = request.args.get("session_id") or session.get("session_id")

    connection = clients.get(session_id)["connection"]
    if not connection:
        return jsonify({"error": "Database connection not found"}), 500

    try:
        receiver_email = data["receiver_email"]
        connection.send(f"GET_USER_BY_EMAIL#{receiver_email}")
        response = connection.receive()
        if "ENDED" in response:
            return render_template("404.html",
                                   error="Hold on, buddy. Something is off...\nPlease 'wait' for the updates"), 404
        if "User not found" in response.strip:
            return

        recipient_id = response.split("#")[0]

        # Notify recipient
        socketio.emit(f"friend_request_{recipient_id}", {
            "message": "You have a new friend request!"
        }, room=recipient_id)

    except Exception as e:
        print(f"⚠️ Error in notify_receiver: {str(e)}")

@app.route("/pending_friend_requests", methods=["GET"])
def pending_friend_requests():
    session_id = request.args.get("session_id") or session.get("session_id")
    receiver_email = session.get("email")

    if not session_id or session_id not in clients:
        return jsonify({"error": "Session invalid"}), 401
    if not receiver_email:
        return jsonify({"error": "User not logged in"}), 401

    connection = clients[session_id]["connection"]
    if not connection:
        return jsonify({"error": "Database connection not found"}), 500

    connection.send(f"GET_PENDING_REQUESTS#{json.dumps({'email': receiver_email})}")
    response = connection.receive().strip()
    print("PENDING:", response)

    if "ENDED" in response:
        return jsonify({"error": "Session ended"}), 403
    if not response:
        return jsonify({"pending_requests": []})

    try:
        data = json.loads(response)
        pending_requests = []
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            data_obj = data[0]

            # Flatten and extract friend requests
            if "friends" in data_obj:
                flat_friends = [
                    item for sublist in data_obj["friends"]
                    if isinstance(sublist, list) for item in sublist
                ]
                pending_requests.extend(flat_friends)

        return jsonify({"pending_requests": pending_requests})
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid response format"}), 500

# region socketio
# Global dictionary to store connected users
connected_users = {}

# This will track which users are in which project rooms
user_rooms = {}

@app.route("/connected_users")
def get_connected_users():
    """Returns the list of currently connected users."""
    return jsonify({"connected_users": list(connected_users.keys())})

@socketio.on("connect")
def handle_connect():
    client_id = session.get("client_id")
    if client_id:
        connected_users[client_id] = {
            "client_id": client_id,
            "session_id": request.sid,
            "status": "online"
        }
        current_active_users = list(connected_users.keys())
        socketio.emit("update_online_status", {"active_users": current_active_users}, to="all")

        join_room(f"user_{client_id}")
        socketio.emit("update_online_status", {"id": client_id, "online": True}, to="all")

@socketio.on("disconnect")
def handle_disconnect():
    """Handles user disconnection and removes them from the connected list."""
    client_id = None
    for user_id, user_data in connected_users.items():
        if user_data["session_id"] == request.sid:
            client_id = user_id
            break

    if client_id:
        del connected_users[client_id]  # Remove the user from connected users

        # Notify other users that this user is offline
        socketio.emit("update_online_status", {"id": client_id, "online": False}, to=None)

        print(f"❌ User {client_id} disconnected.")
#
# rooms_lock   = threading.Lock()          # protects the two dicts below
# project_rooms = {}                       # {project_id: {client_id, …}}

project_rooms = []
join_project = []
@socketio.on("join_project")
def on_join_project(data):
    try:
        global project_rooms
        project_id = data.get("project_id")
        room = f"project_{project_id}"

        join_room(room)  # Joins the Socket.IO room
        print(f"Client {request.sid} joined {room}")
        if not project_rooms:
            project_rooms = [{"project_id": project_id, "users": [f"{session['client_id']}"]}]
        else:
            for project in project_rooms:
                if project_id in project["project_id"]:
                    if not session['client_id'] in project['users']:
                        project['users'].append(session['client_id'])
                        print(f"{session['username']} has joined the room!")
                # for i in project["users"]:

        emit("joined_room", {"room": room})  # <-- emit ONLY to the sender!
    except Exception:
            return render_template("404.html", error="You made a mistake, buddy"), 404
@socketio.on("leave_project")
def on_leave_project(data):
    """Handles users leaving a project room."""
    client_id = session.get("client_id")
    project_id = data.get("project_id")

    if client_id and project_id:
        room = f"project_{project_id}"
        leave_room(room)

        # Remove the room from the user's list of rooms
        if client_id in user_rooms and room in user_rooms[client_id]:
            user_rooms[client_id].remove(room)

        print(f"Client {request.sid} ({client_id}) left {room}")
        emit("left_room", {"room": room}, room=room)

@socketio.on("team_update")
def handle_team_update(data):
    sender = session.get("username", "Unknown")
    project_id = data.get("project_id")

    if not project_id:
        print("❗ No project_id provided with message.")
        return

    message_text = data.get("message", "").strip()
    if not message_text:
        return

    message_data = {
        "sender": sender,
        "message": message_text
    }

    # Save the message to file
    save_message_to_file(project_id, sender, message_text)

    # Emit to the project room
    socketio.emit("team_update", message_data, room=f"project_{project_id}")
    print(f"📨 Message broadcast to project_{project_id} from {sender}")
@socketio.on('chat_message')
def handle_chat_message(data):
    message = data['message']
    emit('chat_message', {'message': message}, broadcast=True)
    print("Message", message)

def save_message_to_file(project_id, sender, message):
    user_dir = f"static/Chat/{project_id}"
    os.makedirs(user_dir, exist_ok=True)
    filepath = os.path.join(user_dir, "chat.txt")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(filepath, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {sender}: {message}\n")
@app.route("/chat_history/<project_id>")
def chat_history(project_id):
    filepath = f"static/Chat/{project_id}/chat.txt"
    if not os.path.exists(filepath):
        return jsonify(messages=[])  # no history yet

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Return lines as a list of strings
    return jsonify(messages=lines)
# endregion

# endregion

# region    --- WORKERS ---
@app.route('/team_dashboard')
@role_required('Manager', 'Worker')
def team_dashboard():
    return render_template('team_dashboard.html')

def fetch_workers_for_manager(manager_id):
    connection = clients.get(session["session_id"])["connection"]
    if not connection:
        return []

    connection.send(f"GET_WORKERS#{manager_id}")
    response = connection.receive()
    if "ENDED" in response:
        return render_template("404.html",
                               error="Hold on, buddy. Something is off...\nPlease 'wait' for the updates"), 404
    try:
        workers = json.loads(response)
        if isinstance(workers, dict):
            workers = [workers]
            session["workers"] = workers
            print("workers: ", workers)
        return workers
    except json.JSONDecodeError:
        return []

@role_required('Manager')
@app.route('/my_workers')
def my_workers():
    if "client_id" not in session:
        return redirect(url_for("login"))

    manager_id = session["client_id"]
    connection = clients.get(session["session_id"])["connection"]

    if not connection:
        return jsonify({"error": "No active connection."}), 500

    connection.send(f"GET_WORKERS#{manager_id}")
    response = connection.receive()
    if "ENDED" in response:
        return render_template("404.html",
                               error="Hold on, buddy. Something is off...\nPlease 'wait' for the updates"), 404
    try:
        workers = json.loads(response)
        return render_template('my_workers.html', workers=workers)
    except json.JSONDecodeError:
        return "Error loading workers", 500

@app.route('/register_worker', methods=['POST'])
def register_worker():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    manager_id = request.form['manager_id']  # Select a manager from dropdown!

    session_id = str(uuid.uuid4())
    if session_id not in clients:
        clients[session_id] = ConnectionWithDatabase(session_id)

    connection = clients[session_id]
    if not connection.connected:
        connection.connect()
    if not connection.connected:
        return render_template('404.html', error="Database connection failed.")

    connection.send(f"SIGNUP_WORKER {username}#{email}#{password}#{manager_id}")
    response = connection.receive()
    if "ENDED" in response:
        return render_template("404.html",
                               error="Hold on, buddy. Something is off...\nPlease 'wait' for the updates"), 404
    print("response=", response)

    if response and "successfully" in response:
        session["username"] = username
        session["email"] = email
        session["session_id"] = session_id
        session["client_id"] = response.split("ID:")[1] if "ID:" in response else None

        return redirect(url_for('login'))

    return render_template('404.html', error="Registration failed. Please try again.")

@app.route('/assign_project_to_worker', methods=['POST'])
def assign_project_to_worker():
    if session.get('role') != 'Manager':
        return jsonify({"error": "Unauthorized access."}), 403

    data = request.get_json()
    worker_id = data.get('worker_id')
    project_id = data.get('project_id')

    if not worker_id or not project_id or worker_id == session['client_id'] :
        return jsonify({"error": "Missing worker or project ID."}), 400

    connection = clients[session["session_id"]]["connection"]
    connection.send(f"ASSIGN_PROJECT#{session['client_id']}.{worker_id}.{project_id}")
    response = connection.receive()
    if "ENDED" in response:
        return render_template("404.html",
                               error="Hold on, buddy. Something is off...\nPlease 'wait' for the updates"), 404
    if "assigned" in response.lower():
        return jsonify({"success": True})
    else:
        return jsonify({"error": response}), 500

@app.route('/add_worker', methods=['POST'])
def add_worker():
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({'error': 'Email is required'}), 400

    if email == session["email"]:
        return jsonify({'error': 'Others email is required'}), 400
    session_id = session["session_id"]
    clients[session_id]["connection"].send(f"SEND_REQUEST_WORKER#{session['client_id']}.{email}")

    return jsonify({'message': 'Worker added successfully'}), 200

@app.route('/accept_work_request', methods=['POST'])
def accept_work_request():
    data = request.get_json()
    sender_id = data.get('sender_id')
    # TODO: Process accepting the work request
    return jsonify({"success": True})

@app.route('/decline_work_request', methods=['POST'])
def decline_work_request():
    data = request.get_json()
    sender_id = data.get('sender_id')
    # TODO: Process declining the work request
    return jsonify({"success": True})
# endregion

#region -- OTHERS --
@app.route('/reset_timer', methods=['POST'])
def reset_timer():
    if "username" in session:
        session["time_since_login"] = time.time()
    return '', 204
@app.route('/register', methods=['POST'])
def register():
    try:
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        session_id = str(uuid.uuid4())
        connection = ConnectionWithDatabase(session_id)

        if not connection.connected:
            connection.connect()
        if not connection.connected:
            return render_template('404.html', error="Database connection failed.")

        connection.send(f"SIGNUP {username}#{email}#{password}")
        response = connection.receive()
        if "ENDED" in response:
            return render_template("404.html",
                                   error="Hold on, buddy. Something is off...\nPlease 'wait' for the updates"), 404
        print("response=", response)

        if response and "successfully" in response:
            return render_template('login.html', message="You have registered successfully!")

        return render_template('404.html', error="Registration failed. Please try again.")

    except Exception as e:
        import traceback
        print("Exception in /register:", e)
        traceback.print_exc()
        return render_template('404.html', error="Internal server error during registration.")
@app.route('/logout')
def logout():
    session_id = session.get("session_id")
    if session_id and session_id in clients:
        connection = clients[session_id].get("connection")
        if connection:
            try:
                connection.close()
            except Exception as e:
                print(f"Error closing connection: {e}")
        clients.pop(session_id, None)  # Clean up the client entry safely

    keys_to_clear = [
        'username', 'password', 'session_id', 'client_id',
        'notification', 'time_since_login', 'friends', 'tasks',
        'project_id', 'projects', 'shared_projects', 'role', 'pic',
        'sprints', 'email', 'workers', 'project_id', 'task_id'
    ]
    for key in keys_to_clear:
        session.pop(key, None)

    # Redirect back to login
    return redirect(url_for('login'))
@app.route('/profile')
def profile():
    try:
        session_id = session["session_id"]
        connection = clients[session_id]["connection"]
        if not connection.connected:
            return render_template("404.html",
                                   error="Hold on, buddy. Something is off...\nPlease 'wait' for the updates"), 404
        return render_template('profile.html')
    except Exception:
            return render_template("404.html", error="You made a mistake, buddy"), 404
@app.route('/listToDo')
def listToDo():
    try:
        session_id = session["session_id"]
        connection = clients[session_id]["connection"]
        if not connection.connected:
            return render_template("404.html",
                                   error="Hold on, buddy. Something is off...\nPlease 'wait' for the updates"), 404
        return render_template('listToDo.html')
    except Exception:
            return render_template("404.html", error="You made a mistake, buddy"), 404
@app.route('/404')
def page_404():
    return render_template('404.html')

@role_required('Guest')
@app.route('/become_manager')
def become_manager():
    try:
        session_id = session['session_id']
        user_dir = f"static/Become_a_manager"
        with open(user_dir+f"/become_a_manager.txt", 'r', encoding='utf-8') as f:
            lines = f.readlines()
        # if  # no lines or the username didn't appear in the file:
        #     - Make sure the isChecked value is False

        return render_template('become_manager.html', projects=session['projects'], isChecked= '....')
    except Exception as e:
        print(e)
        return render_template("404.html", error=e), 404


@app.route('/settings')
def settings():
    try:
        session_id = session["session_id"]
        connection = clients[session_id]["connection"]
        if not connection.connected:
            return render_template("404.html",
                                   error="Hold on, buddy. Something is off...\nPlease 'wait' for the updates"), 404
        return render_template('settings.html')
    except Exception:
            return render_template("404.html", error="You made a mistake, buddy"), 404
@app.route('/upload-avatar', methods=['POST'])
def upload_avatar():
    try:
        session_id = session["session_id"]
        connection = clients[session_id]["connection"]
        if not connection.connected:
            return render_template("404.html",
                                   error="Hold on, buddy. Something is off...\nPlease 'wait' for the updates"), 404

        data_url = request.form['croppedImage']
        if not data_url:
            return "No image data", 400

        # Extract base64 part from data URL
        match = re.search(r'^data:image/(png|jpeg);base64,(.*)$', data_url)
        if not match:
            return "Invalid image format", 400

        image_data = base64.b64decode(match.group(2))
        user_dir = f"static/profile_pics/{session['username']}"
        # Create the directory if it doesn't exist
        os.makedirs(user_dir, exist_ok=True)
        with open(f"{user_dir}/avatar.png", 'wb') as f:
            f.write(image_data)  # replace image_data with your actual image bytes

        connection.send(f"UPDATE_PROFILE#{session['client_id']}.{user_dir}/avatar.png")
        return redirect('/profile')
    except Exception:
        return render_template("404.html", error="You made a mistake, buddy"), 404
# endregion

def start():
    socketio_thread = threading.Thread(target=run_socketio)
    socketio_thread.daemon = True  # Allow Flask to exit cleanly
    socketio_thread.start()

    app.run(debug=True, use_reloader=False, threaded=True, host='0.0.0.0', port=5000)

