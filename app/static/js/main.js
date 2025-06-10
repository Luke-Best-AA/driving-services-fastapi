// Main shared JS for navigation, popups, API helpers, and global utilities
// Handles nav bar logic, session management, popups, and exposes API functions globally
// Used by all pages for consistent UI and backend communication
//
(async function() {
    // Navigation bar and logout logic
    const logoutLink = document.getElementById('logout-link');
    const adminLink = document.getElementById('admin-dashboard-link');
    const navBar = document.getElementById('main-nav');
    if (logoutLink) {
        logoutLink.addEventListener('click', function(e) {
            e.preventDefault();
            // Show logout confirmation popup
            showLogoutConfirmationPopup();
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
        if (loggedIn) {
            if (navBar) navBar.style.display = '';
        } else {
            if (navBar) navBar.style.display = 'none';
        }

        const isAdmin = user && JSON.parse(user).is_admin;
        if (adminLink) {
            if (isAdmin) {
                adminLink.style.display = 'block';
            } else {
                adminLink.style.display = 'none';
            }
        }

        // Time-dependent greeting logic
        const greetingDiv = document.getElementById('greeting-message');
        if (greetingDiv && user) {
            let username = '';
            try {
                username = JSON.parse(user).username || '';
            } catch (e) {
                username = '';
            }
            if (username) {
                const now = new Date();
                const hour = now.getHours();
                let greeting = 'Hello';
                if (hour >= 5 && hour < 12) {
                    greeting = 'Good morning';
                } else if (hour >= 12 && hour < 18) {
                    greeting = 'Good afternoon';
                } else if (hour >= 18 && hour < 22) {
                    greeting = 'Good evening';
                } else {
                    greeting = 'Good night';
                }
                greetingDiv.textContent = `${greeting}, ${username}`;
                greetingDiv.style.display = 'block';
            } else {
                greetingDiv.style.display = 'none';
            }
        }
    } else {
        // if local storage has access token, refresh token and user, redirect to /dashboard
        const accessToken = localStorage.getItem('access_token');
        const refreshToken = localStorage.getItem('refresh_token');
        const user = localStorage.getItem('user');
        if (accessToken && refreshToken && user) {
            if (navBar) navBar.style.display = '';
            // redirect to /dashboard
            window.location.href = '/dashboard';
        }
        else {
            if (navBar) navBar.style.display = 'none';
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

// Token/user API helpers (refresh, get user, get policy, etc.)
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
        // Show session expired popup on refresh failure
        window.showSessionExpiredPopup();
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

// DRY API handler for token refresh and error handling
async function handleApiResponse({ url, method = 'GET', headers = {}, body = null, retry = true }) {
    const accessToken = localStorage.getItem('access_token');
    headers['Authorization'] = `Bearer ${accessToken}`;
    if (body && !headers['Content-Type']) {
        headers['Content-Type'] = 'application/json';
    }
    let response;
    try {
        response = await fetch(url, {
            method,
            headers,
            body: body ? JSON.stringify(body) : undefined
        });
    } catch (err) {
        return { success: false, status: 0, message: 'Network error', error: err };
    }
    if (response.ok) {
        const data = await response.json();
        return { success: true, data };
    } else if (response.status === 401 && retry) {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
            const refreshResponse = await window.refreshToken();
            if (refreshResponse) {
                // Retry once after refresh
                return await handleApiResponse({ url, method, headers, body, retry: false });
            }
        }
        // If refresh fails, show session expired popup
        window.showSessionExpiredPopup();
        return { success: false, status: 401, message: 'Session expired' };
    } else if ([400, 422].includes(response.status)) {
        let errorData;
        try {
            errorData = await response.json();
        } catch (e) {
            errorData = null;
        }
        return {
            success: false,
            status: response.status,
            message: window.extractApiErrorMessage(errorData),
            error: errorData
        };
    } else if (response.status === 404) {
        return { success: false, status: 404, message: 'Not found' };
    } else if (response.status === 409) {
        return { success: false, status: 409, message: 'Already Exists' };
    }
    return { success: false, status: response.status, message: 'Unknown error' };
}

// Refactored API functions for CRUD operations
async function createCarInsurancePolicy(data) {
    return await handleApiResponse({
        url: '/create_car_insurance_policy',
        method: 'POST',
        body: data
    });
}

async function updateCarInsurancePolicy(updateData) {
    return await handleApiResponse({
        url: '/update_car_insurance_policy',
        method: 'PUT',
        body: updateData
    });
}

async function deleteCarInsurancePolicy(policyId) {
    return await handleApiResponse({
        url: `/delete_car_insurance_policy?policy_id=${policyId}`,
        method: 'DELETE'
    });
}

async function updateUser(updateData) {
    return await handleApiResponse({
        url: '/update_user',
        method: 'PUT',
        body: updateData
    });
}

async function createUser(data) {
    return await handleApiResponse({
        url: '/create_user',
        method: 'POST',
        body: data
    });
}

// Populate optional extras in policy forms
async function populateOptionalExtras(policy, optionalsList, disabled = false) {
    if (optionalsList) {
        optionalsList.innerHTML = 'Loading...';
        const allExtras = await window.fetchAllOptionalExtras();
        let selectedExtras;
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
            // Show name and price
            label.appendChild(document.createTextNode(` ${extra.name} (£${Number(extra.price).toFixed(2)})`));
            optionalsList.appendChild(label);
        });
    }
}

async function updateUserPassword(userId, existingPassword, newPassword) {
    const accessToken = localStorage.getItem('access_token');
    const response = await fetch('/update_user_password', {
        method: 'PATCH',
        headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ user_id: userId, existing_password: existingPassword, new_password: newPassword })
    });
    if (response.ok) {
        const data = await response.json();
        console.log('Password updated successfully:', data);
        return data;
    } else if (response.status === 401) {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
            const refreshResponse = await window.refreshToken();
            if (refreshResponse) {
                return await updateUserPassword(userId, existingPassword, newPassword);
            }
        }
        console.error('Error updating password:', response.statusText);
    } else {
        const errorData = await response.json();
        console.error('Error updating password:', errorData);
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

// Utility: extract API error messages
function extractApiErrorMessage(error) {
    if (!error) return 'Unknown error.';
    if (typeof error === 'string') return error;
    if (error.message) return error.message;
    if (error.detail) return error.detail;
    if (error.response && error.response.data && error.response.data.message) return error.response.data.message;
    if (error.status === 422 && error.body) {
        // Pydantic validation error
        try {
            const body = typeof error.body === 'string' ? JSON.parse(error.body) : error.body;
            if (body && body.detail && Array.isArray(body.detail)) {
                return body.detail.map(e => e.msg).join('; ');
            }
        } catch (e) {}
        return 'Validation error (422).';
    }
    return 'An error occurred.';
}

// Show session expired popup and handle redirect
function showSessionExpiredPopup() {
    // Only show if not logging out
    if (window._isLoggingOut) return;
    // Clear tokens and user info
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    // Use the popup from base.html
    if (window.openPopup && window.closePopup) {
        const popupTitle = document.getElementById('popup-title');
        const popupBody = document.getElementById('popup-body');
        const popupClose = document.getElementById('popup-close');
        if (popupTitle) popupTitle.textContent = 'Session Expired';
        if (popupBody) {
            popupBody.innerHTML = '<p>Your session has expired. Please log in again.</p>' +
                '<button id="session-expired-ok-btn" class="login-again-btn">Login again</button>';
        }
        if (popupClose) {
            popupClose.style.display = 'none';
        }
        window.openPopup();
        setTimeout(() => {
            const okBtn = document.getElementById('session-expired-ok-btn');
            if (okBtn) {
                okBtn.onclick = function() {
                    window.closePopup();
                    window.location.href = '/';
                };
            }
        }, 0);
    } else {
        window.location.href = '/';
    }
}

// Show logout confirmation popup
function showLogoutConfirmationPopup() {
    const popupTitle = document.getElementById('popup-title');
    const popupBody = document.getElementById('popup-body');
    if (popupTitle) popupTitle.textContent = 'Confirm Logout';
    if (popupBody) {
        popupBody.innerHTML = `<p>Are you sure you want to log out?</p>
            <div style='text-align:center;margin-top:1em;'>
                <button id='logout-yes-btn' class='logout-btn'>Yes</button>
                <button id='logout-no-btn' class='logout-btn'>No</button>
            </div>`;
    }
    window.openPopup();
    setTimeout(() => {
        const yesBtn = document.getElementById('logout-yes-btn');
        const noBtn = document.getElementById('logout-no-btn');
        if (yesBtn) {
            yesBtn.onclick = function() {
                window._isLoggingOut = true; // Set flag before logout
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                localStorage.removeItem('user');
                window.closePopup();
                window.location.href = '/';
            };
        }
        if (noBtn) {
            noBtn.onclick = function() {
                window.closePopup();
            };
        }
    }, 0);
}
window.showLogoutConfirmationPopup = showLogoutConfirmationPopup;

// Export all helpers and API functions to window for global access
// Ensure availability of functions across different parts of the application
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
window.extractApiErrorMessage = extractApiErrorMessage;
window.handleApiResponse = handleApiResponse;
window.showSessionExpiredPopup = showSessionExpiredPopup;