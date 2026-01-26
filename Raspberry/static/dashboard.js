function selectRoom(roomId) {
    // Hide all room cards
    const cards = document.querySelectorAll(".room-grid .room-details");
    cards.forEach((card) => (card.style.display = "none"));

    // Show selected room card
    const selectedRoom = document.getElementById("room-" + roomId);
    if (selectedRoom) {
        selectedRoom.style.display = "block";
    }
}

// Show first room by default on page load
window.addEventListener("DOMContentLoaded", function () {
    const firstCard = document.querySelector(".room-grid .card");
    if (firstCard) {
        const roomId = firstCard.id.replace("room-", "");
        selectRoom(parseInt(roomId));
    }
});
