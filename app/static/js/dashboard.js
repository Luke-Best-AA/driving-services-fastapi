document.addEventListener('DOMContentLoaded', async function () {
    const userData = localStorage.getItem('user')
    const user = userData ? JSON.parse(userData) : null;
    const userId = user ? user.user_id : null;
    const policyCreate = document.getElementById('policy-create');
    const policyDetails = document.getElementById('policy-details');
    const policyUpdate = document.getElementById('policy-update');
    const policyDelete = document.getElementById('policy-delete');
    // if policy details is not null set the display to none
    if (policyCreate) {
        policyCreate.style.display = 'none';
    }
    if (policyDetails) {
        policyDetails.style.display = 'none';
    }
    if (policyUpdate) {
        policyUpdate.style.display = 'none';
    }
    if (policyDelete) {
        policyDelete.style.display = 'none';
    }
    try {
        const user = await window.getUserByMyself();
        if (user) {
            populateUserDetails(user);
        } else {
            console.error('No user found');
        }
    }
    catch (error) {
        console.error('Error fetching user:', error);
    }

    try {
        const policies = await getCarInsuranceByMyself();
        populateCarInsuranceList({ policies });
    } catch (error) {
        console.error('Error fetching car insurance policy:', error);
    }

    // Delegate for view policy buttons
    document.querySelectorAll('.view-btn').forEach(btn => {
        btn.addEventListener('click', async function (e) {
            const policyId = e.target.getAttribute('data-policy-id');
            try {
                const policy = await window.getCarInsuranceById(policyId);
                if (policy) {
                    const popUpContainer = document.getElementById('popup-container');
                    const popUpTitle = document.getElementById('popup-title');
                    const popUpBody = document.getElementById('popup-body');
                    const policyDetails = document.getElementById('policy-details');
                    populateCarInsuranceDetails(policy);
                    popUpBody.innerHTML = policyDetails.innerHTML;
                    popUpTitle.innerHTML = `Policy Number: ${policy.policy.policy_number}`;
                    if (typeof openPopup === 'function') {
                        openPopup();
                    } else if (popUpContainer) {
                        popUpContainer.style.display = 'block';
                        const overlay = document.getElementById('popup-overlay');
                        if (overlay) overlay.style.display = 'block';
                    }
                } else {
                    console.error('No policy found');
                }
            } catch (error) {
                console.error('Error fetching car insurance policy:', error);
            }
        });
    });

    // Delegate for update policy buttons
    document.querySelectorAll('.update-btn').forEach(btn => {
        btn.addEventListener('click', async function (e) {
            const policyId = e.target.getAttribute('data-policy-id');
            try {
                const policy = await window.getCarInsuranceById(policyId);
                if (policy) {
                    const popUpContainer = document.getElementById('popup-container');
                    const popUpTitle = document.getElementById('popup-title');
                    const popUpBody = document.getElementById('popup-body');
                    const policyUpdate = document.getElementById('policy-update');
                    populateCarInsuranceInputs(policy);
                    popUpBody.innerHTML = policyUpdate.innerHTML;
                    popUpTitle.innerHTML = `Policy Number: ${policy.policy.policy_number}`;                    
                    setPopupInputValues(policy);
                    if (typeof openPopup === 'function') {
                        openPopup();
                    } else if (popUpContainer) {
                        popUpContainer.style.display = 'block';
                        const overlay = document.getElementById('popup-overlay');
                        if (overlay) overlay.style.display = 'block';
                    }
                }
            } catch (error) {
                console.error('Error fetching car insurance policy:', error);
            }

            setTimeout(() => {
                const updateForm = document.getElementById('policy-form');
                const errorDiv = document.getElementById('update-policy-error');
                if (updateForm) {
                    updateForm.addEventListener('submit', async function (e) {
                        e.preventDefault();
                        if (errorDiv) {
                            errorDiv.style.display = 'none';
                            errorDiv.textContent = '';
                        }
                        // Collect form data
                        const formData = new FormData(updateForm);
                        // Build updated_policy object
                        const updated_policy = {
                            ci_policy_id: parseInt(formData.get('policy_id'), 10),
                            user_id: parseInt(formData.get('user_id'), 10),
                            policy_number: formData.get('policy_number'),
                            start_date: formData.get('start_date'),
                            end_date: formData.get('end_date'),
                            make: formData.get('make'),
                            model: formData.get('model'),
                            vrn: formData.get('vrn'),
                            coverage: formData.get('coverage')
                        };

                        // Get selected optional extra IDs
                        const optionalsList = updateForm.querySelector("#optionals-list");
                        const optionals = Array.from(optionalsList.querySelectorAll('input[type="checkbox"]:checked')).map(input => input.value);

                        let optional_extras = [];
                        if (optionals.length > 0) {
                            // Fetch all optional extras and filter by selected IDs
                            const allExtras = await window.fetchAllOptionalExtras();
                            optional_extras = allExtras.filter(extra =>
                                optionals.includes(String(extra.extra_id))
                            );
                        }

                        // Compose the request body
                        const data = {
                            updated_policy,
                            optional_extras
                        };

                        // Call API
                        const result = await window.updateCarInsurancePolicy(data);
                        // alert json result
                        console.log(result);
                        if (result.success) {
                            window.closePopup();
                            location.reload();
                        } else {
                            if (errorDiv) {
                                errorDiv.textContent = window.extractApiErrorMessage(result.data || result.message);
                                errorDiv.style.display = 'block';
                            }
                        }
                    });
                }
            }, 0);     
        });
    });

    // Delegate for delete policy buttons
    document.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', async function (e) {
            const policyId = e.target.getAttribute('data-policy-id');
            try {
                const policy = await window.getCarInsuranceById(policyId);
                if (policy) {
                    const popUpContainer = document.getElementById('popup-container');
                    const popUpTitle = document.getElementById('popup-title');
                    const popUpBody = document.getElementById('popup-body');
                    const policyDetails = document.getElementById('policy-details');
                    const policyDelete = document.getElementById('policy-delete');
                    const policyDeleteDetails = document.getElementById('policy-delete-details');
                    populateCarInsuranceDetails(policy);
                    policyDeleteDetails.innerHTML = policyDetails.innerHTML;
                    popUpBody.innerHTML = policyDelete.innerHTML;
                    popUpTitle.innerHTML = `Policy Number: ${policy.policy.policy_number}`;
                    if (typeof openPopup === 'function') {
                        openPopup();
                    } else if (popUpContainer) {
                        popUpContainer.style.display = 'block';
                        const overlay = document.getElementById('popup-overlay');
                        if (overlay) overlay.style.display = 'block';
                    }
                } else {
                    console.error('No policy found');
                }
            } catch (error) {
                console.error('Error fetching car insurance policy:', error);
            }
            setTimeout(() => {
                const confirmDeleteBtn = document.getElementById('confirm-delete-btn');
                if (confirmDeleteBtn) {
                    confirmDeleteBtn.addEventListener('click', async function () {
                        try {
                            await window.deleteCarInsurancePolicy(policyId);
                            const popupContainer = document.getElementById('popup-container');
                            const overlay = document.getElementById('popup-overlay');
                            if (popupContainer) popupContainer.style.display = 'none';
                            if (overlay) overlay.style.display = 'none';
                            // refresh page
                            location.reload();
                        } catch (error) {
                            console.error('Error deleting car insurance policy:', error);
                        }
                    });
                }
            }, 0);
        });
    });

    // Delegate for create policy button
    document.querySelectorAll('.create-btn').forEach(btn => {
        btn.addEventListener('click', async function (e) {
            const popUpContainer = document.getElementById('popup-container');
            const popUpTitle = document.getElementById('popup-title');
            const popUpBody = document.getElementById('popup-body');
            const policyCreate = document.getElementById('policy-create');
            // Set popup content
            popUpBody.innerHTML = policyCreate.innerHTML;
            popUpTitle.innerHTML = 'New Policy';

            popUpBody.querySelector('#user-id').value = userId || '';
            // random 5 digit number
            popUpBody.querySelector('#policy-number').value = window.createPolicyNumber();
            popUpBody.querySelector("#start-date").value = window.createStartDate();
            // Set end date to 1 year minus 1 day from start date
            const startDateInput = popUpBody.querySelector("#start-date");
            const endDateInput = popUpBody.querySelector("#end-date");
            const startDate = window.createStartDate();
            startDateInput.value = window.dateToDatabaseFormat(startDate);            
            const endDate = window.createEndDate(startDate);
            endDateInput.value = window.dateToDatabaseFormat(endDate);

            // add event listener to start date input
            startDateInput.addEventListener('change', function() {
                const newStartDate = new Date(startDateInput.value); 
                const newEndDate = window.createEndDate(newStartDate);
                endDateInput.value = window.dateToDatabaseFormat(newEndDate);
            });                

            const createOptionalsList = popUpBody.querySelector('#create-optionals-list');
            if (createOptionalsList) {
                createOptionalsList.innerHTML = 'Loading...';
                const allExtras = await window.fetchAllOptionalExtras();

                createOptionalsList.innerHTML = '';
                allExtras.forEach(extra => {
                    const label = document.createElement('label');
                    label.className = 'optional-extra-checkbox';

                    const checkbox = document.createElement('input');
                    checkbox.type = 'checkbox';
                    checkbox.value = extra.extra_id;
                    checkbox.name = 'optionals';

                    label.appendChild(checkbox);
                    label.appendChild(document.createTextNode(' ' + extra.name));
                    // Add a tooltip for the checkbox
                    createOptionalsList.appendChild(label);
                });
            }           

            if (typeof openPopup === 'function') {
                openPopup();
            } else if (popUpContainer) {
                popUpContainer.style.display = 'block';
                const overlay = document.getElementById('popup-overlay');
                if (overlay) overlay.style.display = 'block';
            }

            // Attach submit handler after form is in DOM
            setTimeout(() => {
                const popupForm = document.getElementById('policy-create-form');
                const errorDiv = document.getElementById('create-policy-error');
                if (popupForm) {
                    popupForm.addEventListener('submit', async function (e) {
                        e.preventDefault();
                        if (errorDiv) {
                            errorDiv.style.display = 'none';
                            errorDiv.textContent = '';
                        }
                        // Collect form data
                        const formData = new FormData(popupForm);
                        // Build policy object
                        const policy = {
                            ci_policy_id: 0, // For create, backend should ignore or auto-generate
                            user_id: parseInt(formData.get('user_id'), 10),
                            policy_number: formData.get('policy_number'),
                            start_date: formData.get('start_date'),
                            end_date: formData.get('end_date'),
                            make: formData.get('make'),
                            model: formData.get('model'),
                            vrn: formData.get('vrn'),
                            coverage: formData.get('coverage')
                        };

                        // Get selected optional extra IDs
                        const optionalsList = popupForm.querySelector("#create-optionals-list");
                        const optionals = Array.from(optionalsList.querySelectorAll('input[type="checkbox"]:checked')).map(input => input.value);

                        let optional_extras = [];
                        if (optionals.length > 0) {
                            // Fetch all optional extras and filter by selected IDs
                            const allExtras = await window.fetchAllOptionalExtras();
                            optional_extras = allExtras.filter(extra =>
                                optionals.includes(String(extra.extra_id))
                            );
                        }

                        // Compose the request body
                        const data = {
                            policy,
                            optional_extras
                        };
                        // Call API
                        const result = await window.createCarInsurancePolicy(data);
                        if (result.success) {
                            window.closePopup();
                            location.reload();
                        } else {
                            if (errorDiv) {
                                errorDiv.textContent = window.extractApiErrorMessage(result.data || result.message);
                                errorDiv.style.display = 'block';
                            }
                        }
                    });
                }
            }, 0);
        });
    });

    // Hide delete buttons for non-admin users (fix: do not redeclare userData/user)
    const isAdmin = user && user.is_admin;
    if (!isAdmin) {
        document.querySelectorAll('.delete-btn').forEach(btn => {
            btn.style.display = 'none';
        });
        // Also remove admin-only class from body for CSS fallback
        document.body.classList.remove('is-admin');
    } else {
        document.body.classList.add('is-admin');
    }
});

// define function to get car insurance by myself
async function getCarInsuranceByMyself() {
    const accessToken = localStorage.getItem('access_token');
    const response = await fetch('/read_car_insurance_policy?mode=myself', {
        headers: {
            'Authorization': `Bearer ${accessToken}`
        }
    });
    if (response.ok) {
        const data = await response.json();
        console.log(data);
        //extract the policy data
        const policies = data.policies;
        return policies;
    } else {
        // if the token is expired refresh the token
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
            const refreshResponse = await window.refreshToken();
            if (refreshResponse) {
                const data = await getCarInsuranceByMyself();
                return data;
            }
        }
        console.error('Error fetching car insurance policy:', response.statusText);
    }
}

// define function to populate user details
async function populateUserDetails(user) {
    const template = document.getElementById('user-profile-detail');
    const container = document.getElementById('user-profile');

    if (!template || !container) {
        alert("Template or container not found");
        return;
    }
    // Remove the template from the DOM (keep in memory)
    template.style.display = 'none';
    // Clear previous content
    container.innerHTML = '';
    // For each policy, clone the template and fill in data
    const clone = template.cloneNode(true);
    clone.style.display = '';
    clone.removeAttribute('id');
    let html = fillUserTemplate(clone.innerHTML, user);
    clone.innerHTML = html;
    container.appendChild(clone);
}
    

function populateCarInsuranceList(data) {
    console.log(data);
    // Get the template and container
    const template = document.getElementById('car-insurance-policy-list');
    const container = document.getElementById('car-insurance-policies');
    if (!template || !container) {
        alert("Template or container not found");
        return;
    }
    // Remove the template from the DOM (keep in memory)
    template.style.display = 'none';

    // Clear previous content
    container.innerHTML = '';
    // For each policy, clone the template and fill in data
    (data.policies || []).forEach(item => {
        const policy = item.policy || {};
        const clone = template.cloneNode(true);
        clone.style.display = '';
        clone.removeAttribute('id');

        let html = fillPolicyTemplate(clone.innerHTML, { ...policy, optional_extras: item.optional_extras });
        clone.innerHTML = html;

        container.appendChild(clone);
    });
}

// define function to replace html in #policy-details with populated template #car-insurance-policy-detail
async function populateCarInsuranceDetails(policy) {
    const template = document.getElementById('car-insurance-policy-detail');
    const container = document.getElementById('policy-details');
    if (!template || !container) {
        alert("Template or container not found");
        return;
    }
    // Remove the template from the DOM (keep in memory)
    template.style.display = 'none';

    // Clear previous content
    container.innerHTML = '';
    // For each policy, clone the template and fill in data
    const clone = template.cloneNode(true);
    clone.style.display = '';
    clone.removeAttribute('id');

    let html = fillPolicyTemplate(clone.innerHTML, { ...policy.policy, optional_extras: policy.optional_extras });
    clone.innerHTML = html;

    container.appendChild(clone);
}

async function populateCarInsuranceInputs(policy) {
    const template = document.getElementById('car-insurance-policy-inputs');
    const container = document.getElementById('policy-update');
    if (!template || !container) {
        alert("Template or container not found");
        return;
    }
    // Remove the template from the DOM (keep in memory)
    template.style.display = 'none';
    // Clear previous content
    container.innerHTML = '';
    // For each policy, clone the template and fill in data
    const clone = template.cloneNode(true);
    clone.style.display = '';
    clone.removeAttribute('id');
    let html = fillPolicyInputsTemplate(clone.innerHTML, { ...policy.policy, optional_extras: policy.optional_extras });
    clone.innerHTML = html;

    container.appendChild(clone);

    // Set input values after inserting into DOM
    const p = policy.policy || {};
    const policyIdInput = container.querySelector('#policy-id');
    const policyUserIdInput = container.querySelector('#policy-user-id');
    const policyNumberInput = container.querySelector('#policy-number');
    const endDateInput = container.querySelector('#end-date');
    const userIdInput = container.querySelector('#user-id');

    if (policyIdInput) policyIdInput.value = p.ci_policy_id || '';
    if (policyUserIdInput) policyUserIdInput.value = p.user_id || '';
    if (policyNumberInput) policyNumberInput.value = p.policy_number || '';
    if (endDateInput) endDateInput.value = p.end_date || '';
    if (userIdInput) userIdInput.value = p.user_id || '';
}

// Helper to set values on the popup's visible inputs and render optional extras
async function setPopupInputValues(policy) {
    const p = policy.policy || {};
    const popup = document.getElementById('popup-body');
    const startDateInput = popup.querySelector('#start-date');
    const vrnInput = popup.querySelector('#vrn');
    const makeInput = popup.querySelector('#make');
    const modelInput = popup.querySelector('#model');
    const coverageInput = popup.querySelector('#coverage');
    const endDateLabel = popup.querySelector('#end-date-label');
    const optionalsList = popup.querySelector('#optionals-list');

    if (startDateInput) {
        let val = p.start_date || '';
        if (val && val.length > 10) val = val.slice(0, 10);
        startDateInput.value = val;

        startDateInput.addEventListener('change', function() {
            const startVal = startDateInput.value;
            const endDateInput = popup.querySelector('#end-date');
            if (startVal && endDateLabel) {
                // Use main.js date functions for formatting
                const start = new Date(startVal);
                const end = window.createEndDate(start);
                // Set label in dd/mm/yyyy
                endDateLabel.textContent = window.formatDate(window.dateToDatabaseFormat(end));
                // Set input value in yyyy-mm-dd
                if (endDateInput) {
                    endDateInput.value = window.dateToDatabaseFormat(end);
                }
            }
        });
    }
    if (vrnInput) vrnInput.value = p.vrn || '';
    if (makeInput) makeInput.value = p.make || '';
    if (modelInput) modelInput.value = p.model || '';
    if (coverageInput) coverageInput.value = p.coverage || '';

    window.populateOptionalExtras(policy, optionalsList);
}

function fillUserTemplate(templateHtml, user) {
    role = user.is_admin ? 'Admin' : 'User';
    return templateHtml
        .replace(/\[username\]/g, user.username || '')
        .replace(/\[email\]/g, user.email || '')
        .replace(/\[role\]/g, role || '');
}

function fillPolicyTemplate(templateHtml, policy) {
    // Format optional_extras as a comma-delimited string of names if it's an array of objects
    let optionals = '';
    if (Array.isArray(policy.optional_extras)) {
        optionals = policy.optional_extras.map(e => e.name || '').filter(Boolean).join('<br/>');
    } else if (typeof policy.optional_extras === 'string') {
        optionals = policy.optional_extras;
    }

    let start_date = policy.start_date || '';
    // Ensure date is formatted as dd/mm/yyyy
    if (start_date && start_date.includes('-')) {
        start_date = window.formatDate(start_date); // use global function
    }

    let end_date = policy.end_date || '';
    // Ensure date is formatted as dd/mm/yyyy
    if (end_date && end_date.includes('-')) {
        end_date = window.formatDate(end_date); // use global function
    }    

    return templateHtml
        .replace(/\[policy id\]/g, policy.ci_policy_id || '')
        .replace(/\[policy number\]/g, policy.policy_number || '')
        .replace(/\[start date\]/g, start_date || '')
        .replace(/\[end date\]/g, end_date || '')
        .replace(/\[make\]/g, policy.make || '')
        .replace(/\[model\]/g, policy.model || '')
        .replace(/\[vrn\]/g, policy.vrn || '')
        .replace(/\[coverage\]/g, policy.coverage || '')
        .replace(/\[optionals\]/g, optionals);
}

function fillPolicyInputsTemplate(templateHtml, policy) {
    let end_date = policy.end_date || '';
    // Ensure date is formatted as dd/mm/yyyy
    if (end_date && end_date.includes('-')) {
        end_date = window.formatDate(end_date); // use global function
    }
    return templateHtml
        .replace(/\[policy number\]/g, policy.policy_number || '')
        .replace(/\[end date\]/g, end_date || '');
}
