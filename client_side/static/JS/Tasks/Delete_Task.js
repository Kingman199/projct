document.addEventListener('DOMContentLoaded', () => {
  const sprintContextMenu = document.getElementById('sprintContextMenu');
  let currentSprintId = null;

  // Add right-click handler to sprint headings
  document.querySelectorAll('.sprint-heading').forEach(sprintHeader => {
    sprintHeader.addEventListener('contextmenu', (e) => {
      e.preventDefault();
      currentSprintId = sprintHeader.id.split('-')[1]; // Extract Sprint ID

      // Position the context menu at mouse position
      sprintContextMenu.style.left = `${e.clientX}px`;
      sprintContextMenu.style.top = `${e.clientY}px`;
      sprintContextMenu.style.display = 'block';
    });
  });

  // Hide the context menu when clicking elsewhere
  document.addEventListener('click', () => {
    sprintContextMenu.style.display = 'none';
  });

  // Define deleteSprint function
  window.deleteSprint = () => {
    if (confirm(`Are you sure you want to delete sprint ${currentSprintId}?`)) {
      // Replace with actual delete logic (e.g., API call or modal)
      console.log(`Deleting sprint: ${currentSprintId}`);
      // Example AJAX:
      fetch(`/delete_sprint/${currentSprintId}`, {
          method: 'DELETE',
        })
          .then(res => res.json())
          .then(data => {
            if (data.success) {
              // Remove the sprint DOM element
              const sprintContainer = document.getElementById(`sprint-${data.deletedSprintId}`);
              if (sprintContainer) {
                sprintContainer.parentElement.remove(); // removes the whole sprint block
              }
            } else {
              alert(data.message || 'Failed to delete sprint.');
            }
          })
          .catch(err => {
            console.error('Delete error:', err);
            alert('An error occurred while deleting the sprint.');
          });
    }
  };
});




        // --- Task Deleted ---
        socket.on("delete_task", (data) => {
            console.log("🗑️ Task deleted:", data.task_id);

            const { task_id, deleted_by, sprint_name } = data;
            const taskRow = document.getElementById(`task-${task_id}`);
            let visualTaskNumber = "?";

            if (taskRow) {
                const sprintID = taskRow.closest("tbody")?.id.replace("taskBody-", "");
                if (sprintID) {
                    visualTaskNumber = getVisualTaskNumber(task_id, sprintID);
                }
                taskRow.remove();
            }

            showActionPopup(`${deleted_by} deleted Task #${visualTaskNumber} in ${sprint_name}`);
        });
