document.addEventListener('mousedown', function(event) {
    if (event.button === 0) {  // 0 is the left mouse button
        event.preventDefault();
    }
});