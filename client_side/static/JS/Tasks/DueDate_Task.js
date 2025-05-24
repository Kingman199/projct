document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".due-date-cell").forEach(cell => {
    cell.addEventListener("click", () => {
      if (cell.querySelector("input")) return;

      const current = cell.textContent.trim();
      const taskId = cell.dataset.id;
      const sprintId = cell.dataset.sprint;

      cell.textContent = '';
      const input = document.createElement("input");
      input.type = "text";
      input.value = current;
      cell.appendChild(input);

      const fp = flatpickr(input, {
        locale: "he", // Hebrew
        altInput: true,
        altFormat: "j F Y",    // Displayed format
        dateFormat: "d/m/Y",   // Backend format
        defaultDate: (current && current.toLowerCase() !== "none") ? current : null,
        onClose: function (selectedDates, dateStr) {
          // If no change, restore and skip update
          if (dateStr === current) {
            cell.textContent = current;
          } else {
            cell.textContent = dateStr;
            console.log("Updating task with:", { taskId, sprintId, dateStr });
            updateTask(sprintId, taskId, { DueDate: dateStr });
          }

          fp.destroy(); // Call destroy from this scope
        }
      });

      fp.open();
    });
  });
});
