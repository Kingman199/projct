// AFK_Time.js
document.addEventListener("DOMContentLoaded", () => {
    /* ───── CONFIG ───── */
    const maxIdleMinutes     = 5;   // log-out after this many idle minutes
    const warningTimeMinutes = 2;   // show warning modal after this many idle minutes
    const PING_INTERVAL_MS   = 60_000; // min gap between /reset_timer pings  (1 min)

    /* ───── ELEMENTS ───── */
    const modal        = document.getElementById("idleTimeoutModal");
    const stayLoggedIn = document.getElementById("stayLoggedInBtn");
    const logoutBtn    = document.getElementById("logoutBtn");
    if (!modal || !stayLoggedIn || !logoutBtn) {
        console.error("Idle-timeout DOM elements missing");
        return;
    }

    /* ───── TIMERS ───── */
    let warnTimerId   = null;
    let logoutTimerId = null;
    const warnDelay   = warningTimeMinutes * 60_000;
    const logoutDelay = maxIdleMinutes     * 60_000;

    const clearTimers = () => {
        clearTimeout(warnTimerId);
        clearTimeout(logoutTimerId);
    };

    const startTimers = () => {
        warnTimerId   = setTimeout(showWarning, warnDelay);
        logoutTimerId = setTimeout(forceLogout, logoutDelay);
    };

    /* ───── KEEP-ALIVE ───── */
    let lastPing = 0;
    const maybePingServer = () => {
        const now = Date.now();
        if (now - lastPing > PING_INTERVAL_MS) {
            fetch("/reset_timer", { method: "POST" }).catch(err =>
                console.warn("Session ping failed:", err)
            );
            lastPing = now;
        }
    };

    /* ───── HANDLERS ───── */
    const showWarning = () => modal.classList.replace("hidden", "visible");
    const hideWarning = () => modal.classList.replace("visible", "hidden");
    const forceLogout = () => window.location.href = "/logout";

    const resetIdle = () => {
        hideWarning();
        maybePingServer();   // throttle keep-alive
        clearTimers();
        startTimers();
    };

    /* ───── ACTIVITY EVENTS ───── */
    ["mousemove", "keydown", "click", "scroll", "touchstart"].forEach(evt =>
        document.addEventListener(evt, resetIdle, { passive: true })
    );

    /* ───── BUTTONS ───── */
    stayLoggedIn.addEventListener("click", resetIdle);
    logoutBtn.addEventListener("click", forceLogout);

    /* ───── ARM EVERYTHING ───── */
    startTimers();
});