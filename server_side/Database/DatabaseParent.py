from Database.DatabaseClients import DatabaseClients
from Database.DatabaseProjects import DatabaseProjects
from Database.DatabaseTasks import DatabaseTasks
import sqlite3

class DatabaseParent:
    def __init__(self):
        conn = sqlite3.connect('wowdatabase.db')
        self.tables = {
            "clients": DatabaseClients(conn),
            "projects": DatabaseProjects(conn),
            "tasks": DatabaseTasks(conn)
        }

    # region --- Clients ---
    def login(self, username, password):
        client_table = self.tables["clients"]
        ok, client_id, role = client_table.loginClient(username, password)

        return ok, client_id, role
    # endregion

    def read_list_by_ID(self, client_id, project_id, name=None):
        if name == "sprints":
            list_ = self.tables["tasks"].sprint_tasks(project_id, client_id)
            return list_

        elif name == "comments":
            task_id = project_id
            return self.tables["tasks"].get_comments(task_id)

    def addTask(self, client_id, project_id, sprint_id, task_id, name):
        self.tables["tasks"].add_empty_item(project_id, sprint_id, client_id, name)

    def delete(self, subject, ids):
        if "projects" in subject:
            self.tables["projects"].deleteProject(ids[1], ids[0])
        if "tasks" in subject:
            self.tables["tasks"].delete_task(ids)

