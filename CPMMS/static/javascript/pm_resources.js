document.addEventListener('DOMContentLoaded', () => {
    const addBtns = document.querySelectorAll('.addbtn'); 
    const addModal = document.getElementById('addModal');
    const updateModal = document.getElementById('updateModal');
    const closeBtns = document.querySelectorAll('.close');
    const updateResourceForm = document.getElementById('updateResourceForm');
    const addResourcesForm = document.getElementById('addResourcesForm');
    const addAnotherBtn = document.getElementById('add_anotherBtn');;
    let isAddAnother = false;
    

    addBtns.forEach((addBtn) => {
        addBtn.addEventListener('click', () => {
            const projectName = addBtn.getAttribute('data-project-name');
            const projectId = addBtn.closest('.resources_box').dataset.projectId;

            const modalTitle = document.getElementById('addModalTitle');
            if (modalTitle) modalTitle.textContent = projectName;

            const form = document.getElementById('addResourcesForm');
            if (form) {
                form.setAttribute('action', `/project-manager-resources/add-resource/${projectId}/`);
            }

            addModal.style.display = 'flex';
        });
    });

    const updateButtons = document.querySelectorAll('.table_icon span');
    updateButtons.forEach((btn) => {
        btn.addEventListener('click', () => {
            const resourceId = btn.getAttribute('data-resource-id');
            const resourceName = btn.getAttribute('data-resource-name');
            const resourceQuantity = btn.getAttribute('data-resource-quantity');
            const resourceType = btn.getAttribute('data-resource-type');
            const resourceSubType = btn.getAttribute('data-resource-subtype'); 
            const resourceCost = btn.getAttribute('data-resource-cost');
            const resourceCostType = btn.getAttribute('data-resource-cost-type');
            const projectName = btn.getAttribute('data-project-name');

            const modalTitle = document.getElementById('updateModalTitle');
            if (modalTitle) modalTitle.textContent = projectName;

            document.querySelector('input[name="updateResource_name"]').value = resourceName;
            document.querySelector('input[name="updateQuantity"]').value = resourceQuantity;

            const updateTypeSelect = document.getElementById('updateType');
            if (updateTypeSelect) {
                updateTypeSelect.value = resourceType;
            }

            const updateSubTypeSelect = document.getElementById('updateSubType');
            if (updateSubTypeSelect) {
                populateSubtypes(updateTypeSelect, updateSubTypeSelect, resourceSubType);
            }

            document.querySelector('input[name="updateCost"]').value = resourceCost;

            const costTypeSelect = document.querySelector('select[name="updateCostType"]');
            if (costTypeSelect) {
                costTypeSelect.value = resourceCostType;
            }

            if (updateResourceForm) {
                updateResourceForm.setAttribute('action', `/project-manager-resources/update-resource/${resourceId}/`);
            }  

            const hiddenResourceIdField = document.getElementById('resource_id');
            if (hiddenResourceIdField) {
                hiddenResourceIdField.value = resourceId;
            }

            updateModal.style.display = 'flex'; 
        });
    });

    closeBtns.forEach((btn) => {
        btn.addEventListener('click', () => {
            if (addModal && addModal.style.display === 'flex') {
                addModal.style.display = 'none';
                window.location.reload(); 
            }
            if (updateModal) {
                updateModal.style.display = 'none';
            }
        });
    });

    window.addEventListener('click', (event) => {
        if (event.target === addModal) {
            addModal.style.display = 'none';
        }
        if (event.target === updateModal) {
            updateModal.style.display = 'none';
        }
    });

    addResourcesForm.addEventListener('submit', async function (event) {
        event.preventDefault();

        const addAnother = isAddAnother; 

        const formData = new FormData(this);
        const actionUrl = this.getAttribute('action');

        try {
            const response = await fetch(actionUrl, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
            });

            const data = await response.json();

            if (data.success) {
                Swal.fire({
                    position: "top-end",
                    icon: "success",
                    title: `<h2 style="font-size: 24px; margin: 0;">Resource Added Successfully</h2>`,
                    text: data.message,
                    showConfirmButton: false,
                    timer: 1500,
                }).then(() => {
                    if (!addAnother) {
                        window.location.reload();
                    } else {
                        addResourcesForm.reset();
                    }
                });
            } else {
                Swal.fire({
                    icon: "error",
                    title: "Error",
                    text: data.message,
                });
            }
        } catch (error) {
            console.error("Error:", error);
            Swal.fire({
                icon: "error",
                title: "Oops...",
                text: 'Something went wrong. Please try again later.',
            });
        }
    });

    addAnotherBtn.addEventListener('click', () => {
        isAddAnother = true;
        addResourcesForm.requestSubmit();
    });

    if (updateResourceForm) {
        updateResourceForm.addEventListener('submit', async function (event) {
            event.preventDefault();

            const formData = new FormData(this);
            const actionUrl = this.getAttribute('action');
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            try {
                const response = await fetch(actionUrl, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': csrfToken,
                    },
                });

                const data = await response.json();

                if (data.success) {
                    Swal.fire({
                        position: "top-end",
                        icon: "success",
                        title: `<h2 style="font-size: 24px; margin: 0;">Resource Updated Successfully</h2>`,
                        text: data.message,
                        showConfirmButton: false,
                        timer: 1500,
                    }).then(() => {
                        window.location.reload(); 
                    });
                } else {
                    Swal.fire({
                        icon: "error",
                        title: "Error",
                        text: data.message,
                    });
                }
            } catch (error) {
                console.error("Error:", error);
                Swal.fire({
                    icon: "error",
                    title: "Oops...",
                    text: 'Something went wrong. Please try again later.',
                });
            }
        });
    }

    const deleteBtn = updateResourceForm.querySelector('.delete');
    deleteBtn.addEventListener('click', async () => {
        const resourceId = document.getElementById('resource_id').value; 
        
        if (!resourceId) {
            Swal.fire({
                icon: 'error',
                title: 'Invalid Resource ID',
                text: 'The resource ID could not be found. Please try again.',
            });
            return;
        }
    
        const confirmed = await Swal.fire({
            title: 'Are you sure?',
            text: 'You won’t be able to undo this!',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#3085d6',
            cancelButtonColor: '#d33',
            confirmButtonText: 'Yes, delete it!',
        });
    
        if (confirmed.isConfirmed) {
            try {
                const response = await fetch(`/project-manager-resources/delete-resource/${resourceId}/`, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    },
                });

                if (!response.ok) throw new Error(await response.text());
                const data = await response.json();
                Swal.fire({
                    position: "top-end",
                    icon: data.success ? "success" : "error",
                    title: data.success ? "Deleted Successfully" : "Error",
                    text: data.message,
                    showConfirmButton: false,
                    timer: 1500,
                }).then(() => {
                    if (data.success) window.location.reload();
                });
            } catch (error) {
                console.error("Error:", error);
                Swal.fire({
                    icon: "error",
                    title: "Oops...",
                    text: "Something went wrong. Please try again later.",
                });
            }
        }
    });

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
});
