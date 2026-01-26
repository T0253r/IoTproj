const controllerGrid = document.getElementById('controller-grid');
const controllerRow = document.getElementById('controller-row');


let selectedControllerId = null;


function getStatusClass(c) {
    if (c.target_temp > c.curr_temp) return 'heating';
    if (c.target_temp < c.curr_temp) return 'cooling';
    return 'stable';
}

function getStatusInfo(priority) {
    if (priority == 2) return { className: 'status-locked', text: 'Ręczna zmiana' };
    if (priority == 1) return { className: 'status-auto', text: 'AutoTemp' };
    return { className: 'status-default', text: 'System' };
}

function createVortexSVG(controllerId) {
    // SVG content as string (acceptable for SVG which doesn't support createElement well)
    return `<svg xmlns="http://www.w3.org/2000/svg" version="1.1" xmlns:xlink="http://www.w3.org/1999/xlink"
            xmlns:svgjs="http://svgjs.dev/svgjs" viewBox="0 0 800 800">
            <defs>
                <linearGradient x1="50%" y1="0%" x2="50%" y2="100%" id="vvvortex-grad-${controllerId}">
                    <stop stop-opacity="1" offset="0%"></stop>
                    <stop stop-opacity="1" offset="100%"></stop>
                </linearGradient>
            </defs>
            <g stroke="url(#vvvortex-grad-${controllerId})" fill="none" stroke-linecap="round">
                <circle r="363" cx="400" cy="400" stroke-width="11" stroke-dasharray="27 16"
                    stroke-dashoffset="25" transform="rotate(60, 400, 400)" opacity="0.05"></circle>
                <circle r="346.5" cx="400" cy="400" stroke-width="11" stroke-dasharray="52 17"
                    stroke-dashoffset="25" transform="rotate(169, 400, 400)" opacity="0.10"></circle>
                <circle r="330" cx="400" cy="400" stroke-width="10" stroke-dasharray="33 38"
                    stroke-dashoffset="25" transform="rotate(234, 400, 400)" opacity="0.14"></circle>
                <circle r="313.5" cx="400" cy="400" stroke-width="10" stroke-dasharray="26 42"
                    stroke-dashoffset="25" transform="rotate(254, 400, 400)" opacity="0.19"></circle>
                <circle r="297" cx="400" cy="400" stroke-width="10" stroke-dasharray="46 36"
                    stroke-dashoffset="25" transform="rotate(54, 400, 400)" opacity="0.23"></circle>
                <circle r="280.5" cx="400" cy="400" stroke-width="10" stroke-dasharray="28 40"
                    stroke-dashoffset="25" transform="rotate(156, 400, 400)" opacity="0.28"></circle>
                <circle r="264" cx="400" cy="400" stroke-width="9" stroke-dasharray="53 27"
                    stroke-dashoffset="25" transform="rotate(32, 400, 400)" opacity="0.32"></circle>
                <circle r="247.5" cx="400" cy="400" stroke-width="9" stroke-dasharray="43 42"
                    stroke-dashoffset="25" transform="rotate(216, 400, 400)" opacity="0.37"></circle>
                <circle r="231" cx="400" cy="400" stroke-width="9" stroke-dasharray="31 12"
                    stroke-dashoffset="25" transform="rotate(215, 400, 400)" opacity="0.41"></circle>
                <circle r="214.5" cx="400" cy="400" stroke-width="8" stroke-dasharray="14 54"
                    stroke-dashoffset="25" transform="rotate(297, 400, 400)" opacity="0.46"></circle>
                <circle r="198" cx="400" cy="400" stroke-width="8" stroke-dasharray="17 17"
                    stroke-dashoffset="25" transform="rotate(308, 400, 400)" opacity="0.50"></circle>
                <circle r="181.5" cx="400" cy="400" stroke-width="8" stroke-dasharray="22 44"
                    stroke-dashoffset="25" transform="rotate(186, 400, 400)" opacity="0.55"></circle>
                <circle r="165" cx="400" cy="400" stroke-width="8" stroke-dasharray="55 25"
                    stroke-dashoffset="25" transform="rotate(172, 400, 400)" opacity="0.59"></circle>
                <circle r="148.5" cx="400" cy="400" stroke-width="7" stroke-dasharray="22 31"
                    stroke-dashoffset="25" transform="rotate(173, 400, 400)" opacity="0.64"></circle>
                <circle r="132" cx="400" cy="400" stroke-width="7" stroke-dasharray="50 49"
                    stroke-dashoffset="25" transform="rotate(311, 400, 400)" opacity="0.68"></circle>
                <circle r="115.5" cx="400" cy="400" stroke-width="7" stroke-dasharray="47 50"
                    stroke-dashoffset="25" transform="rotate(17, 400, 400)" opacity="0.73"></circle>
                <circle r="99" cx="400" cy="400" stroke-width="6" stroke-dasharray="25 47"
                    stroke-dashoffset="25" transform="rotate(121, 400, 400)" opacity="0.77"></circle>
                <circle r="82.5" cx="400" cy="400" stroke-width="6" stroke-dasharray="51 29"
                    stroke-dashoffset="25" transform="rotate(103, 400, 400)" opacity="0.82"></circle>
                <circle r="66" cx="400" cy="400" stroke-width="6" stroke-dasharray="21 43"
                    stroke-dashoffset="25" transform="rotate(10, 400, 400)" opacity="0.86"></circle>
                <circle r="49.5" cx="400" cy="400" stroke-width="6" stroke-dasharray="22 16"
                    stroke-dashoffset="25" transform="rotate(113, 400, 400)" opacity="0.91"></circle>
                <circle r="33" cx="400" cy="400" stroke-width="5" stroke-dasharray="34 24"
                    stroke-dashoffset="25" transform="rotate(120, 400, 400)" opacity="0.95"></circle>
                <circle r="16.5" cx="400" cy="400" stroke-width="5" stroke-dasharray="28 54"
                    stroke-dashoffset="25" transform="rotate(283, 400, 400)" opacity="1.00"></circle>
            </g>
        </svg>`;
}

function createOrUpdateControllerCard(c) {
    const cardId = `card-${c.controller_id}`;
    let card = document.getElementById(cardId);

    // If card doesn't exist, create it
    if (!card) {
        card = document.createElement('div');
        card.id = cardId;
        card.className = 'controller-card';
        card.onclick = () => selectController(c.controller_id);

        // Create structure
        const nameSpan = document.createElement('span');
        nameSpan.className = 'controller-name';

        const tempDiv = document.createElement('div');
        tempDiv.className = 'controller-card-temp';

        const currTempDiv = document.createElement('div');
        const currTempStrong = document.createElement('strong');
        const currTempLabel = document.createElement('span');
        currTempLabel.textContent = 'Obecna';
        currTempDiv.appendChild(currTempStrong);
        currTempDiv.appendChild(currTempLabel);

        const targetTempDiv = document.createElement('div');
        const targetTempStrong = document.createElement('strong');
        const targetTempLabel = document.createElement('span');
        targetTempLabel.textContent = 'Docelowa';
        targetTempDiv.appendChild(targetTempStrong);
        targetTempDiv.appendChild(targetTempLabel);

        tempDiv.appendChild(currTempDiv);
        tempDiv.appendChild(targetTempDiv);

        const infoDiv = document.createElement('div');
        infoDiv.className = 'info-small';
        const statusSpan = document.createElement('span');
        infoDiv.appendChild(statusSpan);

        const vortexDiv = document.createElement('div');
        vortexDiv.className = 'card-vortex';
        vortexDiv.innerHTML = createVortexSVG(c.controller_id);

        card.appendChild(nameSpan);
        card.appendChild(tempDiv);
        card.appendChild(infoDiv);
        card.appendChild(vortexDiv);

        controllerRow.appendChild(card);
    }

    // Update card content
    const statusClass = getStatusClass(c);
    card.className = `controller-card ${statusClass}`;
    if (selectedControllerId === c.controller_id) {
        card.classList.add('active');
    }

    const nameSpan = card.querySelector('.controller-name');
    nameSpan.textContent = c.name;

    const temps = card.querySelectorAll('.controller-card-temp strong');
    if (temps.length >= 2) {
        temps[0].textContent = `${c.curr_temp}°C`;
        temps[1].textContent = `${c.target_temp}°C`;
    }

    const statusInfo = getStatusInfo(c.priority);
    const statusSpan = card.querySelector('.info-small span');
    statusSpan.className = statusInfo.className;
    statusSpan.textContent = statusInfo.text;

}

function createOrUpdateControllerDetails(c) {
    const detailsId = `controller-${c.controller_id}`;
    let details = document.getElementById(detailsId);

    // If details don't exist, create them
    if (!details) {
        details = document.createElement('div');
        details.id = detailsId;
        details.className = 'controller-details';
        details.style.display = 'none';

        // Create structure
        const h2 = document.createElement('h2');

        // Temperature Display Grid
        const tempGrid = document.createElement('div');
        tempGrid.className = 'temp-grid';

        const currTempBox = document.createElement('div');
        currTempBox.className = 'temp-box';
        const currLabel = document.createElement('div');
        currLabel.className = 'temp-box-label';
        currLabel.textContent = 'Aktualna temperatura';
        const currValue = document.createElement('div');
        currValue.className = 'temp-box-value';
        currValue.id = `curr-temp-${c.controller_id}`;
        currTempBox.appendChild(currLabel);
        currTempBox.appendChild(currValue);

        const targetTempBox = document.createElement('div');
        targetTempBox.className = 'temp-box';
        const targetLabel = document.createElement('div');
        targetLabel.className = 'temp-box-label';
        targetLabel.textContent = 'Zadana temperatura';
        const targetValue = document.createElement('div');
        targetValue.className = 'temp-box-value';
        targetValue.id = `target-temp-${c.controller_id}`;
        const tempControls = document.createElement('div');
        tempControls.className = 'temp-controls';
        const plusBtn = document.createElement('button');
        plusBtn.className = 'temp-btn';
        plusBtn.textContent = '+';
        plusBtn.onclick = () => adjustTemp(c.controller_id, 0.5);
        const minusBtn = document.createElement('button');
        minusBtn.className = 'temp-btn';
        minusBtn.textContent = '-';
        minusBtn.onclick = () => adjustTemp(c.controller_id, -0.5);
        tempControls.appendChild(plusBtn);
        tempControls.appendChild(minusBtn);
        targetTempBox.appendChild(targetLabel);
        targetTempBox.appendChild(targetValue);
        targetTempBox.appendChild(tempControls);

        tempGrid.appendChild(currTempBox);
        tempGrid.appendChild(targetTempBox);

        // Status Lines
        const statusLine1 = document.createElement('div');
        statusLine1.className = 'status-line';
        statusLine1.textContent = 'Status: ';
        const statusTextSpan = document.createElement('span');
        statusTextSpan.className = 'status-text';
        statusLine1.appendChild(statusTextSpan);

        const statusLine2 = document.createElement('div');
        statusLine2.className = 'status-line';
        statusLine2.id = `last-change-${c.controller_id}`;

        // AutoTemp Section
        const sectionTitle = document.createElement('div');
        sectionTitle.className = 'section-title';
        sectionTitle.textContent = 'Twoje ustawienia AutoTemp™';

        const infoSmall = document.createElement('div');
        infoSmall.className = 'info-small';
        infoSmall.style.marginBottom = '1rem';
        infoSmall.textContent = 'Automatyczna temperatura komfortowa po wykryciu obecności';

        // Toggle Switch
        const toggleContainer = document.createElement('div');
        toggleContainer.className = 'toggle-container';
        const toggleLabel = document.createElement('label');
        toggleLabel.textContent = 'Używaj AutoTemp™ w tym pokoju:';
        const toggleSwitch = document.createElement('label');
        toggleSwitch.className = 'toggle-switch';
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = `autotemp-${c.controller_id}`;
        const slider = document.createElement('span');
        slider.className = 'slider';
        toggleSwitch.appendChild(checkbox);
        toggleSwitch.appendChild(slider);
        toggleContainer.appendChild(toggleLabel);
        toggleContainer.appendChild(toggleSwitch);

        // Comfort Temperature Control
        const comfortControl = document.createElement('div');
        comfortControl.className = 'comfort-temp-control';
        const comfortLabel = document.createElement('div');
        comfortLabel.className = 'comfort-temp-label';
        comfortLabel.textContent = 'Temperatura komfortowa';
        const comfortControls = document.createElement('div');
        comfortControls.className = 'comfort-controls';
        const prefMinusBtn = document.createElement('button');
        prefMinusBtn.className = 'temp-btn';
        prefMinusBtn.textContent = '-';
        prefMinusBtn.onclick = () => adjustPref(c.controller_id, -0.5);
        const prefValue = document.createElement('div');
        prefValue.className = 'comfort-temp-value';
        prefValue.id = `pref-temp-${c.controller_id}`;
        const prefPlusBtn = document.createElement('button');
        prefPlusBtn.className = 'temp-btn';
        prefPlusBtn.textContent = '+';
        prefPlusBtn.onclick = () => adjustPref(c.controller_id, 0.5);
        comfortControls.appendChild(prefMinusBtn);
        comfortControls.appendChild(prefValue);
        comfortControls.appendChild(prefPlusBtn);
        comfortControl.appendChild(comfortLabel);
        comfortControl.appendChild(comfortControls);

        // Append all sections
        details.appendChild(h2);
        details.appendChild(tempGrid);
        details.appendChild(statusLine1);
        details.appendChild(statusLine2);
        details.appendChild(sectionTitle);
        details.appendChild(infoSmall);
        details.appendChild(toggleContainer);
        details.appendChild(comfortControl);

        controllerGrid.appendChild(details);
    }

    // Update details content
    const h2 = details.querySelector('h2');
    h2.textContent = c.name;


    const currTempEl = document.getElementById(`curr-temp-${c.controller_id}`);
    console.log(c, currTempEl, (`curr-temp-${c.controller_id}`));
    currTempEl.textContent = `${c.curr_temp}°C`;

    const targetTempEl = document.getElementById(`target-temp-${c.controller_id}`);
    targetTempEl.textContent = `${c.target_temp}°C`;

    const statusInfo = getStatusInfo(c.priority);
    const statusTextSpan = details.querySelector('.status-text span');
    if (statusTextSpan) {
        statusTextSpan.className = statusInfo.className;
        statusTextSpan.textContent = statusInfo.text;
    } else {
        const statusText = details.querySelector('.status-text');
        statusText.textContent = '';
        const span = document.createElement('span');
        span.className = statusInfo.className;
        span.textContent = statusInfo.text;
        statusText.appendChild(span);
    }

    const lastChangeLine = document.getElementById(`last-change-${c.controller_id}`);
    lastChangeLine.textContent = `Ostatnia zmiana: ${c.locked_by_name || 'N/A'} (${c.last_seen || 'Never'})`;

    const checkbox = document.getElementById(`autotemp-${c.controller_id}`);
    checkbox.checked = !!c.user_pref_temp;
    checkbox.onchange = () => toggleAutoTemp(c.controller_id, checkbox.checked, c.user_pref_temp || 21.5);

    const prefTempEl = document.getElementById(`pref-temp-${c.controller_id}`);
    prefTempEl.textContent = `${c.user_pref_temp || '21.5'}°C`;
}

function loadControllers(controllers) {

    controllers.forEach(c => {
        createOrUpdateControllerCard(c);
        createOrUpdateControllerDetails(c);
    });

    // Select first controller if none selected
    if (controllers.length > 0 && !selectedControllerId) {
        selectController(controllers[0].controller_id);
    } else if (selectedControllerId) {
        // Reselect current controller to maintain state
        selectController(selectedControllerId);
    }
}

function selectController(controllerId) {
    selectedControllerId = controllerId;
    // Hide all controller details
    const details = document.querySelectorAll(".controller-grid .controller-details");
    details.forEach((detail) => (detail.style.display = "none"));

    // Remove active class from all cards
    const cards = document.querySelectorAll(".controller-card");
    cards.forEach((card) => card.classList.remove("active"));

    // Show selected controller details
    const selectedController = document.getElementById("controller-" + controllerId);
    if (selectedController) {
        selectedController.style.display = "block";
    }

    // Add active class to selected card
    const selectedCard = document.getElementById("card-" + controllerId);
    if (selectedCard) {
        selectedCard.classList.add("active");
    }
}

async function adjustTemp(controllerId, delta) {
    const targetElement = document.getElementById(`target-temp-${controllerId}`);
    const currentTemp = parseFloat(targetElement.textContent);
    const newTemp = currentTemp + delta;

    // Validate temperature range
    if (newTemp < 15 || newTemp > 40) {
        alert('Temperatura musi być w zakresie 15-40°C');
        return;
    }

    // Optimistically update UI
    targetElement.textContent = `${newTemp}°C`;

    // Update card temperature and status
    const card = document.getElementById(`card-${controllerId}`);
    if (card) {
        const cardTargetTemp = card.querySelectorAll('.controller-card-temp strong')[1];
        if (cardTargetTemp) {
            cardTargetTemp.textContent = `${newTemp}°C`;
        }

        // Get current temp to determine new status
        const cardCurrTemp = card.querySelectorAll('.controller-card-temp strong')[0];
        const currTemp = parseFloat(cardCurrTemp.textContent);

        // Update status class
        card.className = 'controller-card';
        if (newTemp > currTemp) {
            card.classList.add('heating');
        } else if (newTemp < currTemp) {
            card.classList.add('cooling');
        } else {
            card.classList.add('stable');
        }
        if (selectedControllerId === controllerId) {
            card.classList.add('active');
        }

        // Update status info - manual change means priority 2
        const statusInfo = getStatusInfo(2);
        const statusSpan = card.querySelector('.info-small span');
        if (statusSpan) {
            statusSpan.className = statusInfo.className;
            statusSpan.textContent = statusInfo.text;
        }
    }

    // Update status info in details view
    const details = document.getElementById(`controller-${controllerId}`);
    if (details) {
        const statusInfo = getStatusInfo(2);
        const statusTextSpan = details.querySelector('.status-text span');
        if (statusTextSpan) {
            statusTextSpan.className = statusInfo.className;
            statusTextSpan.textContent = statusInfo.text;
        } else {
            const statusText = details.querySelector('.status-text');
            if (statusText) {
                statusText.textContent = '';
                const span = document.createElement('span');
                span.className = statusInfo.className;
                span.textContent = statusInfo.text;
                statusText.appendChild(span);
            }
        }
    }

    try {
        const response = await fetch('/set_manual_temp', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                controller_id: controllerId,
                target_temp: newTemp
            })
        });

        const result = await response.json();
        if (!result.success) {
            alert(result.message);
            // Revert UI on error
            targetElement.textContent = `${currentTemp}°C`;
            const card = document.getElementById(`card-${controllerId}`);
            if (card) {
                const cardTargetTemp = card.querySelectorAll('.controller-card-temp strong')[1];
                if (cardTargetTemp) {
                    cardTargetTemp.textContent = `${currentTemp}°C`;
                }
                // Revert status class
                const cardCurrTemp = card.querySelectorAll('.controller-card-temp strong')[0];
                const currTemp = parseFloat(cardCurrTemp.textContent);
                card.className = 'controller-card';
                if (currentTemp > currTemp) {
                    card.classList.add('heating');
                } else if (currentTemp < currTemp) {
                    card.classList.add('cooling');
                } else {
                    card.classList.add('stable');
                }
                if (selectedControllerId === controllerId) {
                    card.classList.add('active');
                }
            }
        }
    } catch (error) {
        console.error('Error adjusting temperature:', error);
        // Revert UI on error
        targetElement.textContent = `${currentTemp}°C`;
        const card = document.getElementById(`card-${controllerId}`);
        if (card) {
            const cardTargetTemp = card.querySelectorAll('.controller-card-temp strong')[1];
            if (cardTargetTemp) {
                cardTargetTemp.textContent = `${currentTemp}°C`;
            }
            // Revert status class
            const cardCurrTemp = card.querySelectorAll('.controller-card-temp strong')[0];
            const currTemp = parseFloat(cardCurrTemp.textContent);
            card.className = 'controller-card';
            if (currentTemp > currTemp) {
                card.classList.add('heating');
            } else if (currentTemp < currTemp) {
                card.classList.add('cooling');
            } else {
                card.classList.add('stable');
            }
            if (selectedControllerId === controllerId) {
                card.classList.add('active');
            }
        }
    }
}

async function adjustPref(controllerId, delta) {
    const prefElement = document.getElementById(`pref-temp-${controllerId}`);
    const currentPref = parseFloat(prefElement.textContent);
    const newPref = currentPref + delta;

    // Validate temperature range
    if (newPref < 15 || newPref > 40) {
        alert('Temperatura musi być w zakresie 15-40°C');
        return;
    }

    // Optimistically update UI
    prefElement.textContent = `${newPref}°C`;

    try {
        const response = await fetch('/set_preference', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                controller_id: controllerId,
                pref_temp: newPref
            })
        });

        const result = await response.json();
        if (!result.success) {
            alert(result.message);
            // Revert UI on error
            prefElement.textContent = `${currentPref}°C`;
        }
    } catch (error) {
        console.error('Error adjusting preference:', error);
        // Revert UI on error
        prefElement.textContent = `${currentPref}°C`;
    }
}

async function toggleAutoTemp(controllerId, isEnabled, currentTemp) {
    const endpoint = isEnabled ? '/set_preference' : '/clear_preference';
    const body = isEnabled
        ? { controller_id: controllerId, pref_temp: currentTemp }
        : { controller_id: controllerId };

    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(body)
        });

        const result = await response.json();
        if (!result.success) {
            alert(result.message);
            // Revert checkbox on error
            const checkbox = document.getElementById(`autotemp-${controllerId}`);
            if (checkbox) {
                checkbox.checked = !isEnabled;
            }
        }
    } catch (error) {
        console.error('Error toggling AutoTemp:', error);
    }
}

async function refreshControllers(isInitialLoad = false) {
    try {
        const response = await fetch('/refresh_controllers');
        const controllers = await response.json();

        // Always use create-or-update logic for consistency
        controllers.forEach(c => {
            createOrUpdateControllerCard(c);
            createOrUpdateControllerDetails(c);
        });

        // On initial load, ensure first controller is selected
        if (isInitialLoad && controllers.length > 0 && !selectedControllerId) {
            selectController(controllers[0].controller_id);
        }
    } catch (error) {
        console.error('Error refreshing controllers:', error);
    }
}

// Load controllers on page load and set up auto-refresh
window.addEventListener("DOMContentLoaded", async function () {
    // Initial load
    await refreshControllers(true);

    // Auto-refresh every 2 seconds
    setInterval(() => refreshControllers(false), 2000);
});