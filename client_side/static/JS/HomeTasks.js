
// ------------ New Task (Section) -------------
document.getElementById('addTaskButton').addEventListener('click', function () {
  const spinner = document.getElementById('loading-spinner');
  spinner.style.display = 'block';

  fetch('/add_task', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      TaskName: 'New Task',
      Status: 'Ready to Start',
      Priority: 'Medium',
      Owners: '',
      DueDate: '',
      Tags: '',
    }),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error('Failed to add task');
      }
      return response.json();
    })
    .then((data) => {
      if (data.status !== 'success') {
        throw new Error('Failed to add the task');
      }

      spinner.style.display = 'none';

      const newTask = data.newTask;

      // Add the new task row to the table
      const taskRow = document.createElement('tr');
      taskRow.classList.add('task-row');
      taskRow.id = `task-${newTask.TaskID}`;
      taskRow.setAttribute('draggable', 'true'); // Make it draggable
      taskRow.addEventListener('dragstart', dragStart); // Add drag start listener
      taskRow.addEventListener('dragover', dragOver);   // Add drag over listener
      taskRow.addEventListener('drop', dropTask);       // Add drop listener

      taskRow.innerHTML = `
        <td>${newTask.TaskID}</td>
        <td contenteditable="true" onblur="updateTaskName(${newTask.TaskID}, this.innerText)">
          ${newTask.TaskName}
        </td>
        <td style="background-color: ${newTask.StatusColor}" onclick="toggleStatusDropdown(event)">
          ${newTask.Status}
        </td>
        <td style="background-color: ${newTask.PriorityColor}">
          ${newTask.Priority}
        </td>
        <td>${newTask.Owners}</td>
        <td>${newTask.DueDate}</td>
        <td>${newTask.Tags}</td>
        <td>
          <div class="progress-bar">
            <div class="progress" style="width: ${newTask.Progress}%;"></div>
          </div>
          ${newTask.Progress}%
        </td>
        <td><button class="delete-button" onclick="openDeleteModal(${newTask.TaskID})">Delete</button></td>
      `;

      document.getElementById('taskBody').appendChild(taskRow);
    })
//    .catch((error) => {
//      console.error('Error:', error);
//      alert('Failed to add the task. Please try again.');
//      spinner.style.display = 'none';
//    });
});


// -------------------------  Draggable  -----------------
let draggedTask = null;

// Triggered when dragging starts
function dragStart(event) {
  draggedTask = event.target; // The row being dragged
  event.dataTransfer.effectAllowed = 'move';
  event.dataTransfer.setData('text/plain', draggedTask.id);
}

// Triggered when dragging over another row
function dragOver(event) {
  event.preventDefault(); // Allow dropping
  event.dataTransfer.dropEffect = 'move';
}

// Triggered when a row is dropped
function dropTask(event) {
  event.preventDefault();
  const targetTask = event.target.closest('tr'); // The row being dropped onto
  if (!targetTask || draggedTask === targetTask) return; // Skip if dropping on itself

  // Swap rows visually
  const taskBody = document.getElementById('taskBody');
  if (targetTask.rowIndex < draggedTask.rowIndex) {
    taskBody.insertBefore(draggedTask, targetTask);
  } else {
    taskBody.insertBefore(draggedTask, targetTask.nextSibling);
  }

  // Update the TaskIDs on the backend
  updateTaskPositions(draggedTask.id.split('-')[1], targetTask.id.split('-')[1]);
}

// Update the task positions via API
function updateTaskPositions(draggedTaskID, targetTaskID) {
  fetch('/update_task_positions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      draggedTaskID,
      targetTaskID,
    }),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error('Failed to update task positions');
      }
      return response.json();
    })
    .then((data) => {
      console.log('Task positions updated successfully:', data);
    })
    .catch((error) => {
      console.error('Error updating task positions:', error);
    });
}



// --------------------------------------  DELETE  --------------------------------------
let taskToDelete = null; // To store the task ID temporarily

function openDeleteModal(taskId) {

  taskToDelete = taskId; // Store the task ID
  const modal = document.getElementById("deleteModal");
  modal.style.display = "block";
}

function closeDeleteModal() {
  taskToDelete = null; // Clear the stored task ID
  const modal = document.getElementById("deleteModal");
  modal.style.display = "none";
}

function confirmDelete() {
  if (!taskToDelete)
  {
    alert("Task ID is missing");
    return;
  }

  fetch("/delete_task", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ task_id: taskToDelete }), // Ensure task_id is passed
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.status === "success") {
        location.reload(); // Reload the page or dynamically remove the task row
      }
    })
//    .catch((error) => {
//      console.error("Error:", error);
//      alert("An error occurred. Please try again.");
//    })
    .finally(() => {
      closeDeleteModal();
    });
}

// --------------------------------------
//   ------------------------------ edit task -
  let originalContent = ""; // To store the original task name before editing
  const editHistory = new Map(); // To store task edit history for undo functionality

  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("td[contenteditable='true']").forEach(cell => {
      // Save original content when the cell is focused
      cell.addEventListener("focus", () => {
        originalContent = cell.innerText;
      });

      // Cancel editing on Esc key
      cell.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
          cell.innerText = originalContent; // Revert to original content
          cell.blur(); // Remove focus from the cell
        }
      });

      // Save changes on blur and trigger feedback effect
      cell.addEventListener("blur", () => {
        const taskID = cell.getAttribute("data-task-id");
        const newContent = cell.innerText.trim();

        if (newContent !== originalContent) {
          // Update task on the server
          updateTaskName(taskID, newContent);

          // Save to history for undo functionality
          if (!editHistory.has(taskID)) {
            editHistory.set(taskID, [originalContent]); // Initialize history
          }
          editHistory.get(taskID).push(newContent);

          // Trigger feedback effect
          showFeedbackEffect(cell, "success");
        } else {
          showFeedbackEffect(cell, "neutral");
        }
      });
    });
  });

  // Undo functionality (Ctrl+Z)
  document.addEventListener("keydown", (event) => {
    if (event.ctrlKey && event.key === "z") {
      const focusedCell = document.activeElement;
      if (focusedCell && focusedCell.getAttribute("contenteditable") === "true") {
        const taskID = focusedCell.getAttribute("data-task-id");
        const history = editHistory.get(taskID);

        if (history && history.length > 1) {
          history.pop(); // Remove the latest change
          const lastValue = history[history.length - 1];
          focusedCell.innerText = lastValue;

          // Optionally, update the server with the reverted change
          updateTaskName(taskID, lastValue);

          // Trigger feedback effect for undo
          showFeedbackEffect(focusedCell, "undo");
        }
      }
    }
  });

  // Function to show feedback effect
  function showFeedbackEffect(cell, effectType) {
    if (effectType === "success") {
      cell.style.backgroundColor = "#d4edda"; // Light green for success
      setTimeout(() => (cell.style.backgroundColor = ""), 1000); // Reset after 1s
    } else if (effectType === "undo") {
      cell.style.backgroundColor = "#fff3cd"; // Light yellow for undo
      setTimeout(() => (cell.style.backgroundColor = ""), 1000); // Reset after 1s
    } else if (effectType === "neutral") {
      cell.style.backgroundColor = "#e2e3e5"; // Light gray for no changes
      setTimeout(() => (cell.style.backgroundColor = ""), 500); // Reset after 0.5s
    }
  }

  // Function to send updated task name to the server
  function updateTaskName(taskID, newTaskName) {
    fetch('/update_task', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        ID: taskID,
        TaskName: newTaskName.trim(),
      }),
    })
    .then((response) => response.json())
    .then((data) => {
      if (data.status === 'success') {
        console.log('Task updated successfully:', data.updated_task);
      } else {
        //
      }
    })
//    .catch((error) => {
//      console.error('Error updating task:', error);
//      alert('Error updating task. Please try again.');
//    });
  }
    //

// ----------------------  DROP MENU ---------------------- \\


   let activeMenu = null;

document.querySelectorAll('.dropdown-Status, .dropdown-Priority').forEach(element => {
  element.addEventListener('click', function (event) {
    event.stopPropagation();

    // Ensure only the corresponding dropdown opens
    const field = this.dataset.field;
    const menu = document.getElementById(`dropdown-${field}`);

    // Positioning logic
    const rect = this.getBoundingClientRect();
    menu.style.left = `${rect.left}px`;
    menu.style.top = `${rect.bottom + window.scrollY}px`;
    menu.style.display = 'block';

    // Update active menu reference
    activeMenu = menu;

    menu.querySelectorAll('div').forEach(option => {
      option.onclick = (e) => {
        e.stopPropagation();
        updateField(this.dataset.id, field, option.dataset.value, this);
      };
    });
  });
});


// Close menu on outside click
window.addEventListener('click', () => {
  if (activeMenu) {
    activeMenu.style.display = 'none';
    activeMenu = null;
  }
});

function updateField(id, field, value, element) {
  const statusColors = {
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
  };

  // Update UI dynamically
  const newColor = statusColors[value] || "#d1d5db";
  element.style.backgroundColor = newColor;
  element.innerText = value;


  // Send update request
  fetch("/update_task", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      ID: parseInt(id),
      [field]: value,
      BC: newColor
    }),
  })
    .then(response => response.json())
    .then(data => {
      if (data.status === "success") {
        console.log("Task updated successfully", data.changes);
      } else {
        console.error("Error updating task:", data.message);
      }
    });
}



const spinner = document.querySelector('.loading-spinner');
function toggleSpinner(show) {
  spinner.style.display = show ? 'block' : 'none';
}

// ------
  document.querySelector('.sidebar-toggle').addEventListener('click', () => {
  document.querySelector('.sidebar').classList.toggle('collapsed');
});
