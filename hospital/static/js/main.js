/**
 * Medicare Hospital & Appointment Management Portal
 * Client-Side Logic & Dynamic Interactions
 */

document.addEventListener('DOMContentLoaded', function () {
    initDoctorFiltering();
    initDoctorSearch();
    initSlotPicker();
    initStatusUpdateModals();
});

/**
 * 1. JavaScript Doctor Filtering by Department
 * Supports Cardiology, Pediatrics, Orthopedics, Neurology, General Medicine, and All
 */
function initDoctorFiltering() {
    const filterButtons = document.querySelectorAll('.dept-filter-btn');
    const doctorCards = document.querySelectorAll('.doctor-card-wrapper');
    const noResultsMsg = document.getElementById('no-doctors-found');

    if (!filterButtons.length || !doctorCards.length) return;

    filterButtons.forEach(btn => {
        btn.addEventListener('click', function () {
            // Update active button state
            filterButtons.forEach(b => b.classList.remove('active'));
            this.classList.add('active');

            const selectedDept = this.getAttribute('data-dept');
            let visibleCount = 0;

            doctorCards.forEach(card => {
                const cardDept = card.getAttribute('data-dept');
                if (selectedDept === 'All' || cardDept === selectedDept) {
                    card.style.display = '';
                    card.classList.add('animate-fade-in');
                    visibleCount++;
                } else {
                    card.style.display = 'none';
                    card.classList.remove('animate-fade-in');
                }
            });

            if (noResultsMsg) {
                noResultsMsg.style.display = (visibleCount === 0) ? 'block' : 'none';
            }
        });
    });
}

/**
 * Live search filter across doctor names and specializations
 */
function initDoctorSearch() {
    const searchInput = document.getElementById('doctorSearchInput');
    const doctorCards = document.querySelectorAll('.doctor-card-wrapper');
    const noResultsMsg = document.getElementById('no-doctors-found');

    if (!searchInput || !doctorCards.length) return;

    searchInput.addEventListener('input', function () {
        const query = this.value.toLowerCase().trim();
        let visibleCount = 0;

        // Reset active filter button to All during global text search
        if (query.length > 0) {
            document.querySelectorAll('.dept-filter-btn').forEach(b => {
                if (b.getAttribute('data-dept') === 'All') b.classList.add('active');
                else b.classList.remove('active');
            });
        }

        doctorCards.forEach(card => {
            const name = card.getAttribute('data-name')?.toLowerCase() || '';
            const spec = card.getAttribute('data-spec')?.toLowerCase() || '';
            const dept = card.getAttribute('data-dept')?.toLowerCase() || '';

            if (name.includes(query) || spec.includes(query) || dept.includes(query)) {
                card.style.display = '';
                visibleCount++;
            } else {
                card.style.display = 'none';
            }
        });

        if (noResultsMsg) {
            noResultsMsg.style.display = (visibleCount === 0) ? 'block' : 'none';
        }
    });
}

/**
 * 2. Interactive Appointment Date & Time Slot Selector
 * Dynamically checks booked vs available slots from server via AJAX
 */
function initSlotPicker() {
    const doctorSelect = document.getElementById('doctor_select');
    const dateInput = document.getElementById('appointment_date');
    const slotContainer = document.getElementById('slot-selection-container');
    const timeSlotSelect = document.getElementById('time_slot_select');
    const slotNotice = document.getElementById('slot-schedule-notice');
    const slotLoader = document.getElementById('slot-loading-spinner');

    if (!doctorSelect || !dateInput || !slotContainer) return;

    function fetchAndRenderSlots() {
        const doctorId = doctorSelect.value;
        const dateValue = dateInput.value;

        if (!doctorId || !dateValue) {
            slotContainer.innerHTML = '<div class="text-muted p-3 bg-light rounded text-center"><i class="bi bi-calendar-event me-2"></i>Please select both a specialist doctor and appointment date to view available time slots.</div>';
            if (slotNotice) slotNotice.style.display = 'none';
            return;
        }

        if (slotLoader) slotLoader.style.display = 'inline-block';
        slotContainer.innerHTML = '<div class="text-center py-4 text-muted"><div class="spinner-border spinner-border-sm text-primary me-2"></div> Checking live slot availability...</div>';

        fetch(`/api/slots/?doctor_id=${encodeURIComponent(doctorId)}&date=${encodeURIComponent(dateValue)}`)
            .then(res => {
                if (!res.ok) throw new Error('Network response was not ok');
                return res.json();
            })
            .then(data => {
                if (slotLoader) slotLoader.style.display = 'none';

                // Working day notice
                if (slotNotice) {
                    if (!data.is_working_day) {
                        slotNotice.className = 'alert alert-warning mb-3 py-2 px-3 small';
                        slotNotice.innerHTML = `<i class="bi bi-exclamation-triangle-fill me-2"></i><strong>Note:</strong> ${data.doctor_name} is normally scheduled on: <strong>${data.available_days_raw}</strong>. You may still book on ${data.day_of_week} if confirmed with the clinic.`;
                        slotNotice.style.display = 'block';
                    } else {
                        slotNotice.className = 'alert alert-success mb-3 py-2 px-3 small';
                        slotNotice.innerHTML = `<i class="bi bi-check-circle-fill me-2"></i>${data.doctor_name} is available on ${data.day_of_week}s. (${data.available_count} of ${data.slots.length} slots free)`;
                        slotNotice.style.display = 'block';
                    }
                }

                // Render slots grid
                renderSlotsGrid(data.slots);
            })
            .catch(err => {
                console.error('Error fetching slots:', err);
                if (slotLoader) slotLoader.style.display = 'none';
                slotContainer.innerHTML = '<div class="alert alert-danger py-2 px-3 small">Unable to retrieve live slots. Please choose directly from the dropdown below.</div>';
            });
    }

    function renderSlotsGrid(slots) {
        slotContainer.innerHTML = '';
        const grid = document.createElement('div');
        grid.className = 'slots-grid';

        const currentValue = timeSlotSelect ? timeSlotSelect.value : '';

        slots.forEach(item => {
            const pill = document.createElement('div');
            pill.className = 'slot-pill';
            pill.setAttribute('data-slot', item.slot);

            if (item.is_booked) {
                pill.classList.add('booked');
                pill.title = 'This slot has already been booked';
                pill.innerHTML = `<div><i class="bi bi-lock-fill me-1"></i>${item.label}</div>`;
            } else {
                pill.innerHTML = `<div><i class="bi bi-clock me-1"></i>${item.label}</div><small class="text-success fw-bold d-block mt-1">Available</small>`;

                if (currentValue === item.slot) {
                    pill.classList.add('selected');
                }

                pill.addEventListener('click', function () {
                    grid.querySelectorAll('.slot-pill').forEach(p => p.classList.remove('selected'));
                    this.classList.add('selected');

                    // Synchronize the underlying Django form select
                    if (timeSlotSelect) {
                        timeSlotSelect.value = item.slot;
                        timeSlotSelect.dispatchEvent(new Event('change'));
                    }
                });
            }

            grid.appendChild(pill);
        });

        slotContainer.appendChild(grid);
    }

    // Trigger on change
    doctorSelect.addEventListener('change', fetchAndRenderSlots);
    dateInput.addEventListener('change', fetchAndRenderSlots);

    // Initial check if values are prepopulated
    if (doctorSelect.value && dateInput.value) {
        fetchAndRenderSlots();
    }
}

/**
 * 3. Admin / Staff Status Update Modal helper
 */
function initStatusUpdateModals() {
    const updateButtons = document.querySelectorAll('.btn-open-status-modal');
    if (!updateButtons.length) return;

    updateButtons.forEach(btn => {
        btn.addEventListener('click', function () {
            const aptId = this.getAttribute('data-apt-id');
            const currentStatus = this.getAttribute('data-apt-status');
            const aptCode = this.getAttribute('data-apt-code');
            const patientName = this.getAttribute('data-patient-name');

            const modalCode = document.getElementById('modalAptCode');
            const modalPatient = document.getElementById('modalPatientName');
            const modalStatusSelect = document.getElementById('modalStatusSelect');
            const modalForm = document.getElementById('statusUpdateForm');

            if (modalCode) modalCode.textContent = aptCode;
            if (modalPatient) modalPatient.textContent = patientName;
            if (modalStatusSelect) modalStatusSelect.value = currentStatus;
            if (modalForm) modalForm.action = `/staff/update-status/${aptId}/`;
        });
    });
}
