window.addEventListener('DOMContentLoaded', async () => {
    const mainContent = document.getElementById('main-content');
    const user = JSON.parse(localStorage.getItem('user'));
    const userId = user.user_id;

    // get user by id
    retrievedUser = await window.getUserById(userId);
    approved = false
    if (retrievedUser && retrievedUser.is_admin) {
        approved = true
    }

    if (!approved) {
        window.location.href = '/';
    }
    else {
        if (window.innerWidth <= 1200) {
            alert("Welcome to the admin dashboard. You must use a desktop to access the features of the admin dashboard effectively.");
        }
        mainContent.style.display = 'block';
    }

    // Get all action buttons and output cards
    const actionButtons = document.querySelectorAll('.action-btn');  
    const definerCards = document.querySelectorAll('.definer-card');
    const outputCards = document.querySelectorAll('.output-card');      

    function removeActiveClassFromButtons(type) {
        if (type === 'all') {
            buttons = document.querySelectorAll('.action-btn, .definer-btn');
        } else {
            buttons = document.querySelectorAll(`.${type}-btn`);
        }
        buttons.forEach(button => {
            button.classList.remove('active-btn');
        });
    }

    function hideAllDefinerCards() {
        definerCards.forEach(card => {
            card.style.display = 'none';
        });
    }

    function hideAllOutputCards() {
        outputCards.forEach(card => {
            card.style.display = 'none';
        });
    }

    function hideAllDefinerAndOutputCards() {
        hideAllDefinerCards();
        hideAllOutputCards();
    }

    // Shared logic for all action buttons
    actionButtons.forEach(btn => {
        btn.addEventListener('click', function () {
            // If already active, do nothing
            if (btn.classList.contains('active-btn')) return;
            removeActiveClassFromButtons('all');
            hideAllDefinerAndOutputCards();
            // Add active to this button
            btn.classList.add('active-btn');
            // Show the corresponding definer card if it exists
            const action = btn.id.replace('-btn', ''); // e.g. create-user
            const definerCard = document.getElementById(`${action}-card`);
            if (definerCard) {
                definerCard.style.display = 'block';
            }
        }, { capture: true }); // Use capture so this runs before individual listeners
    });

    // Set User Buttons
    const createUserBtn = document.getElementById('create-user-btn');
    const readUserBtn = document.getElementById('read-user-btn');
    const updateUserBtn = document.getElementById('update-user-btn');
    const deleteUserBtn = document.getElementById('delete-user-btn');
    
    // Add event listener for create-user-btn    
    if (createUserBtn) {
        const createUserCopyBtn = document.getElementById('create-user-copy-btn');
        const createUserNewBtn = document.getElementById('create-user-new-btn');
        const createUserForm = document.getElementById('create-user-form');
        const createUserCopyUserId = document.getElementById('create-user-copy-user-id');

        createUserBtn.addEventListener('click', () => {
            createUserCopyUserId.style.display = 'none';
        });

        const createUserCopyConfirmBtn = document.getElementById('create-user-copy-confirm-btn');
        const createUserId = document.getElementById('create-user-id');

        createUserCopyBtn.addEventListener('click', () => {
            hideAllOutputCards();
            removeActiveClassFromButtons('definer');
            createUserCopyBtn.classList.add('active-btn');
            createUserCopyUserId.style.display = 'block';
        });

        createUserCopyConfirmBtn.addEventListener('click', () => {
            if (createUserId.value) {
                const userId = createUserId.value;
                const createUserDetailsCard = document.getElementById('create-user-details-card');
                window.getUserById(userId).then(user => {
                    if (user) {
                        // Populate the form with user details
                        createUserDetailsCard.querySelector('.user-id').value = 0;
                        createUserDetailsCard.querySelector('.username').value = user.username;
                        createUserDetailsCard.querySelector('.email').value = user.email;
                        createUserDetailsCard.querySelector('.password').value = '';
                        createUserDetailsCard.querySelector('.role').value = user.is_admin ? 'admin' : 'user';
                        createUserDetailsCard.style.display = 'block';
                    } else {
                        alert('User not found.');
                    }
                });
            }
            else {
                alert('Please enter a user ID.');
            }
        });

        createUserNewBtn.addEventListener('click', () => {
            const createUserDetailsCard = document.getElementById('create-user-details-card');
            hideAllOutputCards
            removeActiveClassFromButtons('definer');
            createUserNewBtn.classList.add('active-btn');
            createUserCopyUserId.style.display = 'none';
            // remove all values from the form
            createUserDetailsCard.querySelector('.user-id').value = 0;
            createUserDetailsCard.querySelector('.username').value = '';
            createUserDetailsCard.querySelector('.email').value = '';
            createUserDetailsCard.querySelector('.password').value = '';
            createUserDetailsCard.querySelector('.role').value = 'user';
            // show the create user details card
            createUserDetailsCard.style.display = 'block';
        });

        createUserForm.addEventListener('submit', async function (e) {
            e.preventDefault();
            const userId = createUserForm.querySelector('.user-id').value || 0;
            const username = createUserForm.querySelector('.username').value;
            let password = createUserForm.querySelector('.password').value;
            if (password) {
                password = md5(password);
            }
            const email = createUserForm.querySelector('.email').value;
            const role = createUserForm.querySelector('.role').value;
            const is_admin = role === 'admin';

            const userData = {
                user_id: Number(userId),
                username: username,
                password: password,
                email: email,
                is_admin: is_admin
            };

            try {
                await window.createUser(userData);
                alert('User created successfully!');
                createUserForm.reset();
            } catch (error) {
                alert('Failed to create user.');
            }
        });
    }

    // Add event listener for read-user-btn
    if (readUserBtn) {
        const readUserByIdInput = document.getElementById('read-user-id-input');
        const readUserByFiterInput = document.getElementById('read-user-filter-input');
        const readUserId = document.getElementById('read-user-id');
        const readUserIdBtn = document.getElementById('read-user-id-btn');
        const readUserListAllBtn = document.getElementById('read-user-all-btn');
        const readUserFilterBtn = document.getElementById('read-user-filter-btn');
        const readUserDetailsCard = document.getElementById('read-user-details-card');
        const readUserListCard = document.getElementById('read-user-list-card');
        const readUserListAllTemplate = document.getElementById('read-user-list-all-output-template');
        const readUserTableBody = document.getElementById('user-list-body');

        readUserBtn.addEventListener('click', () => {              
            readUserByIdInput.style.display = 'none';
            readUserByFiterInput.style.display = 'none';
        });

        const readUserByIdConfirm = document.getElementById('read-user-id-confirm-btn');

        readUserIdBtn.addEventListener('click', () => {
            hideAllOutputCards();
            removeActiveClassFromButtons('definer');
            readUserIdBtn.classList.add('active-btn');
            readUserByFiterInput.style.display = 'none';
            readUserByIdInput.style.display = 'block';
        }); 

        readUserByIdConfirm.addEventListener('click', () => {
            const userId = readUserId.value;
            if (userId) {
                window.getUserById(userId).then(user => {
                    if (user) {
                        // Populate the form with user details
                        readUserDetailsCard.querySelector('.user-id').value = user.user_id;
                        readUserDetailsCard.querySelector('.username').value = user.username;
                        readUserDetailsCard.querySelector('.email').value = user.email;
                        readUserDetailsCard.querySelector('.role').value = user.is_admin ? 'admin' : 'user';
                        readUserDetailsCard.style.display = 'block';
                    } else {
                        alert('User not found.');
                    }
                });
            }
            else {
                alert('Please enter a user ID.');
            }
        });

        readUserListAllBtn.addEventListener('click', () => {
            hideAllOutputCards();
            removeActiveClassFromButtons('definer');
            readUserListAllBtn.classList.add('active-btn');
            readUserByIdInput.style.display = 'none';
            readUserByFiterInput.style.display = 'none';

            // Fetch all users and display them
            getAllUsers().then(users => {
                if (users && users.length > 0) {
                    readUserTableBody.innerHTML = ''; // Clear existing rows
                    users.forEach(user => {
                        if (readUserListAllTemplate && readUserListAllTemplate.content) {
                            const row = readUserListAllTemplate.content.cloneNode(true);
                            row.querySelector('.user-id').textContent = user.user_id;
                            row.querySelector('.username').textContent = user.username;
                            row.querySelector('.email').textContent = user.email;
                            row.querySelector('.role').textContent = user.is_admin ? 'Admin' : 'User';
                            readUserTableBody.appendChild(row);
                        }
                    });
                    // Make the table sortable
                    const userListTable = document.getElementById('user-list-table');
                    if (userListTable && userListTable.classList.contains('sortable-table')) {
                        makeTableSortable(userListTable);
                    }
                    readUserListCard.style.display = 'block';
                } else {
                    alert('No users found.');
                }
            }).catch(error => {
                console.error('Error fetching users:', error);
            });
            readUserListCard.style.display = 'block';
        });

        const readUserFilterConfirmBtn = document.getElementById('read-user-filter-confirm-btn');

        readUserFilterBtn.addEventListener('click', () => {
            hideAllOutputCards();
            removeActiveClassFromButtons('definer');
            readUserFilterBtn.classList.add('active-btn');
            readUserByIdInput.style.display = 'none';
            readUserByFiterInput.style.display = 'block';
        });
            
        readUserFilterConfirmBtn.addEventListener('click', () => {
            const fieldInputValue = document.getElementById('user-field').value;
            const valueInputValue = document.getElementById('user-value').value;

            if (fieldInputValue && valueInputValue) {
                getUserWithFilter(fieldInputValue, valueInputValue).then(users => {
                    if (users && users.length > 0) {
                        readUserTableBody.innerHTML = ''; // Clear existing rows
                        users.forEach(user => {
                            if (readUserListAllTemplate && readUserListAllTemplate.content) {
                                const row = readUserListAllTemplate.content.cloneNode(true);
                                row.querySelector('.user-id').textContent = user.user_id;
                                row.querySelector('.username').textContent = user.username;
                                row.querySelector('.email').textContent = user.email;
                                row.querySelector('.role').textContent = user.is_admin ? 'Admin' : 'User';
                                readUserTableBody.appendChild(row);
                            }
                        });
                        // Make the table sortable
                        const userListTable = document.getElementById('user-list-table');
                        if (userListTable && userListTable.classList.contains('sortable-table')) {
                            makeTableSortable(userListTable);
                        }
                        readUserListCard.style.display = 'block';
                    } else {
                        readUserTableBody.innerHTML = '';
                        readUserListCard.style.display = 'none';
                        alert('No users found with the specified filter.');
                    }
                }).catch(error => {
                    console.error('Error fetching filtered users:', error);
                });
            }
        });
    }

    // Add event listener for update-user-btn
    if (updateUserBtn) {
        const updateUserId = document.getElementById('update-user-id');
        const updateUserIdBtn = document.getElementById('update-user-id-btn');
        const updateUserByIdInput = document.getElementById('update-user-id-input');
        const updateUserPwdInput = document.getElementById('update-user-pwd-input');        

        updateUserBtn.addEventListener('click', () => {
            updateUserByIdInput.style.display = 'none';
            updateUserPwdInput.style.display = 'none';
        });

        const updateUserByIdConfirm = document.getElementById('update-user-id-confirm-btn');

        updateUserIdBtn.addEventListener('click', () => {
            hideAllOutputCards();
            removeActiveClassFromButtons('definer');
            updateUserIdBtn.classList.add('active-btn');
            updateUserPwdInput.style.display = 'none';
            updateUserByIdInput.style.display = 'block';
        });
            
        updateUserByIdConfirm.addEventListener('click', () => {
            const userId = updateUserId.value;
            if (userId) {
                window.getUserById(userId).then(user => {
                    if (user) {
                        // Populate the form with user details
                        const updateUserDetailsCard = document.getElementById('update-user-details-card');
                        updateUserDetailsCard.querySelector('.user-id').value = user.user_id;
                        updateUserDetailsCard.querySelector('.username').value = user.username;
                        updateUserDetailsCard.querySelector('.email').value = user.email;
                        updateUserDetailsCard.querySelector('.role').value = user.is_admin ? 'admin' : 'user';
                        updateUserDetailsCard.style.display = 'block';
                    } else {
                        alert('User not found.');
                    }
                });
            }
            else {
                alert('Please enter a user ID.');
            }                    
        });

        const updatePwdUserId = document.getElementById('update-pwd-user-id');
        const updateUserPwdBtn = document.getElementById('update-user-pwd-btn');

        updateUserPwdBtn.addEventListener('click', () => {
            hideAllOutputCards();
            removeActiveClassFromButtons('definer');
            updateUserPwdBtn.classList.add('active-btn');
            updateUserByIdInput.style.display = 'none';
            updateUserPwdInput.style.display = 'block';
        });

        const updateUserPwdConfirm = document.getElementById('update-user-pwd-confirm-btn');
        updateUserPwdConfirm.addEventListener('click', () => {
            const user_id = updatePwdUserId.value;

            if (user_id) {
                window.getUserById(user_id).then(user => {
                    if (user) {
                        // Populate the form with user details
                        const updateUserPwdDetailsCard = document.getElementById('update-user-pwd-details-card');
                        updateUserPwdDetailsCard.querySelector('.user-id').value = user.user_id;
                        updateUserPwdDetailsCard.querySelector('.username').textContent = user.username;
                        updateUserPwdDetailsCard.style.display = 'block';
                    } else {
                        alert('User not found.');
                    }
                });
            }
        });

        const updateUserForm = document.getElementById('update-user-form');

        updateUserForm.addEventListener('submit', async function (e) {
            e.preventDefault();
            const userId = updateUserForm.querySelector('.user-id').value;
            const username = updateUserForm.querySelector('.username').value;
            const email = updateUserForm.querySelector('.email').value;
            const role = updateUserForm.querySelector('.role').value;
            const is_admin = role === 'admin';

            const userData = {
                user_id: Number(userId),
                username: username,
                email: email,
                is_admin: is_admin
            };

            try {
                await window.updateUser(userData);
                alert('User updated successfully!');
                updateUserByIdConfirm.click(); // Reset the form by re-fetching user details
            } catch (error) {
                alert('Failed to update user.');
            }
        });

        const updateUserPwdForm = document.getElementById('update-user-pwd-form');
        updateUserPwdForm.addEventListener('submit', async function (e) {
            e.preventDefault();
            const userId = updateUserPwdForm.querySelector('.user-id').value;
            const new_password = updateUserPwdForm.querySelector('.new-password').value;
            const confirm_password = updateUserPwdForm.querySelector('.confirm-password').value;

            if (userId && new_password && confirm_password) {
                if (new_password !== confirm_password) {
                    alert('New password and confirm password do not match.');
                    return;
                }

                try {
                    await window.updateUserPassword(userId, "", md5(new_password));
                    alert('Password updated successfully!');
                    updateUserPwdInput.style.display = 'none'; // Hide the input after successful update
                } catch (error) {
                    alert('Failed to update password.');
                }
            } else {
                alert('Please enter a user ID and passwords.');
            }
        });
    }
    
    // Add event listener for delete-user-btn
    if (deleteUserBtn) {
        const deleteUserId = document.getElementById('delete-user-id');
        const deleteUserIdBtn = document.getElementById('delete-user-id-btn');
        const deleteUserByIdInput = document.getElementById('delete-user-id-input');

        deleteUserBtn.addEventListener('click', () => {
            deleteUserByIdInput.style.display = 'none';
        });

        deleteUserIdBtn.addEventListener('click', () => {
            hideAllOutputCards();
            removeActiveClassFromButtons('definer');
            deleteUserIdBtn.classList.add('active-btn');
            deleteUserByIdInput.style.display = 'block';
        });

        const deleteUserByIdConfirm = document.getElementById('delete-user-id-confirm-btn');
            
        deleteUserByIdConfirm.addEventListener('click', () => {
            const userId = deleteUserId.value;
            if (userId) {
                window.getUserById(userId).then(user => {
                    if (user) {
                        // Populate the form with user details
                        const deleteUserDetailsCard = document.getElementById('delete-user-details-card');
                        deleteUserForm.querySelector('.user-id').value = user.user_id;
                        deleteUserDetailsCard.querySelector('.user-id').textContent = user.user_id;
                        deleteUserDetailsCard.querySelector('.username').textContent = user.username;
                        deleteUserDetailsCard.querySelector('.email').textContent = user.email;
                        deleteUserDetailsCard.querySelector('.role').textContent = user.is_admin ? 'Admin' : 'User';
                        deleteUserDetailsCard.style.display = 'block';
                    } else {
                        alert('User not found.');
                    }
                });
            }
            else {
                alert('Please enter a user ID.');
            }                    
        });

        const deleteUserForm = document.getElementById('delete-user-form');

        deleteUserForm.addEventListener('submit', async function (e) {
            e.preventDefault();
            const userId = deleteUserForm.querySelector('.user-id').value;
            if (userId) {
                try {
                    const success = await deleteUser(userId);
                    if (success) {
                        alert('User deleted successfully!');
                        deleteUserId.value = ''; // Clear the input field
                        deleteUserIdBtn.click(); // Reset the form by re-fetching user details
                    } else {
                        alert('Failed to delete user.');
                    }
                } catch (error) {
                    alert('Failed to delete user.');
                }
            } else {
                alert('Please enter a user ID.');
            }
        });          
    }

    // Set Policy Buttons
    const createPolicyBtn = document.getElementById('create-policy-btn');
    const readPolicyBtn = document.getElementById('read-policy-btn');
    const updatePolicyBtn = document.getElementById('update-policy-btn');
    const deletePolicyBtn = document.getElementById('delete-policy-btn');

    // Add event listener for create-policy-btn
    if (createPolicyBtn) {
        const createPolicyForm = document.getElementById('create-policy-form');
        const createPolicyDetailsCard = document.getElementById('create-policy-details-card');
        const createPolicyCopyPolicyId = document.getElementById('create-policy-copy-policy-id');
        const createPolicyCopyBtn = document.getElementById('create-policy-copy-btn');
        const createPolicyNewBtn = document.getElementById('create-policy-new-btn');

        createPolicyBtn.addEventListener('click', () => {
            createPolicyCopyPolicyId.style.display = 'none';
        });

        const createPolicyCopyConfirmBtn = document.getElementById('create-policy-copy-confirm-btn');
        const createPolicyId = document.getElementById('create-policy-id');        

        createPolicyCopyBtn.addEventListener('click', () => {
            hideAllOutputCards();
            removeActiveClassFromButtons('definer');
            createPolicyCopyBtn.classList.add('active-btn');
            createPolicyCopyPolicyId.style.display = 'block';
        });

        createPolicyCopyConfirmBtn.addEventListener('click', () => {
            if (createPolicyId.value) {
                const policyId = createPolicyId.value;
                window.getCarInsuranceById(policyId).then(response => {
                    if (response) {
                        const policy = response.policy;
                        // Populate the form with policy details
                        createPolicyForm.querySelector('.ci-policy-id').value = 0;
                        createPolicyForm.querySelector('.user-id').value = policy.user_id;
                        createPolicyForm.querySelector('.policy-number').value = window.createPolicyNumber();
                        createPolicyForm.querySelector('.vrn').value = policy.vrn;
                        createPolicyForm.querySelector('.make').value = policy.make;
                        createPolicyForm.querySelector('.model').value = policy.model;
                        createPolicyForm.querySelector('.start-date').value = policy.start_date;
                        createPolicyForm.querySelector('.end-date').value = policy.end_date;
                        createPolicyForm.querySelector('.coverage').value = policy.coverage;

                        const optionalsList = createPolicyForm.querySelector('.optionals-list');
                        optionalsList.innerHTML = '';
                        window.populateOptionalExtras(response, optionalsList);

                        createPolicyDetailsCard.style.display = 'block';
                    } else {
                        alert('Policy not found.');
                    }
                });
            }
            else {
                alert('Please enter a policy ID.');
            }
        });

        createPolicyNewBtn.addEventListener('click', () => {
            const createPolicyDetailsCard = document.getElementById('create-policy-details-card');
            hideAllOutputCards();
            removeActiveClassFromButtons('definer');
            createPolicyNewBtn.classList.add('active-btn');
            createPolicyCopyPolicyId.style.display = 'none';
            // remove all values from the form
            createPolicyForm.querySelector('.ci-policy-id').value = 0;
            createPolicyForm.querySelector('.user-id').value = '';
            createPolicyForm.querySelector('.policy-number').value = window.createPolicyNumber();
            createPolicyForm.querySelector('.vrn').value = '';
            createPolicyForm.querySelector('.make').value = '';
            createPolicyForm.querySelector('.model').value = '';
            startDateObj = window.createStartDate();
            startDate = window.dateToDatabaseFormat(startDateObj);
            endDateObj = window.createEndDate(startDateObj);
            endDate = window.dateToDatabaseFormat(endDateObj);
            createPolicyForm.querySelector('.start-date').value = startDate;
            createPolicyForm.querySelector('.end-date').value = endDate;
            createPolicyForm.querySelector('.coverage').value = '';

            // Clear optionals list
            const optionalsList = createPolicyForm.querySelector('.optionals-list');
            optionalsList.innerHTML = '';
            window.populateOptionalExtras(null, optionalsList);

            // Show the create policy details card
            createPolicyDetailsCard.style.display = 'block';
        });

        createPolicyForm.addEventListener('submit', async function (e) {
            e.preventDefault();
            const policyId = createPolicyForm.querySelector('.ci-policy-id').value || 0;
            const userId = createPolicyForm.querySelector('.user-id').value;
            const policyNumber = createPolicyForm.querySelector('.policy-number').value;
            const vrn = createPolicyForm.querySelector('.vrn').value;
            const make = createPolicyForm.querySelector('.make').value;
            const model = createPolicyForm.querySelector('.model').value;
            const startDate = createPolicyForm.querySelector('.start-date').value;
            const endDate = createPolicyForm.querySelector('.end-date').value;
            const coverage = createPolicyForm.querySelector('.coverage').value;

            // Get selected optionals
            const optionalsList = createPolicyForm.querySelector('.optionals-list');
            const selectedOptionals = Array.from(optionalsList.querySelectorAll('input[type="checkbox"]:checked')).map(input => input.value);
     
            // Build the policy object
            const policy = {
                ci_policy_id: Number(policyId),
                user_id: Number(userId),
                policy_number: policyNumber,
                start_date: startDate,
                end_date: endDate,
                make: make,
                model: model,
                vrn: vrn,
                coverage: coverage
            };

            // Get selected optional extra IDs
            let optional_extras = [];
            if (selectedOptionals.length > 0) {
                // Fetch all optional extras and filter by selected IDs
                const allExtras = await window.fetchAllOptionalExtras();
                optional_extras = allExtras.filter(extra =>
                    selectedOptionals.includes(String(extra.extra_id))
                );
            }

            // Compose the request body
            const body = {
                policy,
                optional_extras
            };   

            try {
                await createCarInsurancePolicy(body);
                alert('Policy created successfully!');
                createPolicyForm.reset();
                createPolicyDetailsCard.style.display = 'none'; // Hide the details card after submission
            } catch (error) {
                alert('Failed to create policy.');
            }
        });
    }

    if (readPolicyBtn) {
        const readPolicyId = document.getElementById('read-policy-id');
        const readPolicyIdBtn = document.getElementById('read-policy-id-btn');
        const readPolicyListAllBtn = document.getElementById('read-policy-all-btn');
        const readPolicyFilterBtn = document.getElementById('read-policy-filter-btn');
        const readPolicyDetailsCard = document.getElementById('read-policy-details-card');
        const readPolicyListCard = document.getElementById('read-policy-list-card');
        const readPolicyListAllTemplate = document.getElementById('read-policy-list-all-output-template');
        const policyTableBody = document.getElementById('policy-list-body');
        const readPolicyByIdInput = document.getElementById('read-policy-id-input');
        const readPolicyByFilterInput = document.getElementById('read-policy-filter-input');        

        readPolicyBtn.addEventListener('click', () => {
            readPolicyByIdInput.style.display = 'none';
            readPolicyByFilterInput.style.display = 'none';
        });

        readPolicyIdBtn.addEventListener('click', () => {
            hideAllOutputCards();
            removeActiveClassFromButtons('definer');
            readPolicyIdBtn.classList.add('active-btn');
            readPolicyByFilterInput.style.display = 'none';
            readPolicyByIdInput.style.display = 'block';
            const readPolicyByIdConfirm = document.getElementById('read-policy-id-confirm-btn');

            readPolicyByIdConfirm.addEventListener('click', () => {
                const policyId = readPolicyId.value;
                if (policyId) {
                    window.getCarInsuranceById(policyId).then(response => {
                        if (response) {
                            const policy = response.policy;
                            // Populate the form with policy details
                            readPolicyDetailsCard.querySelector('.ci-policy-id').value = policy.ci_policy_id;
                            readPolicyDetailsCard.querySelector('.user-id').value = policy.user_id;
                            readPolicyDetailsCard.querySelector('.policy-number').value = policy.policy_number;
                            readPolicyDetailsCard.querySelector('.vrn').value = policy.vrn;
                            readPolicyDetailsCard.querySelector('.make').value = policy.make;
                            readPolicyDetailsCard.querySelector('.model').value = policy.model;
                            readPolicyDetailsCard.querySelector('.start-date').value = policy.start_date;
                            readPolicyDetailsCard.querySelector('.end-date').value = policy.end_date;
                            readPolicyDetailsCard.querySelector('.coverage').value = policy.coverage;

                            // Clear optionals list
                            const optionalsList = readPolicyDetailsCard.querySelector('.optionals-list');
                            optionalsList.innerHTML = '';
                            window.populateOptionalExtras(response, optionalsList, true);

                            readPolicyDetailsCard.style.display = 'block';
                        } else {
                            alert('Policy not found.');
                        }
                    });
                }
                else {
                    alert('Please enter a policy ID.');
                }
            });
        });

        readPolicyListAllBtn.addEventListener('click', () => {
            hideAllOutputCards();
            removeActiveClassFromButtons('definer');
            readPolicyListAllBtn.classList.add('active-btn');
            readPolicyByIdInput.style.display = 'none';
            readPolicyByFilterInput.style.display = 'none';

            // Fetch all policies and display them
            getAllCarInsurancePolicies().then(policies => {
                if (policies && policies.length > 0) {
                    policyTableBody.innerHTML = ''; // Clear existing rows
                    policies.forEach(response => {
                        policy = response.policy;
                        if (readPolicyListAllTemplate && readPolicyListAllTemplate.content) {
                            const row = readPolicyListAllTemplate.content.cloneNode(true);
                            start_date = formatDate(policy.start_date);
                            end_date = formatDate(policy.end_date);
                            row.querySelector('.ci-policy-id').textContent = policy.ci_policy_id;
                            row.querySelector('.user-id').textContent = policy.user_id;
                            row.querySelector('.policy-number').textContent = policy.policy_number;
                            row.querySelector('.vrn').textContent = policy.vrn;
                            row.querySelector('.make').textContent = policy.make;
                            row.querySelector('.model').textContent = policy.model;
                            row.querySelector('.start-date').textContent = start_date;
                            row.querySelector('.end-date').textContent = end_date;
                            row.querySelector('.coverage').textContent = policy.coverage;
                            policyTableBody.appendChild(row);
                        }
                    });
                    // Make the table sortable
                    const policyListTable = document.getElementById('policy-list-table');
                    if (policyListTable && policyListTable.classList.contains('sortable-table')) {
                        makeTableSortable(policyListTable);
                    }
                    readPolicyListCard.style.display = 'block';
                } else {
                    alert('No policies found.');
                }
            }).catch(error => {
                console.error('Error fetching policies:', error);
            });
        });

        const readPolicyFilterConfirmBtn = document.getElementById('read-policy-filter-confirm-btn');        

        readPolicyFilterBtn.addEventListener('click', () => {
            hideAllOutputCards();
            removeActiveClassFromButtons('definer');
            readPolicyFilterBtn.classList.add('active-btn');
            readPolicyByIdInput.style.display = 'none';
            readPolicyByFilterInput.style.display = 'block';
        });

        readPolicyFilterConfirmBtn.addEventListener('click', () => {
            const fieldInputValue = document.getElementById('policy-field').value;
            const valueInputValue = document.getElementById('policy-value').value;

            if (fieldInputValue && valueInputValue) {
                getCarInsuranceWithFilter(fieldInputValue, valueInputValue).then(policies => {
                    if (policies && policies.length > 0) {
                        policyTableBody.innerHTML = ''; // Clear existing rows
                        policies.forEach(response => {
                            policy = response.policy;
                            if (readPolicyListAllTemplate && readPolicyListAllTemplate.content) {
                                const row = readPolicyListAllTemplate.content.cloneNode(true);
                                start_date = formatDate(policy.start_date);
                                end_date = formatDate(policy.end_date);
                                row.querySelector('.ci-policy-id').textContent = policy.ci_policy_id;
                                row.querySelector('.user-id').textContent = policy.user_id;
                                row.querySelector('.policy-number').textContent = policy.policy_number;
                                row.querySelector('.vrn').textContent = policy.vrn;
                                row.querySelector('.make').textContent = policy.make;
                                row.querySelector('.model').textContent = policy.model;
                                row.querySelector('.start-date').textContent = start_date;
                                row.querySelector('.end-date').textContent = end_date;
                                row.querySelector('.coverage').textContent = policy.coverage;
                                policyTableBody.appendChild(row);
                            }
                        });
                        // Make the table sortable
                        const policyListTable = document.getElementById('policy-list-table');
                        if (policyListTable && policyListTable.classList.contains('sortable-table')) {
                            makeTableSortable(policyListTable);
                        }
                        readPolicyListCard.style.display = 'block';
                    } else {
                        policyTableBody.innerHTML = '';
                        readPolicyListCard.style.display = 'none';
                        alert('No policies found with the specified filter.');
                    }
                }).catch(error => {
                    console.error('Error fetching filtered policies:', error);
                });
            }
            else {
                alert('Please enter a field and value to filter by.');
            }
        });
    }

    if (updatePolicyBtn) {
        const updatePolicyId = document.getElementById('update-policy-id');
        const updatePolicyIdBtn = document.getElementById('update-policy-id-btn');
        const updatePolicyByIdInput = document.getElementById('update-policy-id-input');

        updatePolicyBtn.addEventListener('click', () => {
            updatePolicyByIdInput.style.display = 'none';
        });

        updatePolicyIdBtn.addEventListener('click', () => {
            hideAllOutputCards();
            removeActiveClassFromButtons('definer');
            updatePolicyIdBtn.classList.add('active-btn');
            updatePolicyByIdInput.style.display = 'block';
        });

        const updatePolicyByIdConfirm = document.getElementById('update-policy-id-confirm-btn');

        updatePolicyByIdConfirm.addEventListener('click', () => {
            const policyId = updatePolicyId.value;
            if (policyId) {
                window.getCarInsuranceById(policyId).then(response => {
                    if (response) {
                        const policy = response.policy;
                        // Populate the form with policy details
                        const updatePolicyDetailsCard = document.getElementById('update-policy-details-card');
                        updatePolicyDetailsCard.querySelector('.ci-policy-id').value = policy.ci_policy_id;
                        updatePolicyDetailsCard.querySelector('.user-id').value = policy.user_id;
                        updatePolicyDetailsCard.querySelector('.policy-number').value = policy.policy_number;
                        updatePolicyDetailsCard.querySelector('.vrn').value = policy.vrn;
                        updatePolicyDetailsCard.querySelector('.make').value = policy.make;
                        updatePolicyDetailsCard.querySelector('.model').value = policy.model;
                        updatePolicyDetailsCard.querySelector('.start-date').value = policy.start_date;
                        updatePolicyDetailsCard.querySelector('.end-date').value = policy.end_date;
                        updatePolicyDetailsCard.querySelector('.coverage').value = policy.coverage;

                        // Clear optionals list
                        const optionalsList = updatePolicyDetailsCard.querySelector('.optionals-list');
                        optionalsList.innerHTML = '';
                        window.populateOptionalExtras(response, optionalsList);

                        // Show the details card
                        updatePolicyDetailsCard.style.display = 'block';
                    } else {
                        alert('Policy not found.');
                    }
                });
            }
            else {
                alert('Please enter a policy ID.');
            }
        });

        const updatePolicyForm = document.getElementById('update-policy-form');

        updatePolicyForm.addEventListener('submit', async function (e) {
            e.preventDefault();
            const policyId = updatePolicyForm.querySelector('.ci-policy-id').value;
            const userId = updatePolicyForm.querySelector('.user-id').value;
            const policyNumber = updatePolicyForm.querySelector('.policy-number').value;
            const vrn = updatePolicyForm.querySelector('.vrn').value;
            const make = updatePolicyForm.querySelector('.make').value;
            const model = updatePolicyForm.querySelector('.model').value;
            const startDate = updatePolicyForm.querySelector('.start-date').value;
            const endDate = updatePolicyForm.querySelector('.end-date').value;
            const coverage = updatePolicyForm.querySelector('.coverage').value;

            // Get selected optionals
            const optionalsList = updatePolicyForm.querySelector('.optionals-list');
            const selectedOptionals = Array.from(optionalsList.querySelectorAll('input[type="checkbox"]:checked')).map(input => input.value);

            // Build the policy object
            const updated_policy = {
                ci_policy_id:  Number(policyId),
                user_id: Number(userId),
                policy_number: policyNumber,
                start_date: startDate,
                end_date: endDate,
                make: make,
                model: model,
                vrn: vrn,
                coverage: coverage
            };

            // Get selected optional extra IDs
            let optional_extras = [];
            if (selectedOptionals.length > 0) {
                // Fetch all optional extras and filter by selected IDs
                const allExtras = await window.fetchAllOptionalExtras();
                optional_extras = allExtras.filter(extra =>
                    selectedOptionals.includes(String(extra.extra_id))
                );
            }

            // Compose the request body
            const body = {
                updated_policy,
                optional_extras
            };                    

            try {
                await window.updateCarInsurancePolicy(body);
                updatePolicyByIdConfirm.click(); // Reset the form by re-fetching policy details
            } catch (error) {
                alert('Failed to update policy.');
            }
            alert('Policy updated successfully!');                    
        });
    }

    if (deletePolicyBtn) {
        const deletePolicyId = document.getElementById('delete-policy-id');
        const deletePolicyIdBtn = document.getElementById('delete-policy-id-btn');
        const deletePolicyByIdInput = document.getElementById('delete-policy-id-input');

        deletePolicyBtn.addEventListener('click', () => {
            deletePolicyByIdInput.style.display = 'none';
        });

        deletePolicyIdBtn.addEventListener('click', () => {
            hideAllOutputCards();
            removeActiveClassFromButtons('definer');
            deletePolicyIdBtn.classList.add('active-btn');
            deletePolicyByIdInput.style.display = 'block';
        });

        const deletePolicyByIdConfirm = document.getElementById('delete-policy-id-confirm-btn');
        const deletePolicyForm = document.getElementById('delete-policy-form');        

        deletePolicyByIdConfirm.addEventListener('click', () => {
            const policyId = deletePolicyId.value;
            if (policyId) {
                window.getCarInsuranceById(policyId).then(response => {
                    if (response) {
                        const policy = response.policy;
                        // Populate the form with policy details
                        const deletePolicyDetailsCard = document.getElementById('delete-policy-details-card');
                        deletePolicyForm.querySelector('.ci-policy-id').value = policy.ci_policy_id;
                        deletePolicyDetailsCard.querySelector('.ci-policy-id').textContent = policy.ci_policy_id;
                        deletePolicyDetailsCard.querySelector('.user-id').textContent = policy.user_id;
                        deletePolicyDetailsCard.querySelector('.policy-number').textContent = policy.policy_number;
                        deletePolicyDetailsCard.querySelector('.vrn').textContent = policy.vrn;
                        deletePolicyDetailsCard.querySelector('.make').textContent = policy.make;
                        deletePolicyDetailsCard.querySelector('.model').textContent = policy.model;
                        deletePolicyDetailsCard.querySelector('.start-date').textContent = formatDate(policy.start_date);
                        deletePolicyDetailsCard.querySelector('.end-date').textContent = formatDate(policy.end_date);
                        deletePolicyDetailsCard.querySelector('.coverage').textContent = policy.coverage;

                        // Clear optionals list
                        const optionalsList = deletePolicyDetailsCard.querySelector('.optionals-list');
                        optionalsList.innerHTML = '';
                        window.populateOptionalExtras(response, optionalsList, true);

                        // Show the details card
                        deletePolicyDetailsCard.style.display = 'block';
                    }
                    else {
                        alert('Policy not found.');
                    }
                });
            }
            else {
                alert('Please enter a policy ID.');
            }
        });

        deletePolicyForm.addEventListener('submit', async function (e) {
            e.preventDefault();
            const policyId = deletePolicyForm.querySelector('.ci-policy-id').value;
            if (policyId) {
                try {
                    const success = await window.deleteCarInsurancePolicy(policyId);
                    if (success) {
                        alert('Policy deleted successfully!');
                        deletePolicyId.value = ''; // Clear the input field
                        deletePolicyIdBtn.click(); // Reset the form by re-fetching policy details
                    } else {
                        alert('Failed to delete policy.');
                    }
                } catch (error) {
                    alert('Failed to delete policy.');
                }
            } else {
                alert('Please enter a policy ID.');
            }
        });
    }

    // Set Opetional Extras Buttons
    const createExtraBtn = document.getElementById('create-extra-btn');
    const readExtraBtn = document.getElementById('read-extra-btn');
    const updateExtraBtn = document.getElementById('update-extra-btn');
    const deleteExtraBtn = document.getElementById('delete-extra-btn');

    // Add event listener for create-extra-btn
    if (createExtraBtn) {
        const createExtraForm = document.getElementById('create-extra-form');
        const createExtraDetailsCard = document.getElementById('create-extra-details-card');
        const createExtraCopyExtraId = document.getElementById('create-extra-copy-extra-id');
        const createExtraCopyBtn = document.getElementById('create-extra-copy-btn');
        const createExtraNewBtn = document.getElementById('create-extra-new-btn');

        createExtraBtn.addEventListener('click', () => {
            createExtraCopyExtraId.style.display = 'none';
        });

        const createExtraCopyConfirmBtn = document.getElementById('create-extra-copy-confirm-btn');
        const createExtraId = document.getElementById('create-extra-id');        

        createExtraCopyBtn.addEventListener('click', () => {
            hideAllOutputCards();
            removeActiveClassFromButtons('definer');
            createExtraCopyBtn.classList.add('active-btn');
            createExtraCopyExtraId.style.display = 'block';
        });

        createExtraCopyConfirmBtn.addEventListener('click', () => {
            if (createExtraId.value) {
                const extraId = createExtraId.value;
                getOptionalExtraById(extraId).then(response => {
                    if (response) {
                        const extra = response.optional_extras[0];
                        // Populate the form with extra details
                        createExtraForm.querySelector('.extra-id').value = 0;
                        createExtraForm.querySelector('.name').value = extra.name;
                        createExtraForm.querySelector('.code').value = extra.code;
                        createExtraForm.querySelector('.price').value = extra.price;

                        // Show the details card
                        createExtraDetailsCard.style.display = 'block';
                    } else {
                        alert('Optional Extra not found.');
                    }
                });
            }
            else {
                alert('Please enter an optional extra ID.');
            }
        });

        createExtraNewBtn.addEventListener('click', () => {
            hideAllOutputCards();
            removeActiveClassFromButtons('definer');
            createExtraNewBtn.classList.add('active-btn');
            createExtraCopyExtraId.style.display = 'none';
            // remove all values from the form
            createExtraForm.querySelector('.extra-id').value = 0;
            createExtraForm.querySelector('.name').value = '';
            createExtraForm.querySelector('.code').value = '';
            createExtraForm.querySelector('.price').value = '';
            // Show the create extra details card
            createExtraDetailsCard.style.display = 'block';
        });

        createExtraForm.addEventListener('submit', async function (e) {
            e.preventDefault();
            const extraId = createExtraForm.querySelector('.extra-id').value;
            const name = createExtraForm.querySelector('.name').value;
            const code = createExtraForm.querySelector('.code').value;
            const price = parseFloat(createExtraForm.querySelector('.price').value);

            // Build the extra object
            const new_extra = {
                extra_id: Number(extraId),
                name: name,
                code: code,
                price: price
            };

            try {
                await createOptionalExtra(new_extra);
                alert('Optional Extra created successfully!');
                createExtraNewBtn.click(); // Reset the form by re-fetching extra details
            } catch (error) {
                alert('Failed to create optional extra.');
            }
        });
    }

    if (readExtraBtn) {
        const readExtraId = document.getElementById('read-extra-id');
        const readExtraIdBtn = document.getElementById('read-extra-id-btn');
        const readExtraListAllBtn = document.getElementById('read-extra-all-btn');
        const readExtraDetailsCard = document.getElementById('read-extra-details-card');
        const readExtraListCard = document.getElementById('read-extra-list-card');
        const readExtraListAllTemplate = document.getElementById('read-extra-list-all-output-template');
        const extraTableBody = document.getElementById('extra-list-body');
        const readExtraByIdInput = document.getElementById('read-extra-id-input');
        const readExtraByFilterInput = document.getElementById('read-extra-filter-input');

        readExtraBtn.addEventListener('click', () => {
            readExtraByIdInput.style.display = 'none';
        });
        readExtraIdBtn.addEventListener('click', () => {
            hideAllOutputCards();
            removeActiveClassFromButtons('definer');
            readExtraIdBtn.classList.add('active-btn');
            readExtraByIdInput.style.display = 'block';
            const readExtraByIdConfirm = document.getElementById('read-extra-id-confirm-btn');

            readExtraByIdConfirm.addEventListener('click', () => {
                const extraId = readExtraId.value;
                if (extraId) {
                    getOptionalExtraById(extraId).then(response => {
                        if (response) {
                            const extra = response.optional_extras[0];
                            // Populate the form with extra details
                            readExtraDetailsCard.querySelector('.extra-id').value = extra.extra_id;
                            readExtraDetailsCard.querySelector('.name').value = extra.name;
                            readExtraDetailsCard.querySelector('.code').value = extra.code;
                            readExtraDetailsCard.querySelector('.price').value = extra.price;

                            // Show the details card
                            readExtraDetailsCard.style.display = 'block';
                        } else {
                            alert('Optional Extra not found.');
                        }
                    });
                }
                else {
                    alert('Please enter an optional extra ID.');
                }
            });
        });
        readExtraListAllBtn.addEventListener('click', () => {
            hideAllOutputCards();
            removeActiveClassFromButtons('definer');
            readExtraListAllBtn.classList.add('active-btn');
            readExtraByIdInput.style.display = 'none';

            // Fetch all optional extras and display them
            window.fetchAllOptionalExtras().then(extras => {
                if (extras && extras.length > 0) {
                    extraTableBody.innerHTML = ''; // Clear existing rows
                    extras.forEach(extra => {
                        if (readExtraListAllTemplate && readExtraListAllTemplate.content) {
                            const row = readExtraListAllTemplate.content.cloneNode(true);
                            row.querySelector('.extra-id').textContent = extra.extra_id;
                            row.querySelector('.name').textContent = extra.name;
                            row.querySelector('.code').textContent = extra.code;
                            row.querySelector('.price').textContent = extra.price.toFixed(2);
                            extraTableBody.appendChild(row);
                        }
                    });
                    // Make the table sortable
                    const extraListTable = document.getElementById('extra-list-table');
                    if (extraListTable && extraListTable.classList.contains('sortable-table')) {
                        makeTableSortable(extraListTable);
                    }
                    readExtraListCard.style.display = 'block';
                } else {
                    alert('No optional extras found.');
                }
            }).catch(error => {
                console.error('Error fetching optional extras:', error);
            });
        });
    }

    if (updateExtraBtn) {
        const updateExtraId = document.getElementById('update-extra-id');
        const updateExtraIdBtn = document.getElementById('update-extra-id-btn');
        const updateExtraByIdInput = document.getElementById('update-extra-id-input');

        updateExtraBtn.addEventListener('click', () => {
            updateExtraByIdInput.style.display = 'none';
        });

        updateExtraIdBtn.addEventListener('click', () => {
            hideAllOutputCards();
            removeActiveClassFromButtons('definer');
            updateExtraIdBtn.classList.add('active-btn');
            updateExtraByIdInput.style.display = 'block';
        });

        const updateExtraByIdConfirm = document.getElementById('update-extra-id-confirm-btn');

        updateExtraByIdConfirm.addEventListener('click', () => {
            const extraId = updateExtraId.value;
            if (extraId) {
                getOptionalExtraById(extraId).then(response => {
                    if (response) {
                        const extra = response.optional_extras[0];
                        // Populate the form with extra details
                        const updateExtraDetailsCard = document.getElementById('update-extra-details-card');
                        updateExtraDetailsCard.querySelector('.extra-id').value = extra.extra_id;
                        updateExtraDetailsCard.querySelector('.name').value = extra.name;
                        updateExtraDetailsCard.querySelector('.code').value = extra.code;
                        updateExtraDetailsCard.querySelector('.price').value = extra.price;

                        // Show the details card
                        updateExtraDetailsCard.style.display = 'block';
                    } else {
                        alert('Optional Extra not found.');
                    }
                });
            }
            else {
                alert('Please enter an optional extra ID.');
            }
        });

        const updateExtraForm = document.getElementById('update-extra-form');

        updateExtraForm.addEventListener('submit', async function (e) {
            e.preventDefault();
            const extraId = updateExtraForm.querySelector('.extra-id').value;
            const name = updateExtraForm.querySelector('.name').value;
            const code = updateExtraForm.querySelector('.code').value;
            const price = parseFloat(updateExtraForm.querySelector('.price').value);

            // Build the extra object
            const updated_extra = {
                extra_id: Number(extraId),
                name: name,
                code: code,
                price: price
            };

            try {
                await updateOptionalExtra(updated_extra);
                updateExtraByIdConfirm.click(); // Reset the form by re-fetching extra details
                alert('Optional Extra updated successfully!');
            } catch (error) {
                alert('Failed to update optional extra.');
            }
        });
    }

    if (deleteExtraBtn) {
        const deleteExtraId = document.getElementById('delete-extra-id');
        const deleteExtraIdBtn = document.getElementById('delete-extra-id-btn');
        const deleteExtraByIdInput = document.getElementById('delete-extra-id-input');

        deleteExtraBtn.addEventListener('click', () => {
            deleteExtraByIdInput.style.display = 'none';
        });

        deleteExtraIdBtn.addEventListener('click', () => {
            hideAllOutputCards();
            removeActiveClassFromButtons('definer');
            deleteExtraIdBtn.classList.add('active-btn');
            deleteExtraByIdInput.style.display = 'block';
        });

        const deleteExtraByIdConfirm = document.getElementById('delete-extra-id-confirm-btn');
        const deleteExtraForm = document.getElementById('delete-extra-form');

        deleteExtraByIdConfirm.addEventListener('click', () => {
            const extraId = deleteExtraId.value;
            if (extraId) {
                getOptionalExtraById(extraId).then(response => {
                    if (response) {
                        const extra = response.optional_extras[0];
                        // Populate the form with extra details
                        const deleteExtraDetailsCard = document.getElementById('delete-extra-details-card');
                        deleteExtraForm.querySelector('.extra-id').value = extra.extra_id;
                        deleteExtraDetailsCard.querySelector('.extra-id').textContent = extra.extra_id;
                        deleteExtraDetailsCard.querySelector('.name').textContent = extra.name;
                        deleteExtraDetailsCard.querySelector('.code').textContent = extra.code;
                        deleteExtraDetailsCard.querySelector('.price').textContent = extra.price;

                        // Show the details card
                        deleteExtraDetailsCard.style.display = 'block';
                    } else {
                        alert('Optional Extra not found.');
                    }
                });
            }
            else {
                alert('Please enter an optional extra ID.');
            }
        });

        deleteExtraForm.addEventListener('submit', async function (e) {
            e.preventDefault();
            const extraId = deleteExtraForm.querySelector('.extra-id').value;
            if (extraId) {
                try {
                    const success = await deleteOptionalExtra(extraId);
                    if (success) {
                        alert('Optional Extra deleted successfully!');
                        deleteExtraId.value = ''; // Clear the input field
                        deleteExtraIdBtn.click(); // Reset the form by re-fetching extra details
                    }
                    else {
                        alert('Failed to delete optional extra.');
                    }
                } catch (error) {
                    alert('Failed to delete optional extra.');
                }
            }
            else {
                alert('Please enter an optional extra ID.');
            }
        });
    }
});

// Reusable table sorting function
function makeTableSortable(table) {
    const ths = table.querySelectorAll('thead th');
    // Select sort description element above the table
    let sortDesc = table.parentElement.querySelector('.table-sort-desc');

    function updateSortDesc(colIdx, isAsc) {
        const colName = ths[colIdx].textContent.trim();
        if (sortDesc) {
            sortDesc.textContent = `Sorted By: ${colName} - ${isAsc ? 'Ascending' : 'Descending'}`;
        }
    }

    ths.forEach((th, colIdx) => {
        th.style.cursor = 'pointer';
        th.addEventListener('click', function () {
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const isAsc = th.classList.contains('sort-asc');
            // Remove sort classes from all headers
            ths.forEach(header => header.classList.remove('sort-asc', 'sort-desc'));
            th.classList.add(isAsc ? 'sort-desc' : 'sort-asc');
            // Sort rows
            rows.sort((a, b) => {
                let aText = a.children[colIdx].textContent.trim();
                let bText = b.children[colIdx].textContent.trim();
                let aNum = parseFloat(aText), bNum = parseFloat(bText);
                if (!isNaN(aNum) && !isNaN(bNum)) {
                    return (isAsc ? bNum - aNum : aNum - bNum);
                }
                return (isAsc ? bText.localeCompare(aText) : aText.localeCompare(bText));
            });
            rows.forEach(row => tbody.appendChild(row));
            updateSortDesc(colIdx, !isAsc);
        });
    });

    // Auto-sort by first column ascending on initial render
    if (ths.length > 0) {
        const th = ths[0];
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        ths.forEach(header => header.classList.remove('sort-asc', 'sort-desc'));
        th.classList.add('sort-asc');
        rows.sort((a, b) => {
            let aText = a.children[0].textContent.trim();
            let bText = b.children[0].textContent.trim();
            let aNum = parseFloat(aText), bNum = parseFloat(bText);
            if (!isNaN(aNum) && !isNaN(bNum)) {
                return aNum - bNum;
            }
            return aText.localeCompare(bText);
        });
        rows.forEach(row => tbody.appendChild(row));
        updateSortDesc(0, true);
    }
}

async function getAllUsers() {
    const accessToken = localStorage.getItem('access_token');
    const response = await fetch('/read_user?mode=list_all', {
        headers: {
            'Authorization': `Bearer ${accessToken}`
        }
    });
    if (response.ok) {
        const data = await response.json();
        console.log(data);
        //extract the user data
        const users = data.users;
        return users;
    } else if (response.status === 401) {
        // if the token is expired refresh the token
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
            const refreshResponse = await window.refreshToken();
            if (refreshResponse) {
                const data = await getAllUsers();
                return data;
            }
        }

        console.error('Error fetching user:', response.statusText);
    }
    return null;
}

async function getUserWithFilter(field, value) {
    const accessToken = localStorage.getItem('access_token');
    const response = await fetch(`/read_user?mode=filter&field=${field}&value=${value}`, {
        headers: {
            'Authorization': `Bearer ${accessToken}`
        }
    });
    if (response.ok) {
        const data = await response.json();
        return data.users;
    } else if (response.status === 401) {
        // if the token is expired refresh the token
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
            const refreshResponse = await window.refreshToken();
            if (refreshResponse) {
                return getUserWithFilter(field, value);
            }
        }
        console.error('Error fetching user:', response.statusText);
    }
    return null;
}

async function deleteUser(userId) {
    const accessToken = localStorage.getItem('access_token');
    const response = await fetch(`/delete_user?user_id=${userId}`, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${accessToken}`
        }
    });
    if (response.ok) {
        return true;
    } else if (response.status === 401) {
        // if the token is expired refresh the token
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
            const refreshResponse = await window.refreshToken();
            if (refreshResponse) {
                return deleteUser(userId);
            }
        }
        console.error('Error deleting user:', response.statusText);
    }
    return false;
}

async function getAllCarInsurancePolicies() {
    const accessToken = localStorage.getItem('access_token');
    const response = await fetch('/read_car_insurance_policy?mode=list_all', {
        headers: {
            'Authorization': `Bearer ${accessToken}`
        }
    });
    if (response.ok) {
        const data = await response.json();
        return data.policies;
    } else if (response.status === 401) {
        // if the token is expired refresh the token
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
            const refreshResponse = await window.refreshToken();
            if (refreshResponse) {
                return getAllCarInsurancePolicies();
            }
        }
        console.error('Error fetching policies:', response.statusText);
    }
    return [];
}

async function getCarInsuranceWithFilter(field, value) {
    const accessToken = localStorage.getItem('access_token');
    const response = await fetch(`/read_car_insurance_policy?mode=filter&field=${field}&value=${value}`, {
        headers: {
            'Authorization': `Bearer ${accessToken}`
        }
    });
    if (response.ok) {
        const data = await response.json();
        return data.policies;
    } else if (response.status === 401) {
        // if the token is expired refresh the token
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
            const refreshResponse = await window.refreshToken();
            if (refreshResponse) {
                return getCarInsuranceWithFilter(field, value);
            }
        }
        console.error('Error fetching policies:', response.statusText);
    }
    return [];
}

async function createOptionalExtra(extra) {
    const accessToken = localStorage.getItem('access_token');
    const response = await fetch('/create_optional_extra', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify(extra)
    });
    if (response.ok) {
        return true;
    } else if (response.status === 401) {
        // if the token is expired refresh the token
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
            const refreshResponse = await window.refreshToken();
            if (refreshResponse) {
                return createOptionalExtra(extra);
            }
        }
        console.error('Error creating optional extra:', response.statusText);
    }
    return false;
}

async function getOptionalExtraById(extraId) {
    const accessToken = localStorage.getItem('access_token');
    const response = await fetch(`/read_optional_extra?mode=by_id&extra_id=${extraId}`, {
        headers: {
            'Authorization': `Bearer ${accessToken}`
        }
    });
    if (response.ok) {
        const data = await response.json();
        return data;
    } else if (response.status === 401) {
        // if the token is expired refresh the token
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
            const refreshResponse = await window.refreshToken();
            if (refreshResponse) {
                return getOptionalExtraById(extraId);
            }
        }
        console.error('Error fetching optional extra:', response.statusText);
    }
    return null;
}

async function updateOptionalExtra(extra) {
    const accessToken = localStorage.getItem('access_token');
    const response = await fetch('/update_optional_extra', {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify(extra)
    });
    if (response.ok) {
        return true;
    } else if (response.status === 401) {
        // if the token is expired refresh the token
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
            const refreshResponse = await window.refreshToken();
            if (refreshResponse) {
                return updateOptionalExtra(extra);
            }
        }
        console.error('Error updating optional extra:', response.statusText);
    }
    return false;
}

async function deleteOptionalExtra(extraId) {
    const accessToken = localStorage.getItem('access_token');
    const response = await fetch(`/delete_optional_extra?extra_id=${extraId}`, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${accessToken}`
        }
    });
    if (response.ok) {
        return true;
    } else if (response.status === 401) {
        // if the token is expired refresh the token
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
            const refreshResponse = await window.refreshToken();
            if (refreshResponse) {
                return deleteOptionalExtra(extraId);
            }
        }
        console.error('Error deleting optional extra:', response.statusText);
    }
    return false;
}

async function createCarInsurancePolicy(policy) {
    const accessToken = localStorage.getItem('access_token');
    const response = await fetch('/create_car_insurance_policy', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify(policy)
    });
    if (response.ok) {
        return true;
    } else if (response.status === 401) {
        // if the token is expired refresh the token
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
            const refreshResponse = await window.refreshToken();
            if (refreshResponse) {
                return createCarInsurancePolicy(policy);
            }
        }
        console.error('Error creating car insurance policy:', response.statusText);
    }
    return false;
}