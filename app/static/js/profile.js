document.addEventListener('DOMContentLoaded', async function () {
    const userProfile = document.getElementById('user-profile');
    const userInputs = document.getElementById('user-inputs');
    const userInputForm = document.getElementById('user-input-form');
    const userProfileDetail = document.getElementById('user-profile-detail');

    if (userProfile) {
        userProfile.style.display = 'none';
    }

    if (userInputs) {
        userInputs.style.display = 'none';
    }

    // Get user info using the global method
    const user = await window.getUserByMyself();
    if (!user) {
        window.showSessionExpiredPopup();
        console.error('No user found');
        return;
    }

    if (!userProfileDetail || !userProfile) {
        console.error('Template or container not found');
        return;
    }

    // Prepare the HTML by replacing placeholders
    let role = user.is_admin ? 'Admin' : 'User';
    let html = userProfileDetail.innerHTML
        .replace(/\[username\]/g, user.username || '')
        .replace(/\[email\]/g, user.email || '')
        .replace(/\[role\]/g, role);

    // Insert into the container
    userProfile.innerHTML = html;
    userProfile.style.display = 'block'; // Show the profile card

    // Set values in the hidden inputs
    document.getElementById('user-id').value = user.user_id || '';
    document.getElementById('username').value = user.username || '';
    document.getElementById('email').value = user.email || '';
    document.getElementById('role').value = role;
    // Set visible, non-editable role field
    const roleDisplay = document.getElementById('role-display');
    if (roleDisplay) {
        roleDisplay.value = role;
    }

    // --- Tab toggle logic ---
    const viewBtn = document.getElementById('view-details-btn');
    const changeBtn = document.getElementById('change-details-btn');

    if (viewBtn && changeBtn && userProfile && userInputs) {
        viewBtn.addEventListener('click', function () {
            viewBtn.classList.add('active');
            changeBtn.classList.remove('active');
            userProfile.style.display = 'block';
            userInputs.style.display = 'none';
        });

        changeBtn.addEventListener('click', function () {
            changeBtn.classList.add('active');
            viewBtn.classList.remove('active');
            userProfile.style.display = 'none';
            userInputs.style.display = 'block';
        });
    }

    const changePasswordBtn = document.getElementById('change-password-btn');
    const updatePasswordForm = document.getElementById('update-password-form');
    if (changePasswordBtn) {
        changePasswordBtn.addEventListener('click', function () {
            userInputForm.style.display = 'none';
            if (updatePasswordForm) {
                updatePasswordForm.style.display = 'block';
            }
        });
    }

    if (updatePasswordForm) {
        updatePasswordForm.addEventListener('submit', async function (e) {
            e.preventDefault();
            const currentPassword = md5(document.getElementById('current-password').value);
            const newPassword = md5(document.getElementById('new-password').value);
            const confirmPassword = md5(document.getElementById('confirm-password').value);

            if (newPassword !== confirmPassword) {
                alert('Passwords do not match.');
                return;
            }

            try {
                await window.updateUserPassword(user.user_id, currentPassword, newPassword);
                alert('Password updated successfully.');
                // Optionally, refresh the page or update the UI
                window.location.reload();
            } catch (err) {
                alert('Failed to update password.');
                console.error(err);
            }
        });
    }

    const cancelPasswordBtn = document.getElementById('cancel-password-btn');

    if (cancelPasswordBtn) {
        cancelPasswordBtn.addEventListener('click', function () {
            if (updatePasswordForm) {
                updatePasswordForm.style.display = 'none';
            }
            userInputForm.style.display = 'block';
        });
    }
});

document.getElementById('user-input-form')?.addEventListener('submit', async function (e) {
    e.preventDefault();

    const userId = document.getElementById('user-id').value;
    const username = document.getElementById('username').value;
    const email = document.getElementById('email').value;
    const password = document.getElementById('password')?.value || '';
    // Get is_admin from the current user info
    const user = await window.getUserById(userId);
    if (!user) {
        showProfileError('User not found or unauthorized.');
        return;
    }

    const data = {
        user_id: Number(userId),
        username: username,
        password: password,
        email: email,
        is_admin: !!user.is_admin
    };

    try {
        const result = await window.updateUser(data);
        if (result && result.success) {
            showProfileSuccess('Profile updated successfully.');
            setTimeout(() => {
                window.location.reload();
            }, 800);
        } else {
            showProfileError(window.extractApiErrorMessage(result && result.data ? result.data : result && result.message));
        }
    } catch (err) {
        showProfileError(window.extractApiErrorMessage(err));
        console.error(err);
    }
});

// Helper functions to show error/success messages
function showProfileError(msg) {
    let errorDiv = document.getElementById('profile-error-msg');
    if (errorDiv) {
        errorDiv.textContent = msg;
        errorDiv.style.display = 'block';
    }
    let successDiv = document.getElementById('profile-success-msg');
    if (successDiv) successDiv.style.display = 'none';
}
function showProfileSuccess(msg) {
    let successDiv = document.getElementById('profile-success-msg');
    if (successDiv) {
        successDiv.textContent = msg;
        successDiv.style.display = 'block';
    }
    let errorDiv = document.getElementById('profile-error-msg');
    if (errorDiv) errorDiv.style.display = 'none';
}