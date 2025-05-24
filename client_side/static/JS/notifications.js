// 📌 notifications.js
import socket from "./static/JS/socket.js";

var client_id = "{{ session.get('client_id', '') }}"; // Injected from Flask

if (!client_id) {
    console.error("⚠️ Client ID is missing. WebSocket connection may not work.");
}

// Toggle the notification dropdown
function toggleNotifications() {
    document.getElementById("notification-dropdown")?.classList.toggle("show");
}

// Add a new notification
function addNotification(message, senderId, senderName) {
    let dropdown = document.getElementById("notification-dropdown");

    if (!dropdown) {
        console.error("❌ Notification dropdown not found.");
        return;
    }

    if (document.getElementById(`notification-${senderId}`)) return; // Prevent duplicates

    senderName = senderName || "Unknown User"; // Fallback name

    let notificationHtml = `
        <p id="notification-${senderId}">
            Friend request from <strong>${senderName}</strong>
            <button onclick="respondRequest('${senderId}', 'accepted')">Accept</button>
            <button onclick="respondRequest('${senderId}', 'denied')">Decline</button>
        </p>
    `;

    dropdown.innerHTML += notificationHtml;
    updateBadge();
}

// Update the notification badge count
function updateBadge() {
    const badge = document.getElementById("notification-badge");
    if (!badge) return;

    const count = document.querySelectorAll("#notification-dropdown p").length;
    badge.textContent = count;
    badge.style.display = count > 0 ? "block" : "none";
}

// WebSocket Event for Friend Requests
socket.on("friend_request_" + client_id, function(data) {
    if (!data || !data.sender_id || !data.sender_username) {
        console.error("❌ Invalid friend request data:", data);
        return;
    }

    addNotification(`Friend request from ${data.sender_username}`, data.sender_id, data.sender_username);
});

// Respond to a friend request
function respondRequest(senderId, status) {
    fetch("/accept_friend_request", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sender_id: senderId, status: status })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById("notification-" + senderId)?.remove();
            updateBadge();
        } else {
            console.error("❌ Error responding to request:", data.error);
        }
    })
    .catch(err => console.error("⚠️ Fetch error:", err));
}

export { toggleNotifications };
