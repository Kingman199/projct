import sqlite3

class DatabaseProjects:
    def __init__(self, conn):
        self.conn = conn
        self.createDb()

    def createDb(self):
        self.conn.execute('''   
            CREATE TABLE IF NOT EXISTS Projects (
                ProjectID INTEGER PRIMARY KEY AUTOINCREMENT,
                ProjectName TEXT NOT NULL,
                ProjectDescription TEXT DEFAULT '',
                ClientID INTEGER NOT NULL,
                FOREIGN KEY (ClientID) REFERENCES CLIENTS(ID)
            )
        ''')
        print("Projects table created successfully")

        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS SharedProject (
                ShareID INTEGER PRIMARY KEY AUTOINCREMENT,  -- Unique ID for this table
                ProjectID INTEGER NOT NULL,
                OwnerID INTEGER NOT NULL,
                ClientID INTEGER NULL,
                FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID) ON DELETE CASCADE,
                FOREIGN KEY (OwnerID) REFERENCES PROJECTS(ClientID),
                FOREIGN KEY (ClientID) REFERENCES PROJECTS(ClientID)
            )
        ''')
        print("SharedProject table created successfully")

    def getProjectByID(self, id):
        query = """
        SELECT *
        FROM Projects
        WHERE ProjectID = ?
        """
        cursor = self.conn.execute(query, (id,))
        return cursor.fetchone()

    def getProjectByName(self, project_name):
        query = """
        SELECT ProjectID, ProjectName, ProjectDescription
        FROM Projects
        WHERE ProjectName = ?
        """
        cursor = self.conn.execute(query, (project_name,))
        return cursor.fetchone()

    def addProject(self, pName, pD, client_id):
        try:
            # Insert the new project
            query = """
            INSERT INTO Projects (ProjectName, ProjectDescription, ClientID)
            VALUES (?, ?, ?)
            """
            cursor = self.conn.execute(query, (pName, pD, client_id))
            new_project_id = cursor.lastrowid  # Retrieve the newly generated ID
            self.conn.commit()

            print(f"Project '{pName}' added successfully with ID {new_project_id}!")
            return new_project_id  # Return the new ID for further use

        except sqlite3.Error as e:
            print(f"Error adding project: {e}")
            return None  # Return None in case of an error

    def duplicateProject(self, original_project_id, client_id):
        """
        Duplicates a project along with its tasks and sprints.
        """

        # 1️⃣ Fetch the original project
        project_query = "SELECT ProjectName, ProjectDescription FROM Projects WHERE ProjectID = ?"
        cursor = self.conn.execute(project_query, (original_project_id,))
        original_project = cursor.fetchone()

        if not original_project:
            print("Error: Original project not found!")
            return None

        original_name, original_description = original_project
        new_project_name = original_name + " (Copy)"

        # 2️⃣ Create the new project
        insert_project_query = """
        INSERT INTO Projects (ProjectName, ProjectDescription, ClientID)
        VALUES (?, ?, ?)
        """
        cursor = self.conn.execute(insert_project_query, (new_project_name, original_description, client_id))
        new_project_id = cursor.lastrowid  # Get the new project ID
        self.conn.commit()
        print(f"Duplicated Project '{new_project_name}' created successfully with ID {new_project_id}")

        # 3️⃣ Duplicate Sprints
        sprint_query = "SELECT SprintID, SprintName, SprintColor FROM Sprints WHERE ProjectID = ?"
        cursor = self.conn.execute(sprint_query, (original_project_id,))
        original_sprints = cursor.fetchall()

        sprint_id_mapping = {}  # Map old sprint IDs to new ones

        for sprint in original_sprints:
            old_sprint_id, sprint_name, sprint_color = sprint
            insert_sprint_query = """
            INSERT INTO Sprints (SprintName, ProjectID, SprintColor)
            VALUES (?, ?, ?)
            """
            cursor = self.conn.execute(insert_sprint_query, (sprint_name, new_project_id, sprint_color))
            new_sprint_id = cursor.lastrowid
            sprint_id_mapping[old_sprint_id] = new_sprint_id  # Store mapping
            self.conn.commit()

        print(f"Duplicated {len(original_sprints)} sprints successfully.")

        # 4️⃣ Duplicate Tasks
        task_query = """
        SELECT TaskID, TaskName, Priority, Status, StatusColor, PriorityColor, Owners, DueDate, Tags, Progress, SprintID
        FROM Tasks WHERE ProjectID = ?
        """
        cursor = self.conn.execute(task_query, (original_project_id,))
        original_tasks = cursor.fetchall()

        for task in original_tasks:
            (task_id, task_name, priority, status, status_color, priority_color, owners,
             due_date, tags, progress, sprint_id) = task

            # Map the sprint ID to the new duplicated sprint
            new_sprint_id = sprint_id_mapping.get(sprint_id, None)

            insert_task_query = """
            INSERT INTO Tasks (TaskName, Priority, Status, StatusColor, PriorityColor, Owners, DueDate, Tags, Progress, ProjectID, SprintID, ClientID)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            self.conn.execute(insert_task_query, (task_name, priority, status, status_color, priority_color, owners,
                                                  due_date, tags, progress, new_project_id, new_sprint_id, client_id))
            self.conn.commit()

        print(f"Duplicated {len(original_tasks)} tasks successfully.")

        return new_project_id

    def addSharedProject(self, owner_id, client_id, project_id):
        try:
            # Check if project exists in Projects table
            check_query = "SELECT COUNT(*) FROM Projects WHERE ProjectID = ?"
            cursor = self.conn.execute(check_query, (project_id,))
            project_exists = cursor.fetchone()[0]

            if project_exists:
                # Insert into SharedProject
                query = """
                INSERT INTO SharedProject (ProjectID, OwnerID, ClientID)
                VALUES (?, ?, ?)
                """
                self.conn.execute(query, (project_id, owner_id, client_id))
                self.conn.commit()
                print(f"Shared entry added for Project {project_id} by Owner {owner_id} for Client {client_id}.")
            else:
                print(f"Error: Project {project_id} does not exist. Cannot create shared entry.")

        except sqlite3.Error as e:
            print(f"Error adding shared project: {e}")

    def deleteProject(self, project_id, client_id):
        try:
            # Delete from Projects table
            query1 = """
            DELETE FROM Projects
            WHERE ProjectID = ? AND ClientID = ?
            """
            self.conn.execute(query1, (project_id, client_id))

            # Delete from SharedProject table for the same project
            query2 = """
            DELETE FROM SharedProject
            WHERE ProjectID = ? AND ClientID = ?
            """
            self.conn.execute(query2, (project_id, client_id))

            self.conn.commit()
            print(f"Project {project_id} deleted for Client {client_id}")
        except sqlite3.Error as e:
            print(f"Error deleting project {project_id}: {e}")

    def reset_autoincrement(self):
        try:
            # Reset AUTOINCREMENT counter for Projects table
            self.conn.execute("DELETE FROM sqlite_sequence WHERE name='Projects'")
            self.conn.commit()
            print("Autoincrement counter for Projects table reset successfully!")
        except sqlite3.Error as e:
            print(f"Error resetting autoincrement: {e}")

    def reset_project_ids(self):
        try:
            # Temporarily disable foreign key checks
            self.conn.execute("PRAGMA foreign_keys = OFF")

            # Create a temporary table with ordered IDs
            temp_query = """
            CREATE TEMPORARY TABLE Projects_temp AS
            SELECT * FROM Projects ORDER BY ProjectID
            """
            self.conn.execute(temp_query)

            # Delete all rows from the original table
            self.conn.execute("DELETE FROM Projects")

            # Insert rows back into the original table with sequential IDs
            reorder_query = """
            INSERT INTO Projects (ProjectID, ProjectName, ProjectDescription, ClientID)
            SELECT ROW_NUMBER() OVER (ORDER BY ProjectID) AS ProjectID,
                   ProjectName, ProjectDescription, ClientID
            FROM Projects_temp
            """
            self.conn.execute(reorder_query)

            # Drop the temporary table
            self.conn.execute("DROP TABLE Projects_temp")

            # Re-enable foreign key checks
            self.conn.execute("PRAGMA foreign_keys = ON")
            self.conn.commit()
            print("Project IDs reset successfully!")
        except sqlite3.Error as e:
            print(f"Error resetting project IDs: {e}")

    def update_project(self, project_id, new_name, new_description, client_id):
        try:
            # Provide default values for empty or blank inputs
            new_name = new_name.strip() if new_name.strip() else "Untitled Project"
            new_description = new_description.strip() if new_description.strip() else "No description provided."

            # Ensure the project exists before updating
            check_query = "SELECT COUNT(*) FROM Projects WHERE ProjectID = ? AND ClientID = ?"
            cursor = self.conn.execute(check_query, (project_id, client_id))
            exists = cursor.fetchone()[0]

            if exists:
                # Update the main project table
                query = """
                UPDATE Projects
                SET ProjectName = ?, ProjectDescription = ?
                WHERE ProjectID = ? AND ClientID = ?
                """
                self.conn.execute(query, (new_name, new_description, project_id, client_id))

                # Ensure the update is reflected in SharedProject
                shared_query = """
                UPDATE SharedProject
                SET OwnerID = ?
                WHERE ProjectID = ?
                """
                self.conn.execute(shared_query, (client_id, project_id))

                self.conn.commit()
                print(
                    f"Project {project_id} updated successfully with Name: '{new_name}' and Description: '{new_description}'")

            else:
                print(f"Project {project_id} does not exist for Client {client_id}. No updates were made.")
        except sqlite3.Error as e:
            print(f"Error updating project {project_id} for Client {client_id}: {e}")

    def allProjects(self, client_id):
        query = """
        SELECT ProjectID, ProjectName, ProjectDescription, ClientID
        FROM Projects
        WHERE ClientID = ?

        UNION

        SELECT p.ProjectID, p.ProjectName, p.ProjectDescription, p.ClientID
        FROM Projects p
        JOIN SharedProject sp ON sp.ProjectID = p.ProjectID
        WHERE sp.ClientID = ?
        """
        # Pass client_id twice since there are two placeholders
        cursor = self.conn.execute(query, (client_id, client_id))
        rows = cursor.fetchall()
        cursor.close()

        owned_projects = []
        shared_projects = []
        for row in rows:
            project = {
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "client_id": row[3]  # This is the owner of the project
            }
            if str(row[3]) == str(client_id):
                owned_projects.append(project)
            else:
                shared_projects.append(project)


        return owned_projects, shared_projects
        # Return a dictionary with separate keys for owned and shared projects
        # return {
        #     "projects": owned_projects,
        #     "shared_projects": shared_projects
        # }

    def closeDb(self):
        self.conn.close()
