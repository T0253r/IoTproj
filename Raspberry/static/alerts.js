function hasOpenModal() {
    return document.querySelector(".custom-modal-overlay") !== null;
}

function showCustomAlert(message) {
    if (hasOpenModal()) {
        return Promise.resolve();
    }

    return new Promise((resolve) => {
        const overlay = document.createElement("div");
        overlay.className = "custom-modal-overlay";

        const modal = document.createElement("div");
        modal.className = "custom-modal";

        const messageDiv = document.createElement("div");
        messageDiv.className = "custom-modal-message";
        messageDiv.textContent = message;

        const buttonsDiv = document.createElement("div");
        buttonsDiv.className = "custom-modal-buttons";

        const okBtn = document.createElement("button");
        okBtn.className = "custom-modal-btn";
        okBtn.textContent = "OK";
        okBtn.onclick = () => {
            document.body.removeChild(overlay);
            resolve();
        };

        buttonsDiv.appendChild(okBtn);
        modal.appendChild(messageDiv);
        modal.appendChild(buttonsDiv);
        overlay.appendChild(modal);
        document.body.appendChild(overlay);

        okBtn.focus();
    });
}

function showCustomConfirm(message) {
    if (hasOpenModal()) {
        return Promise.resolve(false);
    }

    return new Promise((resolve) => {
        const overlay = document.createElement("div");
        overlay.className = "custom-modal-overlay";

        const modal = document.createElement("div");
        modal.className = "custom-modal";

        const messageDiv = document.createElement("div");
        messageDiv.className = "custom-modal-message";
        messageDiv.textContent = message;

        const buttonsDiv = document.createElement("div");
        buttonsDiv.className = "custom-modal-buttons";

        const cancelBtn = document.createElement("button");
        cancelBtn.className =
            "custom-modal-btn custom-modal-btn-cancel";
        cancelBtn.textContent = "Anuluj";
        cancelBtn.onclick = () => {
            document.body.removeChild(overlay);
            resolve(false);
        };

        const confirmBtn = document.createElement("button");
        confirmBtn.className =
            "custom-modal-btn custom-modal-btn-danger";
        confirmBtn.textContent = "Potwierdź";
        confirmBtn.onclick = () => {
            document.body.removeChild(overlay);
            resolve(true);
        };

        buttonsDiv.appendChild(cancelBtn);
        buttonsDiv.appendChild(confirmBtn);
        modal.appendChild(messageDiv);
        modal.appendChild(buttonsDiv);
        overlay.appendChild(modal);
        document.body.appendChild(overlay);

        confirmBtn.focus();
    });
}
