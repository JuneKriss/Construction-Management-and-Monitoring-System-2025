const togglePassword = (inputId, iconElement) => {
    const passwordInput = document.getElementById(inputId);

    if (passwordInput.type === "password") {
        passwordInput.type = "text";
        iconElement.textContent = "visibility_off";
    } else {
        passwordInput.type = "password";
        iconElement.textContent = "visibility";
    }
}

document.addEventListener("DOMContentLoaded", function() {
    const messageElements = document.querySelectorAll('#message-container > div');
    messageElements.forEach(element => {
        const text = element.dataset.message;
        const tags = element.dataset.tags;

        if (tags === 'success') {
            Swal.fire({
                position: "top-end",
                icon: "success",
                title: text,
                showConfirmButton: false,
                timer: 1500,
                customClass: {
                    title: 'swal-title'
                }
            });
        } else if (tags === 'error') {
            Swal.fire({
                icon: "error",
                title: "Error",
                text: text,
                confirmButtonColor: "#4379F2",
            });
        }
    });
});

document.getElementById('upload').addEventListener('change', handleFileUpload);
document.getElementById('remove-btn').addEventListener('click', (e) => {
    e.preventDefault();
    e.stopPropagation();
    removeFile();
});

function handleFileUpload() {
    const uploadInput = document.getElementById('upload');
    const fileNameDisplay = document.getElementById('file-name');
    const removeButton = document.getElementById('remove-btn');
    
    if (uploadInput.files.length > 0) {
        const fileName = uploadInput.files[0].name;
        fileNameDisplay.textContent = `Selected file: ${fileName}`;
        removeButton.style.display = 'inline-block';
    } else {
        fileNameDisplay.textContent = "";
        removeButton.style.display = 'none';
    }
}

function removeFile() {
    const uploadInput = document.getElementById('upload');
    const fileNameDisplay = document.getElementById('file-name');
    const removeButton = document.getElementById('remove-btn');
    
    uploadInput.value = "";
    fileNameDisplay.textContent = "";
    removeButton.style.display = 'none';
}


