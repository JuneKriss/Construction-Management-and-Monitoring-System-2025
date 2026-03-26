document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('search');
    const projectsBody = document.getElementById('projects-body');
    const modal = document.getElementById('projectDetailsModal');
    const closeButton = document.getElementById('closeModal');
    const closeModalButtons = document.querySelectorAll('.closeModal');
    const addModal = document.getElementById('addModal');
    const addButtons = document.querySelectorAll('.addbtn');
    const viewTimeframeBtn = document.getElementById('viewTimeframeBtn');
    const imageModal = document.getElementById('imageModal');
    const modalImage = document.getElementById('modalImage');
    const addResourcesForm = document.getElementById('addResourcesForm');
    const resourcesBody = document.getElementById('resources-body');
    const tableBody = document.querySelector("#personnels tbody");
    const updateModal = document.getElementById('updateModal');
    const saveBtn = document.querySelector(".save_btn");
    const unmarkBtn = document.querySelector(".unmark_btn");

    // Search functionality
    searchInput.addEventListener('input', () => {
        const query = searchInput.value;

        fetch('/foreman_project/foreman-search-projects/?query=' + encodeURIComponent(query), {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.projects && data.projects.length > 0) {
                projectsBody.innerHTML = '';
                data.projects.forEach(project => {
                    const row = `
                        <tr>
                            <td>${project.project_name}</td>
                            <td>${project.client}</td>
                            <td>${project.due_date}</td>
                            <td>
                                <div class="progress">
                                    <div class="progress-fill" style="width: ${project.project_percent}%; color: white;">
                                        <span class="progress-percentage">${project.project_percent}%</span>
                                    </div>
                                </div>
                            </td>
                            <td>${project.project_status}</td>
                            <td><button type="button" class="viewModal" data-id="${project.id}">View</button></td>
                        </tr>
                    `;
                    projectsBody.insertAdjacentHTML('beforeend', row);
                });

                attachViewModalListeners();
            } else {
                console.log('No projects found');
                projectsBody.innerHTML = '<tr><td colspan="6">No projects found.</td></tr>';
            }
        })        
        .catch(error => console.error('Error:', error));
    });
    // Search functionality

    // Set Status Indicator's colors
    const getProjectStatus = (projectStatus, projectPercent) => {
        let statusText = "";
        let statusClass = "";

        if (projectStatus === "Ongoing") {
            if (projectPercent === 0) {
                statusText = "Not Started";
                statusClass = "not_started";
            } else if (projectPercent > 0 && projectPercent <= 25) {
                statusText = "Initial Phase";
                statusClass = "initial";
            } else if (projectPercent > 25 && projectPercent <= 50) {
                statusText = "In Progress";
                statusClass = "in_progress";
            } else if (projectPercent > 50 && projectPercent <= 75) {
                statusText = "Midway";
                statusClass = "midway";
            } else if (projectPercent > 75 && projectPercent < 100) {
                statusText = "Near Completion";
                statusClass = "near_complete";
            } else if (projectPercent === 100) {
                statusText = "Completed";
                statusClass = "completed";
            }
        } else if (projectStatus === "Onhold") {
            statusText = "Onhold";
            statusClass = "onhold";
        } else if (projectStatus === "Not Started") {
            statusText = "Not Started";
            statusClass = "not_started";
        } else {
            statusText = projectStatus;
        }

        return { statusText, statusClass };
    }
    // Set Status Indicator's colors

    //Set Personnels Names
    const getName = (firstName, lastName) => {
        if (firstName !== 'Not Provided' && lastName === 'Not Provided') {
            return firstName;
        }
        if (lastName !== 'Not Provided' && firstName === 'Not Provided') {
            return lastName;
        }
        if (firstName === 'Not Provided' && lastName === 'Not Provided') {
            return 'Names Not Provided';
        }
        return firstName + ' ' + lastName; 
    }
    //Set Personnels Names

    //Display Project Details Modal
    function attachViewModalListeners() {
        document.querySelectorAll('.viewModal').forEach(button => {
            button.addEventListener('click', function () {
                const projectId = this.dataset.id;
                saveBtn.setAttribute("data-id", projectId);
                unmarkBtn.setAttribute("data-id", projectId);
                const actionUrl = `/foreman_project/add-resource/${projectId}/`;
                addResourcesForm.action = actionUrl;

                fetch(`/foreman_project/get-project-details/${projectId}/`)
                    .then(response => response.json())
                    .then(data => {
                        const progressFill = document.getElementById("modal-progress-fill");
                        const progressPercentage = document.getElementById("modal-progress-percentage");

                        document.querySelector(".head_title h2").innerText = `${data.project_name} - ${data.client}`;

                        const statusCircle = document.getElementById('modal-status-circle');
                        const statusTextElement = document.getElementById('modal-status-text');
                        
                        const { statusText, statusClass } = getProjectStatus(data.project_status, data.progress);

                        statusCircle.className = `status-circle status-${statusClass}`;
                        statusTextElement.className = `${statusClass}-text`;
                        statusTextElement.textContent = statusText;

                        progressFill.style.width = `${data.progress}%`;
                        progressPercentage.textContent = `${data.progress}%`;

                        const addResourceButton = document.getElementById('addResourceButton');
                        const saveFinishedDiv = document.querySelector(".save_finished");

                        const taskBody = document.getElementById("taskBody");

                        if (data.progress === 100) {
                            addResourceButton.style.display = 'none';
                           if (data.finalization_status === "Completed") {
                                saveFinishedDiv.style.display = "none"; // Hide buttons
                            } else {
                                saveFinishedDiv.style.display = "block"; // Show buttons

                                if (data.isFinished) {
                                    saveBtn.style.display = "none"; // Hide "Mark as Finished"
                                    unmarkBtn.style.display = "block"; // Show "Remove Mark"
                                } else {
                                    saveBtn.style.display = "block"; // Show "Mark as Finished"
                                    unmarkBtn.style.display = "none"; // Hide "Remove Mark"
                                }
                            }
                        } else {
                            addResourceButton.style.display = 'block';
                            saveFinishedDiv.style.display = "none";
                        }

                        document.getElementById("budget").value = data.budget;
                        document.getElementById("description").value = data.description;
                        document.getElementById("start").value = data.start_date;
                        document.getElementById("due").value = data.due_date;

                        document.getElementById("viewTimeframeBtn").setAttribute("data-contract-url", data.contract_url);
                        document.getElementById("downloadLink").setAttribute("href", data.contract_url);

                        tableBody.innerHTML = "";

                        if (data.project_manager) {
                            const managerRow = document.createElement('tr');
                            const managerName = getName(data.project_manager.first_name, data.project_manager.last_name);
                            managerRow.innerHTML = `
                                <td>${managerName}</td>
                                <td>${data.project_manager.role}</td>
                            `;
                            tableBody.appendChild(managerRow);
                        }
                        
                        if (data.foreman) {
                            const foremanRow = document.createElement('tr');
                            const foremanName = getName(data.foreman.first_name, data.foreman.last_name);
                            foremanRow.innerHTML = `
                                <td>${foremanName}</td>
                                <td>${data.foreman.role}</td>
                            `;
                            tableBody.appendChild(foremanRow);
                        }else{
                            const foremanRow = document.createElement('tr');
                            foremanRow.innerHTML = `
                                <td colspan="2">No foreman currently assigned to this project</td>
                            `;
                            tableBody.appendChild(foremanRow);
                        }
                        
                        if (data.workers && data.workers.length > 0) {
                            data.workers.forEach(worker => {
                                const workerRow = document.createElement('tr');
                                const workerName = getName(worker.first_name, worker.last_name);
                                workerRow.innerHTML = `
                                    <td>${workerName} (${worker.account})</td>
                                    <td>${worker.role}</td>
                                `;
                                tableBody.appendChild(workerRow);
                            });
                        }else{
                            const workerRow = document.createElement('tr');
                            workerRow.innerHTML = `
                                <td colspan="2">No worker currently assigned to this project</td>
                            `;
                            tableBody.appendChild(workerRow);
                        }
                        
                        taskBody.innerHTML = "";
                        if (data.tasks && data.tasks.length > 0) {
                            data.tasks.forEach(task => {
                                const row = document.createElement("tr");
                                row.innerHTML = `
                                    <td>${task.task_name}</td>
                                    <td>${task.date_start}</td>
                                    <td>${task.deadline}</td>
                                    <td>${task.progress}%</td>
                                    <td>${task.percent_from_project}%</td>
                                `;
                                taskBody.appendChild(row);
                            });
                        } else {
                            const emptyRow = document.createElement("tr");
                            emptyRow.innerHTML = `<td colspan="5">No tasks for this project</td>`;
                            taskBody.appendChild(emptyRow);
                        }

                        resourcesBody.innerHTML = "";
                        if (data.resources && data.resources.length > 0) {
                            data.resources.forEach(resource => {
                                const resourceRow = document.createElement('tr');
                                resourceRow.innerHTML = `
                                    <td>${resource.name}</td>
                                    <td>${resource.quantity}</td>
                                    <td>${resource.resource_type_display}</td>
                                    <td>${resource.resource_subtype}</td>
                                    <td>₱ ${resource.cost}</td>
                                    <td>${resource.cost_type}</td>
                                    <td>${resource.added_by === 'PM' ? 'None' : `
                                        <button type="button" 
                                                class="updatebtn" 
                                                data-resource-id="${resource.resource_id}" 
                                                data-resource-name="${resource.name}" 
                                                data-resource-quantity="${resource.quantity}" 
                                                data-resource-type="${resource.resource_type}" 
                                                data-resource-subtype="${resource.resource_subtype}" 
                                                data-resource-cost="${resource.cost}" 
                                                data-resource-cost-type="${resource.cost_type}">
                                            Update
                                        </button>`}
                                    </td>
                                `;
                                resourcesBody.appendChild(resourceRow);
                            });
                        } else {
                            const resourceRow = document.createElement('tr');
                            resourceRow.innerHTML = `
                                <td colspan="6">No resources currently for this project</td>
                            `;
                            resourcesBody.appendChild(resourceRow);
                        }

                        modal.style.display = 'flex';
                    })
                    .catch(error => console.error('Error fetching project details:', error));
            });
        });

        viewTimeframeBtn.addEventListener('click', () => {
            const contractUrl = viewTimeframeBtn.getAttribute('data-contract-url');
            if (contractUrl) {
                modalImage.src = contractUrl;
                imageModal.style.display = 'flex';
            } else {
                alert('No contract available for this project.');
            }
        });
    }
    //Display Project Details Modal

    //Other Modal Functions
    closeButton.addEventListener('click', () => {
        modal.style.display = 'none';
    });

    window.addEventListener('click', (event) => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
        if (event.target === imageModal) {
            imageModal.style.display = 'none';
        }
        if (event.target === addModal) {
            addModal.style.display = 'none';
            projectDetailsModal.style.display = 'flex';
        }
        if (event.target === updateModal) {
            updateModal.style.display = 'none';
        }
    });

    function openAddModal() {
        addModal.style.display = 'flex'; 
        modal.style.display = 'none'; 
    }

    if (addButtons) {
        addButtons.forEach(button => {
            button.addEventListener('click', (event) => {
                event.preventDefault();
                openAddModal();
            });
        });
    }

    closeModalButtons.forEach(button => {
        button.addEventListener('click', () => {
            addModal.style.display = 'none'; 
            
            if (updateModal) {
                updateModal.style.display = 'none';
            }
    
            modal.style.display = 'flex';
        });
    });
    //Other Modal Functions
    attachViewModalListeners();

    //Handle Add Resource Form Submission
    addResourcesForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const formData = new FormData(addResourcesForm);
    
        try {
            const response = await fetch(addResourcesForm.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
            });
    
            const data = await response.json();
    
            if (data.redirect) {
                Swal.fire({
                    position: "top-end",
                    icon: "success",
                    title: data.message,
                    showConfirmButton: false,
                    timer: 1500,
                }).then(() => {
                    location.reload();
                });
            } else {
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: data.message || 'An error occurred.',
                });
            }
        } catch (error) {
            console.error('Error:', error);
            Swal.fire({
                icon: 'error',
                title: 'An error occurred',
                text: 'Please try again.',
            });
        }
    });  
    //Handle Add Resource Form Submission


    document.addEventListener('click', async function (event) {
        //Send Data to Update Modal
        if (event.target.classList.contains('updatebtn')) {
            const button = event.target;
            const resourceId = button.getAttribute('data-resource-id');
            const resourceName = button.getAttribute('data-resource-name');
            const resourceQuantity = button.getAttribute('data-resource-quantity');
            const resourceType = button.getAttribute('data-resource-type');
            const resourceSubtype = button.getAttribute('data-resource-subtype');
            const resourceCost = button.getAttribute('data-resource-cost');
            const resourceCostType = button.getAttribute('data-resource-cost-type');

            document.getElementById('resource_id').value = resourceId;
            document.getElementById('updateResource_name').value = resourceName;
            document.getElementById('updateQuantity').value = resourceQuantity;
            document.getElementById('updateCost').value = resourceCost;
            document.querySelector('select[name="updateCostType"]').value = resourceCostType;

            document.getElementById('updateType').value = resourceType;
            populateSubtypes(document.getElementById('updateType'), document.getElementById('updateSubType'), resourceSubtype);

            updateModal.style.display = 'flex';
        }
        //Send Data to Update Modal

        //Handle Delete Resource
        if (event.target.classList.contains('delete')) {
            const resourceId = document.getElementById('resource_id').value;
    
            if (!resourceId) {
                Swal.fire({
                    icon: "error",
                    title: "Error",
                    text: "No resource selected to delete.",
                });
                return;
            }
            
            Swal.fire({
                title: "Are you sure?",
                text: "You won't be able to revert this!",
                icon: "warning",
                showCancelButton: true,
                confirmButtonColor: "#d33",
                cancelButtonColor: "#3085d6",
                confirmButtonText: "Yes, delete it!",
            }).then(async (result) => {
                if (result.isConfirmed) {
                    try {
                        const response = await fetch('/foreman_project/foreman-delete-resource/', {
                            method: "POST",
                            headers: {
                                "Content-Type": "application/json",
                                "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value,
                            },
                            body: JSON.stringify({ resource_id: resourceId }),
                        });
    
                        const data = await response.json();
    
                        if (data.status === "success") {
                            Swal.fire({
                                position: "top-end",
                                icon: "success",
                                title: "Resource deleted successfully!",
                                showConfirmButton: false,
                                timer: 1500,
                            }).then(() => {
                                location.reload();
                            });
                        } else {
                            Swal.fire({
                                icon: "error",
                                title: "Error",
                                text: data.message || "Unable to delete the resource.",
                            });
                        }
                    } catch (error) {
                        console.error("Error:", error);
                        Swal.fire({
                            icon: "error",
                            title: "An error occurred",
                            text: "Please try again.",
                        });
                    }
                }
            });
        }
        //Handle Delete Resource
    });

    //Handle Update Form Submission
    document.getElementById('updateResourceForm').addEventListener('submit', async function (event) {
        event.preventDefault();
    
        const formData = new FormData(this);
    
        try {
            const response = await fetch('/foreman_project/foreman-update-resource/', {
                method: 'POST',
                body: formData,
            });
            
            const data = await response.json();
            if (data.status === "success") {
                Swal.fire({
                    position: "top-end",
                    icon: "success",
                    title: data.message,
                    showConfirmButton: false,
                    timer: 1500,
                }).then(() => {
                    location.reload();
                });
            } else {
                Swal.fire({
                    icon: "error",
                    title: "Error",
                    text: data.message || "An error occurred.",
                });
            }
        } catch (error) {
            console.error("Error:", error);
            Swal.fire({
                icon: "error",
                title: "An error occurred",
                text: "Please try again.",
            });
        }
    });
    //Handle Update Form Submission

    //Handle SubType Select Options
    const resourceSubtypes = {
        material: ['Concrete Products', 'Masonry', 'Metal', 'Wood', 'Plastics', 'Glass', 'Aggregates', 'Paints & Finishes'],
        supply: ['Adhesives', 'Safety Supplies', 'Electrical Supplies', 'Plumbing Supplies', 'Fasteners', 'Consumables'],
        equipment: ['Heavy Equipment', 'Power Tools', 'Hand Tools', 'Surveying Equipment', 'Lifting Equipment', 'Concrete Equipment', 'Earth Moving Equipment', 'Scaffolding'],
    };

    const populateSubtypes = (typeSelect, subTypeSelect, selectedSubType) => {
        const selectedType = typeSelect.value;
        subTypeSelect.innerHTML = '<option value="" disabled selected>Resource Subtype</option>';
    
        if (resourceSubtypes[selectedType]) {
            resourceSubtypes[selectedType].forEach(subType => {
                const option = document.createElement('option');
                option.value = subType;
                option.textContent = subType;
                if (subType === selectedSubType) {
                    option.selected = true;
                }
                subTypeSelect.appendChild(option);
            });
        }
    };
    
    document.getElementById('updateType').addEventListener('change', function() {
        populateSubtypes(this, document.getElementById('updateSubType'));
    });
    
    document.getElementById('type').addEventListener('change', function() {
        populateSubtypes(this, document.getElementById('subType'));
    });
    //Handle SubType Select Options

    //Handle Save Button
   if (saveBtn) {
        saveBtn.addEventListener("click", function () {
            console.log(this.dataset.id);
            const projectId = this.dataset.id; // Ensure the button has data-id set

            Swal.fire({
                title: "Are you sure?",
                text: "Do you want to mark this project as finished?",
                icon: "warning",
                showCancelButton: true,
                confirmButtonColor: "#3085d6",
                cancelButtonColor: "#d33",
                confirmButtonText: "Yes, mark it!",
                cancelButtonText: "Cancel"
            }).then((result) => {
                if (result.isConfirmed) {
                    updateProjectStatus(true, projectId);
                }
            });
        });
    }

    if (unmarkBtn) {
        unmarkBtn.addEventListener("click", function () {
            console.log(this.dataset.id);
            const projectId = this.dataset.id;

            Swal.fire({
                title: "Are you sure?",
                text: "Do you want to remove the finished mark from this project?",
                icon: "warning",
                showCancelButton: true,
                confirmButtonColor: "#3085d6",
                cancelButtonColor: "#d33",
                confirmButtonText: "Yes, remove it!",
                cancelButtonText: "Cancel"
            }).then((result) => {
                if (result.isConfirmed) {
                    updateProjectStatus(false, projectId);
                }
            });
        });
    }

    function updateProjectStatus(isFinished, projectId) {
        fetch(`/foreman_project/mark-finished/${projectId}/`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCSRFToken(),
            },
            body: JSON.stringify({ isFinished: isFinished }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                Swal.fire({
                    title: "Success!",
                    text: isFinished
                        ? "Project marked as finished successfully!"
                        : "Project unmarked as finished!",
                    icon: "success",
                    confirmButtonColor: "#3085d6"
                }).then(() => {
                    window.location.reload(); // Refresh the page or update the UI accordingly
                });
            } else {
                Swal.fire({
                    title: "Error!",
                    text: isFinished
                        ? "Failed to mark project as finished."
                        : "Failed to remove finished mark.",
                    icon: "error",
                    confirmButtonColor: "#d33"
                });
            }
        })
        .catch(error => {
            console.error("Error:", error);
            Swal.fire({
                title: "Error!",
                text: "An unexpected error occurred.",
                icon: "error",
                confirmButtonColor: "#d33"
            });
        });
    }

    // Function to get CSRF token
    function getCSRFToken() {
        const cookieValue = document.cookie
            .split("; ")
            .find(row => row.startsWith("csrftoken="))
            ?.split("=")[1];
        return cookieValue || "";
    }
});
