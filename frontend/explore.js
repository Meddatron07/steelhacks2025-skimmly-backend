let currentPost = '';
        let savedDownloads = ['slope-notes.pdf', 'chemical-bonds.pdf'];
       
        // Sample comments data
        const commentsData = {
            post1: [
                {author: 'Emma Wilson', text: 'Great explanation! Really helped me understand slope better.'},
                {author: 'Mike Johnson', text: 'The visual representation makes it so clear. Thanks for sharing!'},
                {author: 'Lisa Chen', text: 'Could you do one on derivatives next?'}
            ],
            post2: [
                {author: 'David Brown', text: 'Perfect lab setup diagram!'},
                {author: 'Anna Davis', text: 'This is exactly what I needed for my chemistry practical. Thank you!'}
            ],
            post3: [
                {author: 'Tom Wilson', text: 'Comprehensive timeline. Very helpful for history class.'},
                {author: 'Rachel Green', text: 'Great resource! The dates are clearly organized.'}
            ],
            post4: [
                {author: 'Kevin Park', text: 'Amazing detail on the organelles!'},
                {author: 'Sophie Martinez', text: 'Perfect for my biology exam prep. Love the clear labeling!'}
            ],
            post5: [
                {author: 'Lucy Wang', text: 'This saved my physics grade! Newton\'s laws finally make sense.'},
                {author: 'Marcus Thompson', text: 'Great examples and practice problems. Very thorough!'},
                {author: 'Nina Patel', text: 'Perfect for AP Physics. Thank you so much!'}
            ],
            post6: [
                {author: 'Oliver Smith', text: 'Shakespeare analysis is spot on! Helped with my essay.'},
                {author: 'Grace Liu', text: 'Love the character studies. Very insightful.'}
            ],
            post7: [
                {author: 'James Rodriguez', text: 'Finally, statistics formulas that are easy to understand!'},
                {author: 'Maya Gupta', text: 'This formula sheet is a lifesaver. Bookmarked!'}
            ],
            post8: [
                {author: 'Isabella Cruz', text: '¡Excelente! This really helps with verb conjugations.'},
                {author: 'Antonio Silva', text: 'Perfect reference guide. Muy útil!'}
            ],
            post9: [
                {author: 'Alex Chang', text: 'This is gold for coding interviews! Thanks for sharing.'},
                {author: 'Taylor Brooks', text: 'Data structures finally make sense. Great visual explanations.'},
                {author: 'Priya Sharma', text: 'Using this for my CS midterm. Super helpful!'}
            ],
            post10: [
                {author: 'Nathan Lee', text: 'Economics concepts explained so clearly!'},
                {author: 'Samantha Davis', text: 'Perfect graph for understanding market equilibrium.'}
            ]
        };

        function openFile(filename) {
            // Simulate opening file preview or full view
            alert(`Opening ${filename}...`);
            // In a real app, this would open a file viewer modal or new page
        }

        function showPage(pageId) {
            // Hide all pages
            const pages = document.querySelectorAll('.page');
            pages.forEach(page => page.classList.remove('active'));
           
            // Show selected page
            document.getElementById(pageId).classList.add('active');
           
            // Update sidebar active state (optional enhancement)
            document.querySelectorAll('.nav-item').forEach(item => {
                item.style.backgroundColor = '';
                item.style.color = '#2c5f7a';
            });
        }

        function goToProfile(userId) {
            // In a real app, this would navigate to the specific user's profile
            // For demo purposes, we'll just show an alert
            alert(`Navigating to ${userId}'s profile...`);
        }

        function toggleLike(button) {
            const likeCount = button.querySelector('.like-count');
            let count = parseInt(likeCount.textContent);
           
            if (button.classList.contains('liked')) {
                button.classList.remove('liked');
                likeCount.textContent = count - 1;
                button.style.color = '#666';
            } else {
                button.classList.add('liked');
                likeCount.textContent = count + 1;
                button.style.color = '#e74c3c';
            }
        }

        function openComments(postId) {
            currentPost = postId;
            const modal = document.getElementById('commentsModal');
            const commentsSection = document.getElementById('commentsSection');
           
            // Clear existing comments
            commentsSection.innerHTML = '';
           
            // Load comments for this post
            const comments = commentsData[postId] || [];
            comments.forEach(comment => {
                const commentDiv = document.createElement('div');
                commentDiv.className = 'comment';
                commentDiv.innerHTML = `
                    <div class="comment-avatar"></div>
                    <div class="comment-content">
                        <div class="comment-author">${comment.author}</div>
                        <div class="comment-text">${comment.text}</div>
                    </div>
                `;
                commentsSection.appendChild(commentDiv);
            });
           
            modal.style.display = 'block';
        }

        function closeComments() {
            document.getElementById('commentsModal').style.display = 'none';
            document.getElementById('commentInput').value = '';
        }

        function addComment() {
            const input = document.getElementById('commentInput');
            const text = input.value.trim();
           
            if (text) {
                // Add comment to data
                if (!commentsData[currentPost]) {
                    commentsData[currentPost] = [];
                }
                commentsData[currentPost].push({
                    author: 'You',
                    text: text
                });
               
                // Refresh comments display
                openComments(currentPost);
               
                // Clear input
                input.value = '';
               
                // Update comment count in post
                updateCommentCount(currentPost);
            }
        }

        function updateCommentCount(postId) {
            // This would update the comment count display in the post
            // For demo purposes, we'll just show an alert
            console.log(`Comment added to ${postId}`);
        }

        function downloadFile(filename) {
            // Add to saved downloads if not already there
            if (!savedDownloads.includes(filename)) {
                savedDownloads.push(filename);
            }
           
            // Update download count
            const downloadButtons = document.querySelectorAll('.download-btn');
            downloadButtons.forEach(btn => {
                if (btn.onclick.toString().includes(filename)) {
                    const countSpan = btn.parentElement.querySelector('.download-count');
                    if (countSpan) {
                        let count = parseInt(countSpan.textContent);
                        countSpan.textContent = count + 1;
                    }
                }
            });
           
            alert(`Downloading ${filename}...`);
        }

        function handleFileUpload() {
            const files = document.getElementById('fileInput').files;
            if (files.length > 0) {
                alert(`Uploading ${files.length} file(s)...`);
                // Here you would handle the actual file upload
            }
        }

        function logout() {
            if (confirm('Are you sure you want to log out?')) {
                alert('Logging out')
            }
        }