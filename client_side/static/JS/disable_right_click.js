document.addEventListener("contextmenu", (event) => event.preventDefault()); // Disable right-click
document.addEventListener("mousedown", (event) => {
  if (event.button === 1) { // 0 = Left Click
    event.preventDefault();
  }
});