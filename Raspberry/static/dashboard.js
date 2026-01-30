const controllerGrid = document.getElementById('controller-grid');
const controllerRow = document.getElementById('controller-row');


let selectedControllerId = null;

// Track pending client-side overrides to avoid refresh flicker
const pendingManualTargets = {}; // { [controllerId]: { value: number, updatedAt: number } }
const pendingPrefTemps = {};     // reserved for future use
const PENDING_TTL_MS = 3000;     // keep overrides for a short time
const SIMULATED_FETCH_DELAY_MS = 800; // artificial latency for testing

function isTimeOffline(last_seen_controller) {
    const last_seen = Date.parse(last_seen_controller);
    const current_time_on_server = Date.now() - server_time_offset
    const MAX_DELAY = 1000 * 60 * 1; // 1 minute

    return last_seen + MAX_DELAY < current_time_on_server
}

function getStatusClass(c) {
    if (c.target_temp > c.curr_temp) return 'heating';
    if (c.target_temp < c.curr_temp) return 'cooling';
    return 'stable';
}

const statusToDesc = {
    'heating': 'Grzanie',
    'cooling': 'Oczekiwanie',
    'stable': 'Stabilna'
}

function getStatusInfo(priority, user = "") {
    if (priority == 2) return { className: 'status-locked', text: `${user}` };
    if (priority == 1) return { className: 'status-auto', text: `AutoTemp™ ${user}` };
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

function createTemperaturePicker(controllerId, carouselId, onUpClick, onDownClick) {
    // Create picker container
    const pickerContainer = document.createElement('div');
    pickerContainer.className = 'temp-picker-container';

    // Up arrow
    const upArrow = document.createElement('div');
    upArrow.className = 'picker-arrow picker-arrow-up';
    upArrow.textContent = '▲';
    upArrow.onclick = onUpClick;

    // Carousel wrapper
    const carouselWrapper = document.createElement('div');
    carouselWrapper.className = 'picker-carousel-wrapper';
    const carousel = document.createElement('div');
    carousel.className = 'picker-carousel';
    carousel.id = carouselId;

    // Create temperature options from 15 to 40
    for (let temp = 40; temp >= 15; temp -= 0.5) {
        const option = document.createElement('div');
        option.className = 'picker-option';
        option.textContent = `${temp.toFixed(1)}\u00b0C`;
        option.dataset.temp = temp;
        carousel.appendChild(option);
    }

    carouselWrapper.appendChild(carousel);

    // Down arrow
    const downArrow = document.createElement('div');
    downArrow.className = 'picker-arrow picker-arrow-down';
    downArrow.textContent = '▼';
    downArrow.onclick = onDownClick;

    pickerContainer.appendChild(upArrow);
    pickerContainer.appendChild(carouselWrapper);
    pickerContainer.appendChild(downArrow);

    return pickerContainer;
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
    if (c.user_pref_temp) {
        card.classList.add('autotemp-enabled');
    }

    const is_offline = isTimeOffline(c.last_seen)
    if (is_offline) card.className = "controller-card offline stable"

    const nameSpan = card.querySelector('.controller-name');
    nameSpan.textContent = c.name;

    const temps = card.querySelectorAll('.controller-card-temp strong');
    if (temps.length >= 2) {
        temps[0].textContent = `${parseFloat(c.curr_temp).toFixed(1)}°C`;
        temps[1].textContent = `${parseFloat(c.target_temp).toFixed(1)}°C`;
    }

    const statusInfo = getStatusInfo(c.priority, c.locked_by_name != "" ? c.locked_by_name : c.set_by);
    const statusSpan = card.querySelector('.info-small span');
    statusSpan.className = statusInfo.className;
    statusSpan.textContent = `Kontrola: ${statusInfo.text}`;

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
        currLabel.textContent = 'Obecna temperatura';
        const currValue = document.createElement('div');
        currValue.className = 'temp-box-value';
        currValue.id = `curr-temp-${c.controller_id}`;
        currTempBox.appendChild(currLabel);
        currTempBox.appendChild(currValue);

        const targetTempBox = document.createElement('div');
        targetTempBox.className = 'temp-box';
        const targetLabel = document.createElement('div');
        targetLabel.className = 'temp-box-label';
        targetLabel.textContent = 'Docelowa temperatura';

        // Create picker using helper function
        const pickerContainer = createTemperaturePicker(
            c.controller_id,
            `picker-carousel-${c.controller_id}`,
            () => adjustTemp(c.controller_id, 0.5),
            () => adjustTemp(c.controller_id, -0.5)
        );

        targetTempBox.appendChild(targetLabel);
        targetTempBox.appendChild(pickerContainer);

        tempGrid.appendChild(currTempBox);
        tempGrid.appendChild(targetTempBox);

        // Status Lines
        const statusBox = document.createElement('div');
        statusBox.className = 'status-box';

        const statusLine1 = document.createElement('div');
        statusLine1.className = 'status-line status-text temp-box-value';
        const statusLine2 = document.createElement('div');
        statusLine2.className = 'temp-box-label';
        statusLine2.textContent = 'Kontrolowane przez';
        statusLine2.id = `last-change-${c.controller_id}`;

        statusBox.appendChild(statusLine2);
        statusBox.appendChild(statusLine1);

        tempGrid.appendChild(statusBox);

        // AutoTemp Section
        const sectionTitle = document.createElement('div');
        sectionTitle.className = 'section-title';
        sectionTitle.textContent = 'Twoje ustawienia AutoTemp™';

        const infoSmall = document.createElement('div');
        infoSmall.className = 'info-small-autotemp';
        infoSmall.style.marginBottom = '1rem';
        infoSmall.textContent = 'Automatyczna temperatura komfortowa po wykryciu Twojej obecności';

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

        // Create picker using helper function
        const prefPickerContainer = createTemperaturePicker(
            c.controller_id,
            `pref-picker-carousel-${c.controller_id}`,
            () => adjustPref(c.controller_id, 0.5),
            () => adjustPref(c.controller_id, -0.5)
        );

        comfortControl.appendChild(comfortLabel);
        comfortControl.appendChild(prefPickerContainer);

        // Append all sections
        details.appendChild(h2);
        details.appendChild(tempGrid);
        details.appendChild(sectionTitle);
        details.appendChild(infoSmall);
        details.appendChild(toggleContainer);
        details.appendChild(comfortControl);

        controllerGrid.appendChild(details);
    }

    // Update details content
    const statusClass = getStatusClass(c);
    details.className = `controller-details ${statusClass}`;

    const is_offline = isTimeOffline(c.last_seen)
    if (is_offline) details.className = "controller-details offline stable"

    const h2 = details.querySelector('h2');
    h2.textContent = c.name;


    const currTempEl = document.getElementById(`curr-temp-${c.controller_id}`);
    currTempEl.textContent = `${parseFloat(c.curr_temp).toFixed(1)}°C`;

    // Update picker carousel position
    const carousel = document.getElementById(`picker-carousel-${c.controller_id}`);
    if (carousel) {
        updatePickerPosition(carousel, c.target_temp);
        updatePickerArrowsVisibility(`picker-carousel-${c.controller_id}`, c.target_temp);
    }

    const statusInfo = getStatusInfo(c.priority, c.locked_by_name != "" ? c.locked_by_name : c.set_by);
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

    const checkbox = document.getElementById(`autotemp-${c.controller_id}`);
    checkbox.checked = !!c.user_pref_temp;
    checkbox.onchange = () => toggleAutoTemp(c.controller_id, checkbox.checked, c.user_pref_temp || 21.5);

    // Update preference picker carousel position
    const prefCarousel = document.getElementById(`pref-picker-carousel-${c.controller_id}`);
    if (prefCarousel) {
        updatePickerPosition(prefCarousel, c.user_pref_temp || 21.5);
        updatePickerArrowsVisibility(`pref-picker-carousel-${c.controller_id}`, c.user_pref_temp || 21.5);
    }
}

function loadControllers(controllers) {
    // Handle empty controllers case
    if (controllers.length === 0) {
        showNoControllersMessage();
        return;
    } else {
        hideNoControllersMessage();
    }

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

function showNoControllersMessage() {
    let messageDiv = document.getElementById('no-controllers-message');
    if (!messageDiv) {
        messageDiv = document.createElement('div');
        messageDiv.id = 'no-controllers-message';
        messageDiv.className = 'no-controllers-message';
        messageDiv.innerHTML = `
            <div class="no-controllers-content">
                <span class="mdi--information-outline no-controllers-icon"></span>
                <hr>
                <h3>Brak dostępnych kontrolerów</h3>
                <p>Nie znaleziono żadnych kontrolerów w systemie.</p>
                <div><a href="https://youtu.be/dQw4w9WgXcQ">Zakup kontroler</a> w oficjalnym sklepie.</div>
            </div>
        `;
        controllerRow.appendChild(messageDiv);
    }
    messageDiv.style.display = 'block';
}

function hideNoControllersMessage() {
    const messageDiv = document.getElementById('no-controllers-message');
    if (messageDiv) {
        messageDiv.style.display = 'none';
    }
}

function updatePickerPosition(carousel, targetTemp) {
    const options = carousel.querySelectorAll('.picker-option');
    const optionHeight = parseFloat(getComputedStyle(options[0]).height);

    // Find the index of the target temperature
    let targetIndex = 0;
    options.forEach((option, index) => {
        const temp = parseFloat(option.dataset.temp);
        option.classList.remove('selected');
        if (temp === targetTemp) {
            targetIndex = index;
            option.classList.add('selected');
        }
    });

    // Scroll to position the selected item in the center
    const scrollPosition = targetIndex * optionHeight;
    carousel.style.transform = `translateY(-${scrollPosition}px)`;
}

function updatePickerArrowsVisibility(carouselId, currentTemp) {
    const carousel = document.getElementById(carouselId);
    if (!carousel) return;

    const pickerContainer = carousel.closest('.temp-picker-container');
    if (!pickerContainer) return;

    const upArrow = pickerContainer.querySelector('.picker-arrow-up');
    const downArrow = pickerContainer.querySelector('.picker-arrow-down');

    // Hide up arrow at max temperature (40°C)
    if (upArrow) {
        upArrow.classList.toggle('disabled', currentTemp >= 40);
    }

    // Hide down arrow at min temperature (15°C)
    if (downArrow) {
        downArrow.classList.toggle('disabled', currentTemp <= 15);
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
    // Get current temperature from carousel
    const carousel = document.getElementById(`picker-carousel-${controllerId}`);
    const selected = carousel.querySelector('.picker-option.selected');
    const currentTemp = selected ? parseFloat(selected.dataset.temp) : 21.5;
    const newTemp = currentTemp + delta;

    // Validate temperature range
    if (newTemp < 15 || newTemp > 40) {
        showCustomAlert('Temperatura musi być w zakresie 15-40°C');
        return;
    }

    // Optimistically update UI - update picker carousel
    if (carousel) {
        updatePickerPosition(carousel, newTemp);
        updatePickerArrowsVisibility(`picker-carousel-${controllerId}`, newTemp);
    }

    // Mark a pending override so auto-refresh won't revert immediately
    pendingManualTargets[controllerId] = { value: newTemp, updatedAt: Date.now() };

    // Update card temperature and status
    const card = document.getElementById(`card-${controllerId}`);
    if (card) {
        const cardTargetTemp = card.querySelectorAll('.controller-card-temp strong')[1];
        if (cardTargetTemp) {
            cardTargetTemp.textContent = `${newTemp.toFixed(1)}°C`;
        }

        // Get current temp to determine new status
        const cardCurrTemp = card.querySelectorAll('.controller-card-temp strong')[0];
        const currTemp = parseFloat(cardCurrTemp.textContent);

        // Update status class
        // card.className = 'controller-card';
        card.classList.remove('heating', 'cooling', 'stable');
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
        const statusInfo = getStatusInfo(2, myusername);
        const statusSpan = card.querySelector('.info-small span');
        if (statusSpan) {
            statusSpan.className = statusInfo.className;
            statusSpan.textContent = `Kontrola: ${statusInfo.text}`;
        }
    }

    // Update status info in details view
    const details = document.getElementById(`controller-${controllerId}`);
    if (details) {
        // Get current temp to determine new status
        const currTempEl = document.getElementById(`curr-temp-${controllerId}`);
        const currTemp = currTempEl ? parseFloat(currTempEl.textContent) : 21.5;

        // Update details status class
        details.className = 'controller-details';
        if (newTemp > currTemp) {
            details.classList.add('heating');
        } else if (newTemp < currTemp) {
            details.classList.add('cooling');
        } else {
            details.classList.add('stable');
        }

        const statusInfo = getStatusInfo(2, myusername);
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
        if (SIMULATED_FETCH_DELAY_MS > 0) {
            await sleep(SIMULATED_FETCH_DELAY_MS);
        }
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
            showCustomAlert(result.message);
            // Revert UI on error
            if (carousel) {
                updatePickerPosition(carousel, currentTemp);
            }
            const card = document.getElementById(`card-${controllerId}`);
            if (card) {
                const cardTargetTemp = card.querySelectorAll('.controller-card-temp strong')[1];
                if (cardTargetTemp) {
                    cardTargetTemp.textContent = `${currentTemp.toFixed(1)}°C`;
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
            delete pendingManualTargets[controllerId];
        }
    } catch (error) {
        console.error('Error adjusting temperature:', error);
        // Revert UI on error
        if (carousel) {
            updatePickerPosition(carousel, currentTemp);
        }
        const card = document.getElementById(`card-${controllerId}`);
        if (card) {
            const cardTargetTemp = card.querySelectorAll('.controller-card-temp strong')[1];
            if (cardTargetTemp) {
                cardTargetTemp.textContent = `${currentTemp.toFixed(1)}°C`;
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
        delete pendingManualTargets[controllerId];
    }
}

async function adjustPref(controllerId, delta) {
    // Get current preference from carousel
    const prefCarousel = document.getElementById(`pref-picker-carousel-${controllerId}`);
    const selected = prefCarousel.querySelector('.picker-option.selected');
    const currentPref = selected ? parseFloat(selected.dataset.temp) : 21.5;
    const newPref = currentPref + delta;

    // Validate temperature range
    if (newPref < 15 || newPref > 40) {
        showCustomAlert('Temperatura musi być w zakresie 15-40°C');
        return;
    }

    // Optimistically update UI
    if (prefCarousel) {
        updatePickerPosition(prefCarousel, newPref);
        updatePickerArrowsVisibility(`pref-picker-carousel-${controllerId}`, newPref);
    }

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
            showCustomAlert(result.message);
            // Revert UI on error
            if (prefCarousel) {
                updatePickerPosition(prefCarousel, currentPref);
            }
        }
    } catch (error) {
        console.error('Error adjusting preference:', error);
        // Revert UI on error
        if (prefCarousel) {
            updatePickerPosition(prefCarousel, currentPref);
        }
    }
}

async function toggleAutoTemp(controllerId, isEnabled, currentTemp) {
    const endpoint = isEnabled ? '/set_preference' : '/clear_preference';
    const body = isEnabled
        ? { controller_id: controllerId, pref_temp: currentTemp }
        : { controller_id: controllerId };

    const card = document.getElementById(`card-${controllerId}`);
    if (isEnabled) card.classList.add('autotemp-enabled');
    else card.classList.remove('autotemp-enabled');
    

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
            showCustomAlert(result.message);
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

        // Handle empty controllers case
        if (controllers.length === 0) {
            showNoControllersMessage();
            return;
        } else {
            hideNoControllersMessage();
        }

        // Always use create-or-update logic for consistency
        controllers.forEach(c => {
            createOrUpdateControllerCard(c);
            createOrUpdateControllerDetails(c);

            // Apply client-side override if present and still fresh
            const override = pendingManualTargets[c.controller_id];
            if (override) {
                const isFresh = Date.now() - override.updatedAt < PENDING_TTL_MS;
                if (isFresh && Math.abs(override.value - parseFloat(c.target_temp)) > 0.0001) {
                    applyManualOverride(c.controller_id, override.value);
                } else {
                    // If backend caught up or override expired, drop it
                    if (!isFresh || Math.abs(override.value - parseFloat(c.target_temp)) <= 0.0001) {
                        delete pendingManualTargets[c.controller_id];
                    }
                }
            }
        });

        // On initial load, ensure first controller is selected
        if (isInitialLoad && controllers.length > 0 && !selectedControllerId) {
            selectController(controllers[0].controller_id);
        }
    } catch (error) {
        showCustomAlert("Błąd połączenia z serwerem.")
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

// Small helper for simulating latency
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Helper: apply manual override to UI elements for a controller
function applyManualOverride(controllerId, overrideTemp) {
    // Update picker and arrows in details
    const carousel = document.getElementById(`picker-carousel-${controllerId}`);
    if (carousel) {
        updatePickerPosition(carousel, overrideTemp);
        updatePickerArrowsVisibility(`picker-carousel-${controllerId}`, overrideTemp);
    }

    // Update card
    const card = document.getElementById(`card-${controllerId}`);
    if (card) {
        const cardTargetTemp = card.querySelectorAll('.controller-card-temp strong')[1];
        if (cardTargetTemp) {
            cardTargetTemp.textContent = `${overrideTemp.toFixed(1)}°C`;
        }

        const cardCurrTempStrong = card.querySelectorAll('.controller-card-temp strong')[0];
        const currTemp = cardCurrTempStrong ? parseFloat(cardCurrTempStrong.textContent) : 21.5;

        // card.className = 'controller-card';
        card.classList.remove('heating', 'cooling', 'stable');
        if (overrideTemp > currTemp) {
            card.classList.add('heating');
        } else if (overrideTemp < currTemp) {
            card.classList.add('cooling');
        } else {
            card.classList.add('stable');
        }
        if (selectedControllerId === controllerId) {
            card.classList.add('active');
        }

        const statusInfo = getStatusInfo(2, myusername);
        const statusSpan = card.querySelector('.info-small span');
        if (statusSpan) {
            statusSpan.className = statusInfo.className;
            statusSpan.textContent = `Kontrola: ${statusInfo.text}`;
        }
    }

    // Update details status class & text
    const details = document.getElementById(`controller-${controllerId}`);
    if (details) {
        const currTempEl = document.getElementById(`curr-temp-${controllerId}`);
        const currTemp = currTempEl ? parseFloat(currTempEl.textContent) : 21.5;

        details.className = 'controller-details';
        details.classList.remove('heating', 'cooling', 'stable');
        if (overrideTemp > currTemp) {
            details.classList.add('heating');
        } else if (overrideTemp < currTemp) {
            details.classList.add('cooling');
        } else {
            details.classList.add('stable');
        }

        const statusInfo = getStatusInfo(2, myusername);
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
}