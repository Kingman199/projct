    export function handleTaskInputClick(event) {
        const sprintId = event.target.dataset.sprintId;
        if (event.target.value.trim() === '') {
            event.target.value = "New Task";
            addTask({ key: 'Enter', target: event.target }, sprintId);
        }
    }

    export async function addTask(event, sprintId) {
        if (event.key === 'Enter' && event.target.value.trim() !== '') {
            const taskName = event.target.value.trim();
            const inputField = event.target;

            const newTask = {
                TaskName: taskName,
                Status: "Ready to start",
                Priority: "Medium",
                Owners: "Unassigned",
                DueDate: "--",
                Tags: "--",
                SprintID: sprintId
            };

            try {
                const response = await fetch("/add_task", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(newTask)
                });

                const result = await response.json();
                if (result.status === "success") {
                    const task = result.newTask;

                    const newRow = document.createElement("tr");
                    newRow.classList.add("task-row");
                    newRow.id = `task-${task.TaskID}`;
                    newRow.innerHTML = `
                        <td><input type="checkbox" class="task-checkbox"></td>
                        <td class="task-name-cell" data-task-id="${task.TaskID}">
                            <div class="task-name-content">
                                <span class="display-text">${task.TaskName}</span>
                                <input type="text" class="edit-input">
                            </div>
                            <span class="comment-icon">💬</span>
                        </td>
                        <td class="dropdown-Status" data-field="Status" style="background-color: ${task.StatusColor}"
                            data-id="${task.TaskID}" onclick="toggleStatusDropdown(event)">
                            ${task.Status}
                        </td>
                        <td class="dropdown-Priority" data-field="Priority" style="background-color: ${task.PriorityColor}"
                            data-id="${task.TaskID}">
                            ${task.Priority}
                        </td>
                        <td>${task.Owners}</td>
                        <td>${task.DueDate}</td>
                        <td>${task.Tags}</td>
                        <td>
                            <div class="progress-bar">
                                <div class="progress" style="width: ${task.Progress}%;"></div>
                            </div>
                            ${task.Progress}%
                        </td>
                    `;

                    const taskBody = document.getElementById(`taskBody-${sprintId}`);
                    const addRow = document.getElementById(`add-task-row-${sprintId}`);
                    if (taskBody && addRow) {
                        taskBody.insertBefore(newRow, addRow);
                    } else {
                        console.error("Task body or add-task row not found for sprint:", sprintId);
                    }

                    inputField.value = "";
                    window.location.reload(); // Optional: Remove to avoid full refresh
                }
            } catch (error) {
                console.error("Error adding task:", error);
            }
        }
    }

    // Attach all input listeners dynamically
    export function attachTaskInputListeners() {
        document.querySelectorAll('.task-input').forEach(input => {
            input.addEventListener('click', handleTaskInputClick);
            input.addEventListener('keypress', (event) => {
                const sprintId = event.target.dataset.sprintId;
                addTask(event, sprintId);
            });
        });
    }
/*
                        ADD TASK
Entry:
     - Functions:
       - handleTaskInputClick(event, sprintId):
         - Triggered when clicking on a task input field.
         - Parameters:
           - event: Click event object.
           - sprintId (string or number): ID of the sprint the task belongs to.
         - If input is empty, sets default task name ("New Task") and simulates an 'Enter' key press to trigger addTask().
       - addTask(event, sprintId):
         - Triggered when pressing 'Enter' inside the task input field.
         - Parameters:
           - event: Keypress event object.
           - sprintId (string or number): ID of the sprint where the new task should be added.
         - Sends POST request to '/add_task' with a new task's default data.
         - Awaits server response containing the newly created task data.
Exit:
     - On successful task addition:
     - Dynamically creates a new <tr> (task row) in the corresponding sprint's task table.
     - Fills in task fields: Name, Status, Priority, Owners, Due Date, Tags, Progress.
     - Reloads the page after adding the task.
     - On failure (API error or fetch error):
       - Logs an error to the console.
     - On clicking outside or empty input:
       - If empty, auto-fills with "New Task" and auto-adds.
*/



    // Real-time socket handler
    export function setupSocketTaskListener(socket) {
        socket.on("task_added", (data) => {
            console.log("➕ New Task added:", data.new_task);

            const { new_task, added_by, sprintID, sprint_name } = data;

            const newRow = document.createElement("tr");
            newRow.classList.add("task-row");
            newRow.id = `task-${new_task.TaskID}`;
            newRow.innerHTML = `
                <td><input type="checkbox" class="task-checkbox"></td>
                <td class="task-name-cell" data-task-id="${new_task.TaskID}">
                    <div class="task-name-content">
                        <span class="display-text">${new_task.TaskName}</span>
                        <input type="text" class="edit-input">
                    </div>
                    <span class="comment-icon">💬</span>
                </td>
                <td class="dropdown-Status" data-field="Status" style="background-color: ${new_task.StatusColor}"
                    data-id="${new_task.TaskID}" onclick="toggleStatusDropdown(event)">
                    ${new_task.Status}
                </td>
                <td class="dropdown-Priority" data-field="Priority" style="background-color: ${new_task.PriorityColor}"
                    data-id="${new_task.TaskID}">
                    ${new_task.Priority}
                </td>
                <td>${new_task.Owners}</td>
                <td>${new_task.DueDate}</td>
                <td>${new_task.Tags}</td>
                <td>
                    <div class="progress-bar">
                        <div class="progress" style="width: ${new_task.Progress}%;"></div>
                    </div>
                    ${new_task.Progress}%
                </td>
            `;

            const taskBody = document.getElementById(`taskBody-${sprintID}`);
            const addRow = document.getElementById(`add-task-row-${sprintID}`);
            if (taskBody && addRow) {
                taskBody.insertBefore(newRow, addRow);
            } else {
                console.error("Task body or add-task row not found for sprint:", sprintID);
            }

            showActionPopup(`${added_by} added Task "${new_task.TaskName}" in ${sprint_name}`);
        });
    }
