document.addEventListener('DOMContentLoaded', function() {
    const usernameInput = document.querySelector('input[name="username"]');
    const submit = document.getElementById('submit')
    const another = document.getElementById('another')
    const feedbackDiv = document.createElement('div');
    feedbackDiv.classList.add('username-feedback');
    usernameInput.parentNode.appendChild(feedbackDiv);

    usernameInput.addEventListener('input', function() {
        const username = usernameInput.value;

        feedbackDiv.textContent = '';

        if (username.length > 0) {
            console.log(`Checking username: ${username}`);
            fetch(`/admin_accounts/add_accountPage/check-username/?username=${username}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.exists) {
                    feedbackDiv.textContent = 'Username already exists. Please choose another.';
                    feedbackDiv.style.color = '#ff0033'; 
                    usernameInput.style.border = '1px solid #ff0033';
                    submit.disabled = true;
                    another.disabled = true;
                }else{
                    usernameInput.style.border = '1px solid #4379F2';
                    submit.disabled = false;
                    another.disabled = false;
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        }else{
            usernameInput.style.border = '1px solid #cbcbcb';
        }    
    });
});
