document.addEventListener("DOMContentLoaded", function () {
    function toggleNotifications() {
        document.getElementById("notification-dropdown")?.classList.toggle("show");
    }

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

    function updateBadge() {
        const badge = document.getElementById("notification-badge");
        if (!badge) return;

        const count = document.querySelectorAll("#notification-dropdown p").length;
        badge.textContent = count;
        badge.style.display = count > 0 ? "block" : "none";
    }

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

    function fetchFriends() {
        fetch("/get_friends")
            .then(response => response.json())
            .then(data => {
                const friends = data.friends;

                if (Array.isArray(friends) && friends.length > 0) {
                    updateFriendsUI(friends);
                    setTimeout(fetchFriends, 5000);
                } else {
                    console.info("🛑 No friends found. Halting fetch.");
                    // Stop polling if user has no friends
                }
            })
            .catch(error => {
                console.error("❌ Error fetching friends:", error);
                setTimeout(fetchFriends, 5000); // Retry on error
            });
    }



    function updateFriendsUI(friends) {
        let friendsContainer = document.getElementById("friends-container");
        if (!friendsContainer) {
            console.error("❌ Friends container not found.");
            return;
        }

        friends.forEach(friend => {
            let friendId = friend.id;
            let existingFriend = document.getElementById(`friend-${friendId}`);

            if (existingFriend) {
                let statusElement = existingFriend.querySelector(".status");
                if (statusElement) {
                    statusElement.classList.remove("online", "offline");
                    statusElement.classList.add(friend.online ? "online" : "offline");
                }
            } else {
                let friendCard = document.createElement("div");
                friendCard.classList.add("friend-card");
                friendCard.id = `friend-${friendId}`;

                friendCard.innerHTML = `
                    <img src="${friend.profile_pic}" alt="Profile Picture" width="50">
                    <h4>${friend.username}</h4>
                    <p>Status: <span class="status ${friend.online ? 'online' : 'offline'}"></span></p>
                    <button onclick="messageFriend('${friend.id}')">💬 Message</button>
                `;

                friendsContainer.appendChild(friendCard);
            }
        });
    }

    function updateFriendStatus(friendId, isOnline) {
        let friendElement = document.getElementById(`friend-${friendId}`);
        if (!friendElement) {
            console.warn(`⚠️ Friend element with ID "friend-${friendId}" not found.`);
            return;
        }

        let statusElement = friendElement.querySelector(".status");
        if (statusElement) {
            statusElement.classList.remove("online", "offline");
            statusElement.classList.add(isOnline ? "online" : "offline");
        }
    }

    function messageFriend(friendId) {
        alert(`Messaging user ${friendId}`);
    }


    fetchFriends(); // Start fetching friends on page load
});
