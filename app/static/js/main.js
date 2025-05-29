(async function() {
    const registerLink = document.getElementById('register-link');
    const adminLink = document.getElementById('admin-dashboard-link');
    const navBar = document.getElementById('main-nav');
    if (registerLink) {
        registerLink.addEventListener('click', function(e) {
            if (registerLink.innerText === 'Log Out') {
                if (!confirm("Are you sure you want to log out?")) {
                    e.preventDefault();
                    return;
                }
                // remove tokens from local storage
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                localStorage.removeItem('user');
                window.location.href = '/';
            }
            else {
                window.location.href = '/register';
            }
        });
    }
    const popupContainer = document.getElementById('popup-container');
    const popupOverlay = document.getElementById('popup-overlay');
    const popupTitle = document.getElementById('popup-title');
    const popupBody = document.getElementById('popup-body');
    const popupClose = document.getElementById('popup-close');

    function openPopup() {
        if (popupOverlay) popupOverlay.style.display = 'block';
        if (popupContainer) {
            popupContainer.style.display = 'block';
            popupContainer.classList.remove('popup-close-anim');
            // force reflow for animation restart
            void popupContainer.offsetWidth;
            popupContainer.classList.add('popup-open');
        }
    }

    function closePopup() {
        if (popupContainer) {
            popupContainer.classList.remove('popup-open');
            popupContainer.classList.add('popup-close-anim');
            setTimeout(() => {
                if (popupContainer) popupContainer.style.display = 'none';
                if (popupOverlay) popupOverlay.style.display = 'none';
                if (popupTitle) popupTitle.innerHTML = '';
                if (popupBody) popupBody.innerHTML = '';
                popupContainer.classList.remove('popup-close-anim');
            }, 350);
        } else {
            if (popupOverlay) popupOverlay.style.display = 'none';
            if (popupTitle) popupTitle.innerHTML = '';
            if (popupBody) popupBody.innerHTML = '';
        }
    }

    // Make popup functions globally accessible
    window.openPopup = openPopup;
    window.closePopup = closePopup;

    if (popupClose) {
        popupClose.addEventListener('click', function() {
            closePopup();
        });
    }

    if (window.location.pathname !== '/') {
        const accessToken = localStorage.getItem('access_token');
        const refreshToken = localStorage.getItem('refresh_token');
        const user = localStorage.getItem('user');

        // if these are set set loggedIn to true
        const loggedIn = accessToken && refreshToken && user;
        // change register link to logout link
        if (loggedIn) {
            registerLink.innerText = 'Log Out';

            const isAdmin = user && JSON.parse(user).is_admin;
            if (adminLink) {
                if (isAdmin) {
                    adminLink.style.display = 'block';
                } else {
                    adminLink.style.display = 'none';
                }
            }
        } else {
            window.location.href = '/';
        }

        // You can use these variables as needed
        console.log('Access Token:', accessToken);
        console.log('Refresh Token:', refreshToken);
        console.log('User:', user);

        // call verify token endpoint with the access token
        await fetch('/verify_authentication', {
            method: 'POST',
            headers: {
                "Authorization": `Bearer ${accessToken}`
            }
        })
        .then(response => {
            if (response.ok) {
                return response.json();
            } else {
                // try to refresh the token
                return fetch('/refresh_token', {
                    method: 'POST',
                    headers: {
                        "Authorization": `Bearer ${refreshToken}`
                    }
                })
                .then(response => {
                    if (response.ok) {
                        return response.json();
                    } else {
                        throw new Error('Token refresh failed');
                    }
                })
                .then(data => {
                    if (data) {
                        console.log('Token refresh response:', data);
                        localStorage.setItem('access_token', data.access_token);
                        localStorage.setItem('refresh_token', data.refresh_token);
                        localStorage.setItem('user', JSON.stringify(data.user));
                        // Optionally reload the page or retry the original request
                        window.location.reload();
                    }
                });
            }
        })
        .then(data => {
            if (data) {
                console.log('Token verification response:', data);
                // Handle the response as needed
                // For example, you can redirect to the dashboard or show user info
            }
        })
        .catch(error => {
            console.error('Error verifying token:', error);
            // Handle error if needed
            // For example, you can redirect to the login page
            // remove tokens from local storage
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('user');
            window.location.href = '/';
        });
    }
    else {
        // if local storage has access token, refresh token and user, redirect to /dashboard
        const accessToken = localStorage.getItem('access_token');
        const refreshToken = localStorage.getItem('refresh_token');
        const user = localStorage.getItem('user');
        if (accessToken && refreshToken && user) {
            // redirect to /dashboard
            window.location.href = '/dashboard';
        }
        else {
            registerLink.innerText = 'Register';
            if (navBar) {
                navBar.style.display = 'none';
            }
        }
    }

    // Highlight active nav link
    const navLinks = document.querySelectorAll('#main-nav ul li a');
    navLinks.forEach(link => link.classList.remove('active'));
    let foundActive = false;
    navLinks.forEach(link => {
        if (window.location.pathname !== '/' && link.getAttribute('href') === window.location.pathname) {
            link.classList.add('active');
            foundActive = true;
        }
    });
})();

// Utility: convert date to dd/mm/yyyy
function formatDate(dateString, reverse=false) {
    if (!reverse) {
        const dateParts = dateString.split('-');
        dateString = `${dateParts[2]}/${dateParts[1]}/${dateParts[0]}`;
    }
    else {
        const dateParts = dateString.split('/');
        dateString = `${dateParts[2]}-${dateParts[1]}-${dateParts[0]}`;
    }
    return dateString;
}

// Make token/user functions globally accessible
async function refreshToken() {
    const refreshToken = localStorage.getItem('refresh_token');
    const response = await fetch('/refresh_token', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${refreshToken}`
        }
    });
    if (response.ok) {
        const data = await response.json();
        const accessToken = data.access_token;
        const refreshToken = data.refresh_token;
        const user = data.user;
        // Store tokens in local storage
        localStorage.setItem('access_token', accessToken);
        localStorage.setItem('refresh_token', refreshToken);
        localStorage.setItem('user', JSON.stringify(user));
        return { accessToken, refreshToken, user };
    } else {
        console.error('Error refreshing token:', response.statusText);
        // redirect to login page
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        window.location.href = '/';
    }
}

async function getUserById(userId) {
    const accessToken = localStorage.getItem('access_token');
    const response = await fetch(`/read_user?mode=by_id&user_id=${userId}`, {
        headers: {
            'Authorization': `Bearer ${accessToken}`
        }
    });
    if (response.ok) {
        const data = await response.json();
        console.log(data);
        //extract the user data
        const user = data.users[0];
        return user;
    } else if (response.status === 401) {
        // if the token is expired refresh the token
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
            const refreshResponse = await window.refreshToken();
            if (refreshResponse) {
                const data = await getUserById(userId);
                return data;
            }
        }

        console.error('Error fetching user:', response.statusText);
    }
    return null;
}

async function getUserByMyself() {
    const accessToken = localStorage.getItem('access_token');
    const response = await fetch('/read_user?mode=myself', {
        headers: {
            'Authorization': `Bearer ${accessToken}`
        }
    });
    if (response.ok) {
        const data = await response.json();
        console.log(data);
        //extract the user data
        const users = data.users[0];
        return users;
    } else if (response.status === 401) {
        // if the token is expired refresh the token
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
            const refreshResponse = await window.refreshToken();
            if (refreshResponse) {
                const data = await getUserByMyself();
                return data;
            }
        }
        console.error('Error fetching user:', response.statusText);
    }
    return null;
}

// Add this function to main.js
async function fetchAllOptionalExtras() {
    const accessToken = localStorage.getItem('access_token');
    const response = await fetch('/read_optional_extra?mode=list_all', {
        headers: {
            'Authorization': `Bearer ${accessToken}`
        }
    });
    if (response.ok) {
        const data = await response.json();
        return data.optional_extras || [];
    } else if (response.status === 401) {
        // if the token is expired refresh the token
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
            const refreshResponse = await window.refreshToken();
            if (refreshResponse) {
                const data = await fetchAllOptionalExtras();
                return data;
            }
        }
        console.error('Error fetching optional extras:', response.statusText);
    }
    return null;
}

// Add this function to main.js
async function getCarInsuranceById(policyId) {
    const accessToken = localStorage.getItem('access_token');
    const response = await fetch(`/read_car_insurance_policy?mode=by_id&policy_id=${policyId}`, {
        headers: {
            'Authorization': `Bearer ${accessToken}`
        }
    });
    if (response.ok) {
        const data = await response.json();
        console.log(data);
        //extract the policy data
        const policy = data.policies[0];
        return policy;
    } else if (response.status === 401) {
        // if the token is expired refresh the token
        const storedRefreshToken = localStorage.getItem('refresh_token');
        if (storedRefreshToken) {
            const refreshResponse = await window.refreshToken();
            if (refreshResponse) {
                const data = await getCarInsuranceById(policyId);
                return data;
            }
        }
        console.error('Error fetching car insurance policy:', response.statusText);
    }
    return null;
}

async function createCarInsurancePolicy(data) {
    const accessToken = localStorage.getItem('access_token');
    const response = await fetch('/create_car_insurance_policy', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    });
    console.log('Creating car insurance policy:', data);
    console.log('Response:', response);
    if (response.ok) {
        const data = await response.json();
        console.log(data);
        return data;
    } else if (response.status === 401) {
        // if the token is expired refresh the token
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
            const refreshResponse = await window.refreshToken();
            if (refreshResponse) {
                const data = await createCarInsurancePolicy(data);
                return data;
            }
        }
        console.error('Error creating car insurance policy:', response.statusText);
    }
    return null;
}

async function updateCarInsurancePolicy(updateData) {
    const accessToken = localStorage.getItem('access_token');
    const response = await fetch('/update_car_insurance_policy', {
        method: 'PUT',
        headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(updateData)
    });
    if (response.ok) {
        const data = await response.json();
        return data;
    } else if (response.status === 401) {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
            const refreshResponse = await window.refreshToken();
            if (refreshResponse) {
                return await updateCarInsurancePolicy(policyId, updateData);
            }
        }
        console.error('Error updating car insurance policy:', response.statusText);
    }
    return null;
}

async function deleteCarInsurancePolicy(policyId) {
    const accessToken = localStorage.getItem('access_token');
    const response = await fetch(`/delete_car_insurance_policy?policy_id=${policyId}`, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${accessToken}`
        }
    });
    if (response.ok) {
        const data = await response.json();
        return data;
    } else if (response.status === 401) {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
            const refreshResponse = await window.refreshToken();
            if (refreshResponse) {
                return await deleteCarInsurancePolicy(policyId);
            }
        }
        console.error('Error deleting car insurance policy:', response.statusText);
    }
    return null;
}

async function updateUser(updateData) {
    const accessToken = localStorage.getItem('access_token');
    const response = await fetch('/update_user', {
        method: 'PUT',
        headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(updateData)
    });
    if (response.ok) {
        const data = await response.json();
        return data;
    } else if (response.status === 401) {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
            const refreshResponse = await window.refreshToken();
            if (refreshResponse) {
                return await updateUser(userId, updateData);
            }
        }
        console.error('Error updating user:', response.statusText);
    }
    return null;
}

async function createUser(data) {
    const accessToken = localStorage.getItem('access_token');
    const response = await fetch('/create_user', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    });
    if (response.ok) {
        const data = await response.json();
        return data;
    } else if (response.status === 401) {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
            const refreshResponse = await window.refreshToken();
            if (refreshResponse) {
                return await createUser(data);
            }
        }
        console.error('Error creating user:', response.statusText);
    }
    return null;
}

// Populate optional extras in the policy form
async function populateOptionalExtras(policy, optionalsList, disabled = false) {
    if (optionalsList) {
        optionalsList.innerHTML = 'Loading...';
        const allExtras = await window.fetchAllOptionalExtras();
        if (!policy) {
            selectedExtras = [];
        }
        else {
            selectedExtras = Array.isArray(policy.optional_extras)
                ? policy.optional_extras.map(e => e.extra_id)
                : [];
        }
        optionalsList.innerHTML = '';
        allExtras.forEach(extra => {
            const label = document.createElement('label');
            label.className = 'optional-extra-checkbox'; // for CSS styling

            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.value = extra.extra_id;
            checkbox.name = 'optionals';
            checkbox.checked = selectedExtras.includes(extra.extra_id);
            checkbox.disabled = disabled; // Disable checkbox if form is read-only

            label.appendChild(checkbox);
            label.appendChild(document.createTextNode(' ' + extra.name));
            optionalsList.appendChild(label);
        });
    }
}

function createPolicyNumber() {
    return "CI" + Math.floor(10000 + Math.random() * 90000);
}

function createStartDate() {
    // Returns a Date object for use in createEndDate, but also returns the string for display
    const date = new Date();
    // For compatibility, return both the Date object and the string
    return date;
}

function createEndDate(startDateObj) {
    // Create a new Date object for the end date, 1 year - 1 day after the start date
    const endDate = new Date(startDateObj);
    endDate.setFullYear(endDate.getFullYear() + 1);
    endDate.setDate(endDate.getDate() - 1); // Subtract one day to make it one year minus one day
    return endDate;
}

function dateToDatabaseFormat(date) {
    // Convert a Date object to the format YYYY-MM-DD
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0'); // Months are zero-based
    const day = String(date.getDate()).padStart(2, '0');

    return year + "-" + month + "-" + day;
}

// Export to window for global access to ensure availability
window.refreshToken = refreshToken;
window.getUserById = getUserById;
window.getUserByMyself = getUserByMyself;
window.fetchAllOptionalExtras = fetchAllOptionalExtras;
window.formatDate = formatDate;
window.getCarInsuranceById = getCarInsuranceById;
window.createCarInsurancePolicy = createCarInsurancePolicy
window.updateCarInsurancePolicy = updateCarInsurancePolicy
window.deleteCarInsurancePolicy = deleteCarInsurancePolicy;
window.updateUser = updateUser;
window.createUser = createUser;
window.populateOptionalExtras = populateOptionalExtras;
window.createPolicyNumber = createPolicyNumber;
window.createStartDate = createStartDate;
window.createEndDate = createEndDate;
window.dateToDatabaseFormat = dateToDatabaseFormat;