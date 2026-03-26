document.addEventListener('DOMContentLoaded', () => {
    const projectContainer = document.getElementById("project_container");
    if (projectContainer) {
        projectContainer.addEventListener("submit", function (event) {
            event.preventDefault(); 

            const formData = new FormData(this);
            
            fetch(updateProjectUrl, {
                method: "POST",
                body: formData,
                headers: {
                    "X-CSRFToken": "{{ csrf_token }}",
                },
            })
            .then((response) => response.json())
            .then((data) => {
                if (data.success) {
                    Swal.fire({
                        position: "top-end",
                        icon: "success",
                        title: '<h2 style="font-size: 24px; margin: 0;">' + data.message + '</h2>',
                        showConfirmButton: false,
                        timer: 1500
                    }).then(() => {
                        window.location.reload(); 
                    });
                } else {
                    Swal.fire({
                        icon: "error",
                        title: "Error",
                        text: data.message || "There was an error with your submission",
                    });
                }
            })
            .catch((error) => {
                console.error("Error:", error);
                Swal.fire({
                    icon: "error",
                    title: "Oops...",
                    text: "Something went wrong!",
                });
            });
        });
    }

     const finalizeProjectBtn = document.getElementById("finalize_project_btn");

     if (finalizeProjectBtn) {
        finalizeProjectBtn.addEventListener("click", function (event) {
            event.preventDefault();

            const action = finalizeProjectBtn.classList.contains("finish_btn") ? "finalize" : "undo";
            const confirmText = action === "finalize"
                ? "This will mark the project as Finished."
                : "This will undo the finalization.";

            Swal.fire({
                title: "Are you sure?",
                text: confirmText,
                icon: "warning",
                showCancelButton: true,
                confirmButtonColor: "#3085d6",
                cancelButtonColor: "#d33",
                confirmButtonText: action === "finalize" ? "Yes, finish it!" : "Yes, undo it!"
            }).then((result) => {
                if (result.isConfirmed) {
                    fetch(finalizeProjectUrl, {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            "X-CSRFToken": getCookie("csrftoken")
                        },
                        body: JSON.stringify({ action: action })
                    })
                    .then(response => response.json())
                    .then(data => {
                        Swal.fire({
                            icon: data.success ? "success" : "error",
                            title: data.success ? "Success" : "Error",
                            text: data.message
                        }).then(() => {
                            if (data.success) {
                                location.reload();
                            }
                        });
                    })
                    .catch(error => {
                        console.error("Error:", error);
                        Swal.fire({
                            icon: "error",
                            title: "Oops...",
                            text: "Something went wrong!"
                        });
                    });
                }
            });
        });
    }


// Function to get CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

    // Initialize file upload behavior
    const initFileUpload = () => {
        const uploadInput = document.getElementById('upload');
        const fileNameDisplay = document.getElementById('file-name');

        if (uploadInput && fileNameDisplay) {
            uploadInput.addEventListener('change', (event) => {
                const file = event.target.files[0];
                fileNameDisplay.textContent = file ? `File Name: ${file.name}` : '';
            });
        }
    }

    initFileUpload();
});
