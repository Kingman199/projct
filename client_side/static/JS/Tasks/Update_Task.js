document.addEventListener("DOMContentLoaded", function () {
    let debounceTimer;

    // ---------------------- REAL-TIME TASK NAME UPDATE ---------------------- \\
    document.querySelectorAll(".task-name-cell").forEach(cell => {
        const input = cell.querySelector(".edit-input");
        const displayText = cell.querySelector(".display-text");

        displayText.addEventListener("click", function () {
            displayText.style.display = "none";
            input.style.display = "block";
            input.value = displayText.textContent.trim();
            input.focus();
        });

        input.addEventListener("focus", function () {
            input.dataset.active = "true";
        });

        input.addEventListener("blur", function () {
            input.dataset.active = "false";
            setTimeout(() => {
                if (input.dataset.active === "false") {
                    input.style.display = "none";
                    displayText.textContent = input.value.trim() || "Untitled Task";
                    displayText.style.display = "inline";
                }
            }, 100);
        });

        input.addEventListener("keydown", function (event) {
            if (event.key === "Enter") {
                const taskRow = this.closest(".task-row");
                const taskId = taskRow.id.replace("task-", "");
                const sprintId = taskRow.closest("tbody").id.replace("taskBody-", "");
                const newTaskName = this.value.trim();
                if (newTaskName) {
                    updateTask(sprintId, taskId, { TaskName: newTaskName });
                }
                this.style.display = "none";
                displayText.textContent = newTaskName || "Untitled Task";
                displayText.style.display = "inline";
            }
        });

        input.addEventListener("input", function () {
            clearTimeout(debounceTimer);
            const taskRow = this.closest(".task-row");
            const taskId = taskRow.id.replace("task-", "");
            const sprintId = taskRow.closest("tbody").id.replace("taskBody-", "");
            const newTaskName = this.value.trim();
            if (newTaskName) {
                debounceTimer = setTimeout(() => {
                    updateTask(sprintId, taskId, { TaskName: newTaskName });
                }, 500);
            }
        });
    });

    document.addEventListener("click", function (event) {
        document.querySelectorAll(".edit-input").forEach(input => {
            if (!input.contains(event.target) && !input.closest(".task-name-cell").contains(event.target)) {
                input.style.display = "none";
                const displayText = input.closest(".task-name-cell").querySelector(".display-text");
                displayText.textContent = input.value.trim() || "Untitled Task";
                displayText.style.display = "inline";
            }
        });
    });

    // ---------------------- DROP MENU FUNCTIONALITY ---------------------- \\
    document.querySelectorAll('.dropdown-Status, .dropdown-Priority').forEach(element => {
        element.addEventListener('click', function (event) {
            event.stopPropagation();
            const field = this.dataset.field;
            const taskId = this.dataset.id;
            const menu = document.getElementById(`dropdown-${field}`);

            document.querySelectorAll('.dropdown-menu').forEach(otherMenu => {
                if (otherMenu !== menu) {
                    otherMenu.classList.remove('show');
                    otherMenu.classList.add('hide');
                }
            });

            menu.classList.toggle('show');
            menu.classList.toggle('hide');

            const rect = this.getBoundingClientRect();
            menu.style.left = `${rect.left}px`;
            menu.style.top = `${rect.bottom + window.scrollY}px`;
            menu.setAttribute('data-task-id', taskId);
        });
    });

    document.addEventListener('click', function (event) {
        document.querySelectorAll('.dropdown-menu').forEach(menu => {
            if (!menu.contains(event.target)) {
                menu.classList.remove('show');
                menu.classList.add('hide');
            }
        });
    });

    // ---------------------- HANDLE DROPDOWN OPTION SELECTION ---------------------- \\
    document.querySelectorAll('.dropdown-menu div').forEach(option => {
        option.addEventListener('click', function () {
            const menu = this.parentElement;
            const field = menu.id.replace('dropdown-', '');
            const selectedValue = this.getAttribute('data-value');
            const taskId = menu.getAttribute('data-task-id');
            const element = document.querySelector(`[data-field="${field}"][data-id="${taskId}"]`);
            const sprintId = element.closest("tbody").id.replace("taskBody-", "");

            if (selectedValue === "Custom") {
                currentCustomField = field;
                currentTaskElement = element;
                currentTaskId = taskId;
                currentSprintId = sprintId;
                openCustomLabelModal(field);
            } else {
                updateField(sprintId, taskId, field, selectedValue, element);
            }
        });
    });
});

// ---------------------- GLOBAL VARIABLES ---------------------- \\
var currentCustomField = null;
var currentTaskElement = null;
var currentSprintId = null;
var currentTaskId = null;

// ---------------------- FUNCTION TO UPDATE STATUS OR PRIORITY ---------------------- \\
function updateField(sprintId, taskId, field, value, element) {
    const STATUS_COLORS = {
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
        "": "#d1d5db"
    };

    const PRIORITY_COLORS = {
        "Critical": "#f87171",
        "High": "#facc15",
        "Medium": "#bfdbfe",
        "Low": "#d1fae5",
        "Best Effort": "#e5e7eb",
        "Missing": "#9ca3af"
    };

    const customColors = JSON.parse(localStorage.getItem("customColors")) || {};

    let colors = field === "Priority" ? PRIORITY_COLORS : STATUS_COLORS;
    let newColor = colors[value] || customColors[value];

    if (!newColor) {
        newColor = generateRandomPastelColor();
        customColors[value] = newColor;
        localStorage.setItem("customColors", JSON.stringify(customColors));
    }

    element.style.backgroundColor = newColor;
    element.style.color = "#333";
    element.innerText = value;

    updateTask(sprintId, taskId, { [field]: value, [`${field}Color`]: newColor });

    document.querySelectorAll('.dropdown-menu').forEach(menu => {
        menu.classList.remove('show');
        menu.classList.add('hide');
    });
}

// ---------------------- RANDOM PASTEL COLOR ---------------------- \\
function generateRandomPastelColor() {
    const hue = Math.floor(Math.random() * 360);
    return `hsl(${hue}, 80%, 85%)`;
}

// ---------------------- BACKEND UPDATE FUNCTION ---------------------- \\
export async function updateTask(sprintId, taskId, updateData) {
    updateData["ID"] = taskId;
    updateData["SprintID"] = sprintId;
    updateData["project_id"] = document.body.getAttribute('data-project-id');

    console.log("Calling updateTask with:", {
      taskId,
      sprintId,
      projectId: document.body.getAttribute('data-project-id'),
      updateData
    });


    try {
        const response = await fetch("/update_task", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(updateData)
        });
        const result = await response.json();

        if (result.status === "success") {
            console.log("Task updated:", result.updated_task);
            const updatedTask = result.updated_task;
            const field = Object.keys(updateData).find(k => k !== "ID" && k !== "SprintID" && k !== "project_id");
            const element = document.querySelector(`[data-field="${field}"][data-id="${taskId}"]`);
            if (element) {
                const colorKey = `${field}Color`;
                const newColor = updatedTask[colorKey] || "#d1d5db";
                element.style.backgroundColor = newColor;
                element.style.color = "#333";
            }
        } else {
            console.error("Failed to update task:", result.message);
        }
    } catch (error) {
        console.error("Error updating task:", error);
    }
}

// ---------------------- CUSTOM LABEL MODAL ---------------------- \\
function openCustomLabelModal(field) {
    currentCustomField = field;
    document.getElementById("customField").innerText = field;
    document.getElementById("customLabelName").value = "";
    document.getElementById("customLabelColor").value = "#d1d5db";
    document.getElementById("customLabelModal").classList.remove("hide");
    document.getElementById("customLabelModal").classList.add("show");
}

function closeCustomLabelModal() {
    document.getElementById("customLabelModal").classList.remove("show");
    document.getElementById("customLabelModal").classList.add("hide");
}

function saveCustomLabel() {
    const labelName = document.getElementById("customLabelName").value.trim();
    const labelColor = document.getElementById("customLabelColor").value;
    if (!labelName) {
        alert("Please enter a label name.");
        return;
    }
    if (currentTaskElement) {
        currentTaskElement.style.backgroundColor = labelColor;
        currentTaskElement.innerText = labelName;
        updateTask(currentSprintId, currentTaskId, { [currentCustomField]: labelName, [`${currentCustomField}Color`]: labelColor });
    }
    closeCustomLabelModal();
}
