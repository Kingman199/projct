document.addEventListener("DOMContentLoaded", () => {
    let idleTime = 0;
    const maxIdleMinutes = 5;
    const warningTimeMinutes = 2;

    const modal = document.getElementById("idleTimeoutModal");
    const stayLoggedInBtn = document.getElementById("stayLoggedInBtn");
    const logoutBtn = document.getElementById("logoutBtn");

    if (!modal || !stayLoggedInBtn || !logoutBtn) {
        console.error("Idle modal elements not found.");
        return;
    }

    const maxIdle = maxIdleMinutes * 60 * 1000; // ms
    const warningTime = warningTimeMinutes * 60 * 1000; // ms
    let lastActivity = Date.now();

    function showModal() {
        modal.classList.remove("hidden");
        modal.classList.add("visible");
    }

    function hideModal() {
        modal.classList.remove("visible");
        modal.classList.add("hidden");
    }

    function resetIdleTimer() {
        lastActivity = Date.now();
        hideModal();
    }

    function pingServer() {
        fetch("/reset_timer", { method: "POST" }).catch(err =>
            console.warn("Session ping failed:", err)
        );
    }

    function checkIdle() {
        const now = Date.now();
        const idleDuration = now - lastActivity;

        if (idleDuration >= maxIdle) {
            window.location.href = "/logout";
        } else if (idleDuration >= warningTime) {
            showModal();
        } else {
            hideModal();
        }
    }

    setInterval(checkIdle, 10000); // Check every 10 seconds

    ["mousemove", "keydown", "click", "scroll"].forEach(evt =>
        document.addEventListener(evt, () => {
            resetIdleTimer();
            pingServer();
        })
    );

    stayLoggedInBtn.addEventListener("click", () => {
        resetIdleTimer();
        pingServer();
    });

    logoutBtn.addEventListener("click", () => {
        window.location.href = "/logout";
    });
});
