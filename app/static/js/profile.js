document.addEventListener('DOMContentLoaded', async function () {
    const userProfile = document.getElementById('user-profile');
    const userInputs = document.getElementById('user-inputs');
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
        alert('User not found or unauthorized.');
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
        await window.updateUser(data);
        alert('Profile updated successfully.');
        // Optionally, refresh the page or update the UI
        window.location.reload();
    } catch (err) {
        alert('Failed to update profile.');
        console.error(err);
    }
});