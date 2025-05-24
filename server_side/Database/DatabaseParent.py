from Database.DatabaseClients import DatabaseClients
from Database.DatabaseProjects import DatabaseProjects
from Database.DatabaseListToDo import DatabaseListToDo
from Database.DatabaseTasks import DatabaseTasks
import sqlite3

class DatabaseParent:
    def __init__(self):
        conn = sqlite3.connect('wowdatabase.db')
        self.tables = {
            "clients": DatabaseClients(conn),
            "projects": DatabaseProjects(conn),
            "listToDo": DatabaseListToDo(conn),
            "tasks": DatabaseTasks(conn)
            # "client_project_tasks": DatabaseClientProjectTasks(conn)  # Add new table here
        }

        # self.STATUS_COLORS = {
        #     "Ready to Start": "#d0ebff",
        #     "In Progress": "#facc15",
        #     "Waiting for Review": "#cfe2ff",
        #     "Updating": "#dbeafe",
        #     "Pending Deploy": "#e8e4d3",
        #     "Done": "#d1fae5",
        #     "Future Plan": "#baf5e0",
        #     "Working On It": "#e9d5ff",
        #     "Stuck": "#fca5a5",
        #     "In Tests": "#d9f99d",
        #     "": "#d1d5db",
        # }
        #
        # self.PRIORITY_COLORS = {
        #     "Critical": "#f87171",
        #     "High": "#facc15",
        #     "Medium": "#bfdbfe",
        #     "Low": "#d1fae5",
        #     "Best Effort": "#e5e7eb",
        #     "Missing": "#9ca3af",
        # }

    # region --- Clients ---
    def login(self, username, password):
        client_table = self.tables["clients"]
        # cpt_table = self.tables["client_project_tasks"]
        # projects_table = self.tables["projects"]
        # Attempt to log in the client
        ok, client_id, role = client_table.loginClient(username, password)

        return ok, client_id, role
    # endregion


    def read_list_by_ID(self, client_id, project_id, name=None):
        if name == "sprints":
            list_ = self.tables["tasks"].sprint_tasks(project_id, client_id)
            if list_:
                return list_
            else:
                # Means it's empty
                self.tables["tasks"].add_sprint("_", project_id)
                list_ = self.tables["tasks"].sprint_tasks(project_id, client_id)
                if list_:
                    return list_

        elif name == "projects":
            return self.tables["client_project_tasks"].get_projects_by_client(client_id)
        elif name == "comments":
            task_id = project_id
            return self.tables["tasks"].get_comments(task_id)
        else:
            list_ = self.tables[name].read_list(project_id)
            if list_:
                return list_
            else:
                # Means it's empty
                self.tables[name].add_empty_item(client_id, project_id, "New Task")
                list_ = self.tables[name].read_list(project_id)
                if list_:
                    return list_


    def read_list(self, name):
        return self.tables[name].read_list()

    def addTask(self, client_id, project_id, sprint_id, task_id, name):
        # self.tables["client_project_tasks"].update(client_id, project_id, task_id)
        self.tables["tasks"].add_empty_item(project_id, sprint_id, client_id, name)

    def delete(self, subject, ids):
        if "projects" in subject:
            self.tables["projects"].deleteProject(ids[1], ids[0])
            # self.tables["client_project_tasks"].delete_project(ids[1], ids[0])
        if "tasks" in subject:
            self.tables["tasks"].delete_task(ids)
            # self.tables["client_project_tasks"].delete_task(ids[2], ids[1], ids[0])

