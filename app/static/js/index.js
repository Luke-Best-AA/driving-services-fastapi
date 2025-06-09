// Login and registration page script
// Handles login form submission, registration popup, and popup UI logic
// Uses localStorage for session tokens and user info
// Provides helper functions for showing popups and handling registration
//
const errorElement = document.getElementById('form-login-error-msg');
const usernameInput = document.getElementById('username');
const passwordInput = document.getElementById('password');
const loginForm = document.getElementById('form-login');
const showRegisterLink = document.getElementById('show-register-link');
const popupOverlay = document.getElementById('popup-overlay');
const popupContainer = document.getElementById('popup-container');
const popupContent = document.getElementById('popup-content');
const popupClose = document.getElementById('popup-close');
const popupTitle = document.getElementById('popup-title');
const popupBody = document.getElementById('popup-body');

// On document load, set focus to username input and show body
document.addEventListener('DOMContentLoaded', () => {
    document.body.style.display = 'block';
    usernameInput.focus();
});

// Login form submission: hashes password, sends to backend, handles response
loginForm.addEventListener('submit', async function(event) {
    event.preventDefault();

    const form = event.target;
    const formData = new FormData(form);
    // get the username and password from the form md5 hash the password
    const username = formData.get('username');
    const password = formData.get('password');
    const hashedPassword = md5(password);
    // set the password to the hashed password
    formData.set('password', hashedPassword);

    const response = await fetch('/token', {
        method: 'POST',
        body: formData
    });

    // Handle response as needed
    if (response.ok) {
        const data = await response.json();
        access_token = data.access_token;
        refresh_token = data.refresh_token;
        user = data.user;
        // Store tokens in local storage
        localStorage.setItem('access_token', access_token);
        localStorage.setItem('refresh_token', refresh_token);
        localStorage.setItem('user', JSON.stringify(user));
        // Redirect to the home page
        window.location.href = '/dashboard';
    } else {
        // get the error message from the json response
        const errorData = await response.json();
        const errorMessage = errorData.detail || 'Login failed';
        passwordInput.value = '';
        // put the error message in the login form
        errorElement.innerText = errorMessage;
        errorElement.style.display = 'block';
    }
});

// Helper to show popup with title and body
function showPopup(title, bodyHtml) {
    popupTitle.textContent = title;
    popupBody.innerHTML = bodyHtml;
    window.openPopup();
}

// Show register popup when link clicked, attach submit handler
showRegisterLink.addEventListener('click', function(e) {
    e.preventDefault();
    const template = document.getElementById('register-form-template');
    window.showPopup('Register', template.innerHTML);
    // Focus username
    setTimeout(() => {
        const regUser = document.getElementById('register-username');
        if (regUser) regUser.focus();
    }, 100);
    // Add submit handler
    const regForm = document.getElementById('form-register');
    regForm.addEventListener('submit', handleRegisterSubmit);
});

// Registration handler: validates, sends to backend, shows result in popup
async function handleRegisterSubmit(event) {
    event.preventDefault();
    const form = event.target;
    const username = form.querySelector('#register-username').value.trim();
    const password = form.querySelector('#register-password').value;
    const password2 = form.querySelector('#register-password2').value;
    const email = form.querySelector('#register-email').value.trim();
    const isAdmin = form.querySelector('#register-is-admin').checked;
    const errorMsg = document.getElementById('form-register-error-msg');
    errorMsg.innerText = '';
    // Simple client validation
    if (!username || !password || !password2 || !email) {
        errorMsg.innerText = 'All fields are required.';
        return;
    }
    if (password !== password2) {
        errorMsg.innerText = 'Passwords do not match.';
        return;
    }
    // Prepare JSON body for API
    const body = {
        user_id: 0,
        username: username,
        password: md5(password),
        email: email,
        is_admin: isAdmin
    };
    try {
        const response = await fetch('/register_user', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(body)
        });
        if (response.ok) {
            // Success: show success message using main.js popup logic
            if (window.showPopup) {
                window.showPopup('Registration Successful', '<div class="register-success-msg">Registration successful! Please log in.</div>');
                setTimeout(() => window.hidePopup && window.hidePopup(), 2000);
            }
        } else {
            const errorData = await response.json();
            errorMsg.innerText = errorData.detail || 'Registration failed.';
        }
    } catch (err) {
        errorMsg.innerText = 'Network error.';
    }
}