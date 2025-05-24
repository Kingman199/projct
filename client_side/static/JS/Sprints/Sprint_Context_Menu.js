/*
                    DELETE SPRINT
Entry:
     - Event: 'DOMContentLoaded' fires when the page fully loads.
     - Parameters: None directly.
         - Contextual Input:
         - Right-click (contextmenu) event on elements with class 'sprint-heading' (captures sprint ID).
         - Left-click anywhere else (hides context menu).
         - User click on custom context menu option (calls deleteSprint function).
Exit:
     - Shows a custom context menu positioned at the mouse click location on sprint headings.
     - On confirmation (via deleteSprint):
         - Sends a DELETE request to '/delete_sprint/{currentSprintId}'.
         - On success:
             - Removes the sprint element from the DOM.
         - On failure:
             - Shows an alert with an error message.
     - On cancel:
         - No action taken (context menu hidden).
         */


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
