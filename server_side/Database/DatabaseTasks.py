import sqlite3, os

class DatabaseTasks:
    def __init__(self, conn):
        self.conn = conn
        # self.conn_sprint = conn
        self.enable_foreign_keys()
        self.createDb()

    def enable_foreign_keys(self):
        """Enable foreign key constraints in SQLite."""
        self.conn.execute("PRAGMA foreign_keys = ON;")

    def createDb(self):
        """Create necessary tables if they don't exist."""

        #region Tasks Table
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS Tasks (
                TaskID INTEGER PRIMARY KEY AUTOINCREMENT,
                TaskName TEXT NOT NULL,
                Priority TEXT,
                Status TEXT,
                StatusColor TEXT,
                PriorityColor TEXT,
                Owners TEXT,
                DueDate DATE,
                Tags TEXT,
                Progress INTEGER,
                ProjectID INTEGER,
                SprintID INTEGER,  -- Directly adding SprintID
                ClientID INTEGER,
                FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID) ON DELETE CASCADE,
                FOREIGN KEY (SprintID) REFERENCES Sprints(SprintID) ON DELETE CASCADE,
                FOREIGN KEY (ClientID) REFERENCES CLIENTS(ID)
            );
        ''')
        print("Tasks table created successfully.")
        #endregion Tasks Table

        #region Comments Table
        self.conn.execute('''
                        CREATE TABLE IF NOT EXISTS Comments (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            task_id INTEGER NOT NULL,
                            user_id INTEGER NOT NULL,
                            content TEXT NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (task_id) REFERENCES Tasks(TaskID) ON DELETE CASCADE
                        );
                    ''')
        self.conn.execute('''
                        CREATE TABLE IF NOT EXISTS Files (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            comment_id INTEGER,
                            file_path TEXT NOT NULL,
                            FOREIGN KEY (comment_id) REFERENCES Comments(id) ON DELETE CASCADE
                        );
                    ''')

        print("Comments table created successfully.")
        #endregion Comments Table

        # region Sprint Tables
        self.conn.execute('''
                CREATE TABLE IF NOT EXISTS Sprints (
                    SprintID INTEGER PRIMARY KEY AUTOINCREMENT,
                    SprintName TEXT NOT NULL,
                    ProjectID INTEGER,
                    SprintColor TEXT,
                    FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID)
                );
            ''')
        print("Sprints table created successfully.")

        # # Check if the SprintColor column exists before adding it
        # cursor = self.conn.cursor()
        # cursor.execute("PRAGMA table_info(Sprints);")
        # columns = [col[1] for col in cursor.fetchall()]
        #
        # if "SprintColor" not in columns:
        #     try:
        #         self.conn.execute("ALTER TABLE Sprints ADD COLUMN SprintColor TEXT;")
        #         print("SprintColor column added successfully.")
        #     except sqlite3.OperationalError as e:
        #         print(f"Error adding SprintColor column: {e}")
        #
        # self.conn.commit()

        self.conn.execute('''
                        CREATE TABLE IF NOT EXISTS SprintTasks (
                            SprintTaskID INTEGER PRIMARY KEY AUTOINCREMENT,
                            SprintID INTEGER NOT NULL,
                            TaskID INTEGER NOT NULL,
                            FOREIGN KEY (SprintID) REFERENCES Sprints(SprintID) ON DELETE CASCADE,
                            FOREIGN KEY (TaskID) REFERENCES Tasks(TaskID) ON DELETE CASCADE
                        );
                    ''')
        print("SprintTasks table created successfully.")
        # endregion

        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.commit()

    def duplicateSprintsAndTasks(self, original_project_id, new_project_id):
        try:
            # Step 1: Duplicate Sprints
            sprint_query = """
            INSERT INTO Sprints (SprintName, ProjectID, SprintColor)
            SELECT SprintName, ?, SprintColor
            FROM Sprints WHERE ProjectID = ?
            """
            self.conn.execute(sprint_query, (new_project_id, original_project_id))
            self.conn.commit()

            # Step 2: Map old Sprints to new Sprints
            sprint_mapping_query = """
            SELECT Old.SprintID, New.SprintID FROM Sprints AS Old
            JOIN Sprints AS New ON Old.SprintName = New.SprintName
            WHERE Old.ProjectID = ? AND New.ProjectID = ?
            """
            cursor = self.conn.execute(sprint_mapping_query, (original_project_id, new_project_id))
            sprint_mapping = {row[0]: row[1] for row in cursor.fetchall()}  # {old_sprint_id: new_sprint_id}

            # Step 3: Duplicate Tasks
            for old_sprint_id, new_sprint_id in sprint_mapping.items():
                task_query = """
                INSERT INTO Tasks (TaskName, Priority, Status, StatusColor, PriorityColor, Owners, DueDate, Tags, Progress, ProjectID, SprintID, ClientID)
                SELECT TaskName, Priority, Status, StatusColor, PriorityColor, Owners, DueDate, Tags, Progress, ?, ?
                FROM Tasks WHERE ProjectID = ? AND SprintID = ?
                """
                self.conn.execute(task_query, (new_project_id, new_sprint_id, original_project_id, old_sprint_id))

            self.conn.commit()

            # Step 4: Map old Tasks to new Tasks
            task_mapping_query = """
            SELECT Old.TaskID, New.TaskID FROM Tasks AS Old
            JOIN Tasks AS New ON Old.TaskName = New.TaskName
            WHERE Old.ProjectID = ? AND New.ProjectID = ?
            """
            cursor = self.conn.execute(task_mapping_query, (original_project_id, new_project_id))
            task_mapping = {row[0]: row[1] for row in cursor.fetchall()}  # {old_task_id: new_task_id}

            # Step 5: Duplicate SprintTasks (to maintain Sprint <-> Task relations)
            for old_task_id, new_task_id in task_mapping.items():
                sprint_task_query = """
                INSERT INTO SprintTasks (SprintID, TaskID)
                SELECT ?, ?
                FROM SprintTasks WHERE TaskID = ?
                """
                self.conn.execute(sprint_task_query, (sprint_mapping[old_sprint_id], new_task_id, old_task_id))

            self.conn.commit()

            print(f"Sprints, tasks, and relationships duplicated successfully for project {new_project_id}!")

        except sqlite3.Error as e:
            print(f"Error duplicating sprints and tasks: {e}")

    # region   Sprints


    def update_sprint(self, list_items):
        print("WORKS")
        update_query = '''
                        UPDATE Sprints
                        SET SprintName = ?,
                            SprintColor = ?
                        WHERE SprintID = ?
                    '''
        data = (
            list_items[1],  # SprintName
            list_items[2],  # SprintColor
            list_items[0],  # sprint_id
        )
        self.conn.execute(update_query, data)
        self.conn.commit()


    def add_sprint_with_task(self, sprint_details, client_id, project_id):
        """
        Adds a new sprint and automatically creates a linked task.
        :param sprint_details: List containing [SprintName, SprintColor]
        :param client_id: The ClientID for the task
        :param project_id: The ProjectID for the sprint and task
        """
        cursor = self.conn.cursor()
        try:
            sprint_name = sprint_details[1]
            sprint_color = sprint_details[2]

            # Insert sprint without SprintID (auto-generated)
            cursor.execute('''
                INSERT INTO Sprints (SprintName, SprintColor, ProjectID)
                VALUES (?, ?, ?)
            ''', (sprint_name, sprint_color, project_id))

            sprint_id = cursor.lastrowid  # ✅ Get the auto-generated SprintID


            cursor.execute('''
                INSERT INTO Tasks (TaskName, ClientID, ProjectID)
                VALUES (?, ?, ?)
            ''', ('Task for Sprint ' + str(sprint_id), client_id, project_id))
            task_id = cursor.lastrowid  # Get the TaskID of the new task

            # Link Task to Sprint
            cursor.execute('''
                INSERT INTO SprintTasks (SprintID, TaskID)
                VALUES (?, ?)
            ''', (sprint_id, task_id))

            self.conn.commit()
            print(f"Sprint '{sprint_name}' (ID: {sprint_id}) with Task linked successfully!")
            return sprint_id

        except sqlite3.Error as e:
            print(f"Error adding sprint and task: {e}")
            self.conn.rollback()
            return None

    def add_sprint(self, sprint_name, project_id):
        """
        Adds a new sprint to the database.
        :param sprint_name: The name of the sprint.
        :param project_id: The project to which the sprint belongs.
        """
        cursor = self.conn.cursor()
        cursor.execute('''
               INSERT INTO Sprints (SprintName, ProjectID)
               VALUES (?, ?)
           ''', (sprint_name, project_id))

        self.conn.commit()

    def delete_sprint(self, sprint_id, project_id):
        """
        Deletes a sprint by ID and project, removes all linked tasks and their sprint-task relations.
        Ensures the sprint belongs to the given project before deletion.
        """
        try:
            cursor = self.conn.cursor()

            # Step 1: Get all task IDs linked to this sprint
            cursor.execute('''
                SELECT TaskID FROM SprintTasks
                WHERE SprintID = ?
            ''', (sprint_id,))
            task_ids = [row[0] for row in cursor.fetchall()]

            # Step 2: Confirm the sprint belongs to the specified project
            cursor.execute('''
                SELECT 1 FROM Sprints
                WHERE SprintID = ? AND ProjectID = ?
            ''', (sprint_id, project_id))
            if not cursor.fetchone():
                print(f"No sprint with ID {sprint_id} found for project {project_id}.")
                return

            # Step 3: Delete the sprint (cascades SprintTasks entries)
            cursor.execute('''
                DELETE FROM Sprints
                WHERE SprintID = ? AND ProjectID = ?
            ''', (sprint_id, project_id))

            # Step 4: Delete the tasks linked to the sprint
            if task_ids:
                cursor.executemany('''
                    DELETE FROM Tasks
                    WHERE TaskID = ?
                ''', [(task_id,) for task_id in task_ids])

            self.conn.commit()
            print(f"Sprint {sprint_id} and its tasks were deleted successfully.")

        except sqlite3.Error as e:
            print(f"Error deleting sprint {sprint_id} and its tasks: {e}")
            self.conn.rollback()

    # def get_sprints(self, project_id):
    #     """
    #     Retrieves all sprints for a given project **without tasks** (Tasks will be fetched separately).
    #     """
    #     cursor = self.conn.cursor()
    #     query = '''
    #         SELECT SprintID, SprintName, SprintColor
    #         FROM Sprints
    #         WHERE ProjectID = ?
    #         ORDER BY SprintID
    #     '''
    #
    #     cursor.execute(query, (project_id,))
    #     rows = cursor.fetchall()
    #
    #     sprints = []
    #     for row in rows:
    #         sprints.append({
    #             "SprintID": row[0],
    #             "SprintName": row[1],
    #             "SprintColor": row[2],
    #             "Tasks": None  # Fetch tasks separately when needed
    #         })
    #
    #     cursor.close()
    #     return sprints

    def sprint_tasks(self, project_id, client_id):
        """
        Retrieves all sprints for a given project along with their associated tasks.
        :param project_id: The ID of the project.
        :return: A list of dictionaries containing sprint and task information.
        """
        cursor = self.conn.cursor()
        query = '''
            SELECT s.SprintID, s.SprintName, s.SprintColor, t.TaskID, t.TaskName
            FROM Sprints s
            LEFT JOIN SprintTasks st ON s.SprintID = st.SprintID
            LEFT JOIN Tasks t ON st.TaskID = t.TaskID
            WHERE s.ProjectID = ?
        '''

        cursor.execute(query, (project_id,))
        rows = cursor.fetchall()

        sprints_dict = {}  # Store sprints as a dictionary to avoid duplication

        for row in rows:
            sprint_id, sprint_name, sprint_color, task_id, task_name = row

            if sprint_id not in sprints_dict:
                sprints_dict[sprint_id] = {
                    "SprintID": sprint_id,
                    "SprintName": sprint_name,
                    "SprintColor": sprint_color,
                    "Tasks": []
                }
            print(sprints_dict)
            tasks = self.read_list(project_id, sprint_id)
            if task_id is not None:  # Ensure we only append valid tasks
                if not tasks:
                    self.add_empty_item(project_id, sprint_id, client_id, "New Task")
                tasks = self.read_list(project_id, sprint_id)
                print(tasks)
                sprints_dict[sprint_id]["Tasks"].extend(tasks)  # Flatten list
            else:
                if not tasks:
                    self.add_empty_item(project_id, sprint_id, client_id, "New Task")
                    sprints_dict[sprint_id]["Tasks"].extend(tasks)  # Flatten list
                    print(tasks)

        print(sprints_dict)
        return list(sprints_dict.values())  # Convert dictionary to list

    # endregion

    # region Tasks
    def add_empty_item(self, project_id, sprint_id, client_id, taskName):
        """Add a new empty task for the specified client and project."""

        try:
            add_query = '''
                INSERT INTO Tasks (
                    TaskName, 
                    Priority, 
                    Status, 
                    StatusColor, 
                    PriorityColor, 
                    Owners, 
                    DueDate, 
                    Tags, 
                    Progress,
                    ProjectID,
                    SprintID,
                    ClientID
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            '''
            data = (
                taskName,  # TaskName
                "Medium",  # Priority
                "Ready to start",  # Status
                "#d0ebff",  # StatusColor
                "#bfdbfe",  # PriorityColor
                "",  # Owners
                None,  # DueDate
                "",  # Tags
                0,  # Progress
                project_id,  # ProjectID
                sprint_id,  # ClientID
                client_id
            )
            self.conn.execute(add_query, data)
            self.conn.commit()
            print("Empty task added.")
        except sqlite3.Error as e:
            print(f"Error adding empty task: {e}")

    def update_item(self, list_items):
        """Update a task in the database based on the TaskID."""
        try:
            # Fetch the current SprintID from the database before updating
            cursor = self.conn.cursor()
            cursor.execute("SELECT SprintID, ProjectID FROM Tasks WHERE TaskID = ?", (list_items[0],))
            result = cursor.fetchone()

            if result:
                correct_sprint_id, correct_project_id = result
                print(f"Correct SprintID in DB: {correct_sprint_id}, Correct ProjectID in DB: {correct_project_id}")
            else:
                print(f"Task {list_items[0]} not found in database.")
                return

            update_query = '''
                UPDATE Tasks
                SET TaskName = ?, 
                    Priority = ?, 
                    Status = ?, 
                    StatusColor = ?, 
                    PriorityColor = ?, 
                    Owners = ?, 
                    DueDate = ?, 
                    Tags = ?, 
                    Progress = ?
                WHERE TaskID = ? AND SprintID = ? AND ProjectID = ?;
            '''

            # Ensure we're using the correct SprintID
            data = (
                list_items[1],  # TaskName
                list_items[2],  # Priority
                list_items[3],  # Status
                list_items[4],  # StatusColor
                list_items[5],  # PriorityColor
                list_items[6],  # Owners
                list_items[7],  # DueDate
                list_items[8],  # Tags
                list_items[9],  # Progress
                list_items[0],  # TaskID
                correct_sprint_id,  # Correct SprintID from DB
                correct_project_id  # Correct ProjectID from DB
            )

            cursor.execute(update_query, data)

            if cursor.rowcount == 0:
                print(
                    f"❌ Update failed: No rows matched TaskID={list_items[0]}, SprintID={correct_sprint_id}, ProjectID={correct_project_id}")
            else:
                self.conn.commit()
                print(f"✅ Task {list_items[0]} updated successfully!")

        except sqlite3.Error as e:
            print(f"Error updating task: {e}")

    def delete_task(self, ids):
        cursor = self.conn.cursor()

        # Delete the specified task
        delete_query = "DELETE FROM Tasks WHERE ProjectID = ? AND TaskID = ?"
        cursor.execute(delete_query, tuple(ids))

        self.conn.commit()
        cursor.close()

        print(f"Task with ID {ids} deleted successfully.")

    def updataDrag(self, target_id, draggable_id):
        target_id = int(target_id)
        draggable_id = int(draggable_id[0])

        cursor = self.conn.cursor()
        try:
            # Fetch the positions of the dragged and target tasks
            cursor.execute("SELECT TaskID FROM Tasks WHERE TaskID = ?", (draggable_id,))
            dragged_task_position = cursor.fetchone()

            cursor.execute("SELECT TaskID FROM Tasks WHERE TaskID = ?", (target_id,))
            target_task_position = cursor.fetchone()

            # Check if positions were fetched successfully
            if not dragged_task_position or not target_task_position:
                return {"error": "Invalid task IDs"}

            # Swap the positions
            dragged_task_position = dragged_task_position[0]
            target_task_position = target_task_position[0]

            cursor.execute("UPDATE Tasks SET Position = ? WHERE TaskID = ?", (target_task_position, draggable_id))
            cursor.execute("UPDATE Tasks SET Position = ? WHERE TaskID = ?", (dragged_task_position, target_id))

            # Commit the changes
            self.conn.commit()
            return {"success": True, "message": "Task positions updated successfully"}

        except Exception as e:
            return {"error": str(e)}

    def read_list(self, project_id, sprint_id=None):
        """
        Retrieves tasks for a given project and optionally filters by sprint.

        :param project_id: The ID of the project to retrieve tasks for.
        :param sprint_id: (Optional) The ID of the sprint to filter tasks by.
        :return: A list of task dictionaries.
        """
        cursor = self.conn.cursor()

        # Base query
        query = '''
            SELECT TaskID, TaskName, Priority, Status, StatusColor, PriorityColor, 
                   Owners, DueDate, Tags, Progress, SprintID
            FROM Tasks
            WHERE ProjectID = ?
        '''
        params = [project_id]

        # Add sprint filter if provided
        if sprint_id is not None:
            query += " AND SprintID = ?"
            params.append(sprint_id)

        # Execute query
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()

        # Convert to a list of dictionaries (using list comprehension)
        tasks = [
            {
                "TaskID": row[0],
                "TaskName": row[1],
                "Priority": row[2],
                "Status": row[3],
                "StatusColor": row[4],
                "PriorityColor": row[5],
                "Owners": row[6],
                "DueDate": row[7],
                "Tags": row[8],
                "Progress": row[9],
                "SprintID": row[10]
            }
            for row in rows
        ]

        cursor.close()
        return tasks
    # endregion

    #region Comments
    def get_comments(self, task_id):
        """
        Retrieves comments and associated files for a given task.

        :param task_id: The ID of the task to fetch comments for.
        :return: A list of comment dictionaries, each containing a list of files.
        """
        cursor = self.conn.cursor()

        query = '''
            SELECT c.id, c.task_id, c.user_id, c.content, c.created_at, f.file_path
                FROM Comments c
                LEFT JOIN Files f ON c.id = f.comment_id
                WHERE c.task_id = ?
                ORDER BY c.created_at ASC;
        '''
        cursor.execute(query, (task_id,))
        rows = cursor.fetchall()

        comments = {}
        for row in rows:
            comment_id = row[0]
            if comment_id not in comments:
                comments[comment_id] = {
                    "CommentID": row[0],
                    "TaskID": row[1],
                    "UserID": row[2],
                    "Content": row[3],
                    "CreatedAt": row[4],
                    "Files": []
                }
            if row[5]:
                comments[comment_id]["Files"].append(row[5])

        cursor.close()
        print(comments.values())
        return list(comments.values())

    def add_comment(self, task_id, user_id, content):
        query = '''
            INSERT INTO Comments (task_id, user_id, content) VALUES (?, ?, ?);
        '''
        self.conn.execute(query, (task_id, user_id, content))
        self.conn.commit()
        print("Comment added successfully.")


    def update_comment(self, comment_id, new_content):
        query = "UPDATE Comments SET content = ? WHERE id = ?"
        self.conn.execute(query, (new_content, comment_id))
        self.conn.commit()
        print("Comment updated successfully.")


    def delete_comment(self, comment_id):
        query = "DELETE FROM Comments WHERE id = ?"
        self.conn.execute(query, (comment_id,))
        self.conn.commit()
        print("Comment deleted successfully.")


    def add_file(self, comment_id, file_path):
        query = "INSERT INTO Files (comment_id, file_path) VALUES (?, ?)"
        self.conn.execute(query, (comment_id, file_path))
        self.conn.commit()
        print("File attached successfully.")


    def delete_file(self, file_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT file_path FROM Files WHERE id = ?", (file_id,))
        file_path = cursor.fetchone()

        if file_path and os.path.exists(file_path[0]):
            os.remove(file_path[0])
            print("File deleted from disk.")

        query = "DELETE FROM Files WHERE id = ?"
        self.conn.execute(query, (file_id,))
        self.conn.commit()
        print("File record deleted successfully.")
    #end Comments