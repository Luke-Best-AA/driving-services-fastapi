const errorElement = document.getElementById('form-login-error-msg');
const usernameInput = document.getElementById('username');
const passwordInput = document.getElementById('password');
const loginForm = document.getElementById('form-login');

// on document load set focus to username input
document.addEventListener('DOMContentLoaded', () => {
    document.body.style.display = 'block';
    usernameInput.focus();
});

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