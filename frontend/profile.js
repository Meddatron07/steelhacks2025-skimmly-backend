let uploadedNotes = [];
let userProfile = null;

function handleNameEnter(event) {
    if (event.key === 'Enter') {
        event.target.blur();
    }
}

async function loadUserProfile() {
    try {
        const response = await fetch('https://steelhacks2025-skimmly-backend.onrender.com/api/profile', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`
            }
        });

        if (response.ok) {
            userProfile = await response.json();
            updateProfileDisplay();
        } else {
            console.error('Failed to load profile');
        }
    } catch (error) {
        console.error('Error loading profile:', error);
    }
}

function updateProfileDisplay() {
    if (!userProfile) return;

    // Update display elements
    document.getElementById('displayName').textContent = userProfile.username || 'Enter your name';
    document.getElementById('displayEducation').textContent = userProfile.education_level || 'Education not set';
    document.getElementById('displayPronouns').textContent = userProfile.pronouns || 'Pronouns not set';

    // Update form fields (for edit mode)
    document.getElementById('userName').value = userProfile.username || '';
    document.getElementById('educationLevel').value = userProfile.education_level || '';
    document.getElementById('pronouns').value = userProfile.pronouns || '';

    // Update stats
    document.getElementById('followersCount').textContent = userProfile.followers_count || 0;
    document.getElementById('followingCount').textContent = userProfile.following_count || 0;
    document.getElementById('likesCount').textContent = userProfile.notes_count * 15 || 0; // Simulate likes
}

async function saveProfile() {
    try {
        const profileData = {
            username: document.getElementById('userName').value,
            education_level: document.getElementById('educationLevel').value,
            pronouns: document.getElementById('pronouns').value
        };

        console.log('Saving profile data:', profileData);
        console.log('Auth token:', localStorage.getItem('authToken') ? 'Present' : 'Missing');

        const response = await fetch('https://steelhacks2025-skimmly-backend.onrender.com/api/profile', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`
            },
            body: JSON.stringify(profileData)
        });

        if (response.ok) {
            const updatedProfile = await response.json();
            userProfile = updatedProfile.user;
            updateProfileDisplay();
            console.log('Profile updated successfully');
        } else {
            const errorText = await response.text();
            console.error('Failed to save profile:', errorText);
            throw new Error(`Failed to save profile: ${response.status} ${errorText}`);
        }
    } catch (error) {
        console.error('Error saving profile:', error);
        throw error;
    }
}

        function showSection(section) {
            // Remove active class from all nav items
            document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
            // Add active class to clicked item
            event.target.classList.add('active');
           
            // Handle section switching logic here
            console.log('Switched to:', section);
        }

        function logout() {
            if (confirm('Are you sure you want to log out?')) {
                alert('Logging out...');
                // Add logout logic here
            }
        }

        function changeProfilePic() {
            document.getElementById('profilePicInput').click();
        }

        function changeCoverPhoto() {
            document.getElementById('coverPhotoInput').click();
        }

        function uploadNotes() {
            document.getElementById('notesInput').click();
        }

        function handleProfilePicChange(event) {
            const file = event.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const profileImg = document.getElementById('profileImage');
                    profileImg.src = e.target.result;
                    profileImg.classList.remove('hidden');
                    // Hide the emoji
                    profileImg.parentElement.style.fontSize = '0';
                };
                reader.readAsDataURL(file);
            }
        }

        function handleCoverPhotoChange(event) {
            const file = event.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const coverImg = document.getElementById('coverImage');
                    coverImg.src = e.target.result;
                    coverImg.classList.remove('hidden');
                };
                reader.readAsDataURL(file);
            }
        }

        function handleNotesUpload(event) {
            const files = event.target.files;
            for (let file of files) {
                if (file.type.startsWith('image/')) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        addNoteToGrid(e.target.result, file.name);
                    };
                    reader.readAsDataURL(file);
                }
            }
        }

        function addNoteToGrid(imageSrc, fileName) {
            const notesGrid = document.getElementById('notesGrid');
            const noteId = 'note_' + Date.now();
           
            const noteItem = document.createElement('div');
            noteItem.className = 'note-item';
            noteItem.id = noteId;
           
            noteItem.innerHTML = `
                <img src="${imageSrc}" alt="${fileName}" class="note-image">
                <div class="note-info">
                    <div class="note-title">${fileName}</div>
                    <div class="note-date">Uploaded ${new Date().toLocaleDateString()}</div>
                </div>
                <button class="delete-note" onclick="deleteNote('${noteId}')">×</button>
            `;
           
            notesGrid.appendChild(noteItem);
            uploadedNotes.push({ id: noteId, fileName: fileName, src: imageSrc });
        }

        function deleteNote(noteId) {
            if (confirm('Are you sure you want to delete this note?')) {
                document.getElementById(noteId).remove();
                uploadedNotes = uploadedNotes.filter(note => note.id !== noteId);
            }
        }

        function handleDragOver(event) {
            event.preventDefault();
            event.target.closest('.upload-area').classList.add('dragover');
        }

        function handleDragLeave(event) {
            event.target.closest('.upload-area').classList.remove('dragover');
        }

        function handleDrop(event) {
            event.preventDefault();
            event.target.closest('.upload-area').classList.remove('dragover');

            const files = event.dataTransfer.files;
            for (let file of files) {
                if (file.type.startsWith('image/')) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        addNoteToGrid(e.target.result, file.name);
                    };
                    reader.readAsDataURL(file);
                }
            }
        }

        // Edit mode functions
        function toggleEditMode() {
            const editableFields = document.getElementById('editableFields');
            const displayFields = document.getElementById('displayFields');
            const editBtn = document.getElementById('editProfileBtn');

            if (editableFields.classList.contains('hidden')) {
                // Enter edit mode
                editableFields.classList.remove('hidden');
                displayFields.classList.add('hidden');
                editBtn.textContent = '❌ Cancel';
                editBtn.onclick = cancelEdit;
            } else {
                // Exit edit mode
                exitEditMode();
            }
        }

        function exitEditMode() {
            const editableFields = document.getElementById('editableFields');
            const displayFields = document.getElementById('displayFields');
            const editBtn = document.getElementById('editProfileBtn');

            editableFields.classList.add('hidden');
            displayFields.classList.remove('hidden');
            editBtn.innerHTML = '✏️ Edit Profile';
            editBtn.onclick = toggleEditMode;
        }

        async function saveAndCloseEdit() {
            console.log('Save button clicked, starting save process...');
            try {
                console.log('Calling saveProfile()...');
                await saveProfile();
                console.log('Profile saved successfully, exiting edit mode...');
                exitEditMode();
            } catch (error) {
                console.error('Error saving profile:', error);
                alert('Failed to save profile. Please try again.');
            }
        }

        function cancelEdit() {
            // Reset fields to original values
            updateProfileDisplay();
            exitEditMode();
        }