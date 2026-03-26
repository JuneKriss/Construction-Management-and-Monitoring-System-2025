document.addEventListener('DOMContentLoaded', function() {

    ///////////////////////////////////////////////////////////////////////////////////////////////////////////////// JS calendar
    const calendarEl = document.getElementById('calendar');

    const tasksJsonAdjusted = tasksJson.map(event => {
        if (event.end) {
            let endDate = new Date(event.end);
            endDate.setDate(endDate.getDate() + 1);
            event.end = endDate.toISOString().split('T')[0];
        }
        return event;
    });

    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        events: tasksJsonAdjusted,
        eventClick: function(info) {
            const eventModal = document.getElementById('eventModal');
            eventModal.style.display = 'flex';
        
            const event = info.event;
            const modalTitle = document.getElementById('eventModalTitle');
            const modalStart = document.getElementById('eventModalStart');
            const modalEnd = document.getElementById('eventModalEnd');
            const modalDescription = document.getElementById('eventModalDescription');
            const workersTableBody = document.getElementById('task_details-body');
            const progressFill = document.getElementById('progressFill');
            const progressPercentage = document.getElementById('progressPercentage');
            const detailsTaskName = document.getElementById('eventTaskName');
            const detailsTaskPercentage = document.getElementById('eventModalTaskPercentage');
            const removedWorkersInput = document.getElementById('removed_workers');
            const taskScheduleId = document.getElementById('task_id');

            modalTitle.innerHTML = event.title;
            detailsTaskName.value = event.extendedProps.task_name;
            detailsTaskPercentage.value = event.extendedProps.percent_from;
            modalStart.value = event.start.toLocaleDateString('en-CA');
            modalEnd.value = event.end ? event.end.toISOString().split('T')[0] : '';
            modalDescription.innerHTML = event.extendedProps.description || 'No description';
            taskScheduleId.value = event.extendedProps.task_id;

            const progress = event.extendedProps.progress
            progressFill.style.width = `${progress}%`;
            progressPercentage.textContent = `${progress}%`;
        
            workersTableBody.innerHTML = ''; 

            const pmFName = event.extendedProps.project_manager_fname;
            const pmLName = event.extendedProps.project_manager_lname;

            let displayPmName = '';

            if (pmFName !== 'Not Provided' && pmLName === 'Not Provided') {
                displayPmName = pmFName;
            } 
            else if (pmLName !== 'Not Provided' && pmFName === 'Not Provided') {
                displayPmName = pmLName;
            } 
            else if (pmFName === 'Not Provided' && pmLName === 'Not Provided') {
                displayPmName = 'Names Not Provided';
            } 
            else {
                displayPmName = `${pmFName} ${pmLName}`;
            }

            const pmRow = document.createElement('tr');
            pmRow.innerHTML = `
                <td>${displayPmName}</td>
                <td>Project Manager</td>
                <td>None</td>
            `;

            workersTableBody.appendChild(pmRow);
        
            event.extendedProps.workers.forEach(worker => {
                const workerFName = worker.Fname;
                const workerLName = worker.Lname;
                const workerRole = worker.role;
                const workerId = worker.worker_id;

                let displayWorkerName = '';
                
                if (workerFName !== 'Not Provided' && workerLName === 'Not Provided') {
                    displayWorkerName = workerFName;
                } else if (workerLName !== 'Not Provided' && workerFName === 'Not Provided') {
                    displayWorkerName = workerLName;
                } else if (workerFName === 'Not Provided' && workerLName === 'Not Provided') {
                    displayWorkerName = 'Names Not Provided';
                } else {
                    displayWorkerName = `${workerFName} ${workerLName}`;
                }

                const row = document.createElement('tr');
                row.dataset.workerId = workerId;
                row.innerHTML = `
                    <td>${displayWorkerName}</td>
                    <td>${workerRole}</td>
                    <td><button class="removeWorkerBtn" type="button">Remove</button></td>
                `;

                const removeBtn = row.querySelector('.removeWorkerBtn');
                removeBtn.addEventListener('click', () => {
                    row.classList.toggle('marked-for-removal');
                    if (row.classList.contains('marked-for-removal')) {
                        removeBtn.textContent = "Undo";
                        removeBtn.classList.add("undoBtn");
                        addWorkerToRemovalList(row.dataset.workerId);
                    } else {
                        removeBtn.textContent = "Remove";
                        removeBtn.classList.remove("undoBtn");
                        removeWorkerFromRemovalList(row.dataset.workerId);
                    }
                });

                workersTableBody.appendChild(row);

                const addWorkerToRemovalList = (workerId) => {
                    let removedWorkers = removedWorkersInput.value ? removedWorkersInput.value.split(',') : [];
                    removedWorkers.push(workerId);
                    removedWorkersInput.value = removedWorkers.join(',');
                    console.log(removedWorkers)
                }
                
                const removeWorkerFromRemovalList = (workerId) => {
                    let removedWorkers = removedWorkersInput.value ? removedWorkersInput.value.split(',') : [];
                    removedWorkers = removedWorkers.filter(id => id !== workerId);
                    removedWorkersInput.value = removedWorkers.join(',');
                    console.log(removedWorkers)
                }
            });
        }
    });

    calendar.render();

    document.getElementById('projects').addEventListener('change', function() {
        const selectedProjectId = this.value;
    
        const filteredTasks = tasksJsonAdjusted.filter(task => {
            return selectedProjectId === "" || task.project_id == selectedProjectId;
        });
    
        // Clear existing events and add filtered events
        calendar.removeAllEvents();
        calendar.addEventSource(filteredTasks);
    });
    /////////////////////////////////////////////////////////////////////////////////////////////////////////////////

    ///////////////////////////////////////////////////////////////////////////////////////////////////////////////// Modal Handling
    const modals = document.querySelectorAll('.taskModal, .eventModal');
    const modal = document.getElementById('taskModal');
    const btn = document.getElementById('openModal');
    const closeBtns = document.querySelectorAll('.closeModal');

    closeBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const modal = btn.closest('.taskModal, .eventModal');
            if (modal) {
                modal.style.display = 'none';
            } else {
                console.error('No modal found for this close button.');
            }
        });
    });

    if (btn) {
        btn.onclick = function(event) {
            event.preventDefault();
            modal.style.display = 'flex';
        };
    }

    window.onclick = function(event) {
        modals.forEach(modal => {
            if (event.target === modal) {
                modal.style.display = 'none';
            }
        });
    };

    
    modals.forEach(modal => {
        const addSelectBtn = modal.querySelector('.addSelect');
        const removeSelectBtn = modal.querySelector('.removeSelect');
        const assigneeContainer = modal.querySelector('.assigneeContainer');

        function toggleRemoveButton() {
            const selectElements = assigneeContainer.querySelectorAll('select');
            removeSelectBtn.style.display = selectElements.length > 1 ? 'flex' : 'none';
        }

        addSelectBtn.addEventListener('click', () => {
            const originalSelect = assigneeContainer.querySelector('select');
            const newSelect = originalSelect.cloneNode(true);
            newSelect.value = ''; 
            assigneeContainer.appendChild(newSelect);
            toggleRemoveButton();
        });

        removeSelectBtn.addEventListener('click', () => {
            const selectElements = assigneeContainer.querySelectorAll('select');
            if (selectElements.length > 1) {
                assigneeContainer.removeChild(selectElements[selectElements.length - 1]);
                toggleRemoveButton();
            }
        });

        toggleRemoveButton();
    });
    /////////////////////////////////////////////////////////////////////////////////////////////////////////////////

    ///////////////////////////////////////////////////////////////////////////////////////////////////////////////// Add task form alert
    const form = document.getElementById('taskForm');
    form.addEventListener('submit', function(event) {
        event.preventDefault();

        const taskName = document.getElementById('taskName').value;
        const taskStart = document.getElementById('taskStart').value;
        const taskEnd = document.getElementById('taskEnd').value;

        const startDate = new Date(taskStart);
        const endDate = new Date(taskEnd);

        if (endDate < startDate) {
            Swal.fire({
                icon: "error",
                title: "Invalid Dates",
                html: `<p style="font-size: 16px; color: #555;">The deadline cannot be before the start date. Please correct the dates.</p>`,
                showConfirmButton: true
            });
            return;
        }

        Swal.fire({
            position: "top-end",
            icon: "success",
            title: '<h2 style="font-size: 24px; margin: 0;">Task Scheduled Successfully</h2>',
            html: `<p style="font-size: 16px; color: #555; margin-top: 8px;">Task "${taskName}" has been scheduled.</p>`,
            showConfirmButton: false,
            timer: 1500
        }).then(() => {
            form.submit(); 
        });
    });
    /////////////////////////////////////////////////////////////////////////////////////////////////////////////////

    ///////////////////////////////////////////////////////////////////////////////////////////////////////////////// Check Task Percent From Field if valid
    const projectSelect = document.getElementById('project');
    const taskPercentageInput = document.getElementById('taskPercentage');
    const errorMessage = document.getElementById('errorMessage');

    async function fetchProjectPercentage(projectId) {
        try {
            const response = await fetch(`/foreman_project/add-taskSchedule/get_project_percentage/${projectId}/`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            return data.total_percentage;
        } catch (error) {
            console.error("Failed to fetch project percentage:", error);
            return 0;
        }
    }

    async function validatePercentage() {
        const projectId = projectSelect.value;
        const newTaskPercentage = parseInt(taskPercentageInput.value, 10) || 0;

        if (!projectId) return;

        const currentPercentage = await fetchProjectPercentage(projectId);
        const totalPercentage = currentPercentage + newTaskPercentage;

        if (totalPercentage > 100) {
            errorMessage.style.display = 'block';
            errorMessage.textContent = "Error: Total project percentage exceeds 100%.";
            taskPercentageInput.setCustomValidity("Total percentage exceeds 100%");
        } else {
            errorMessage.textContent = "";
            taskPercentageInput.setCustomValidity("");
        }
    }
    projectSelect.addEventListener('change', validatePercentage);
    taskPercentageInput.addEventListener('input', validatePercentage);
    /////////////////////////////////////////////////////////////////////////////////////////////////////////////////

    ///////////////////////////////////////////////////////////////////////////////////////////////////////////////// Set Minimum Dates for Date Field
    
        // Get today’s date in the proper format
    const today = new Date().toLocaleDateString('en-CA');

    // Only apply min dates in taskModal
    const taskModalStartDates = document.querySelectorAll("#taskModal .start_date");
    const taskModalEndDates = document.querySelectorAll("#taskModal .end_date");

    taskModalStartDates.forEach(startDateInput => {
        if (!startDateInput.value) {
            startDateInput.setAttribute("min", today);
        } else {
            startDateInput.removeAttribute("min");
        }

        const correspondingEndDate = startDateInput.closest('.task_form_group').querySelector(".end_date");
        startDateInput.addEventListener("change", function () {
            if (correspondingEndDate) {
                correspondingEndDate.setAttribute("min", startDateInput.value);
            }
        });
    });

    taskModalEndDates.forEach(endDateInput => {
        if (!endDateInput.value) {
            endDateInput.setAttribute("min", today);
        } else {
            endDateInput.removeAttribute("min");
        }
    });

    /////////////////////////////////////////////////////////////////////////////////////////////////////////////////
});
