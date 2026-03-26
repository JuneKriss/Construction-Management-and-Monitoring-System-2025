document.getElementById("projectForm").addEventListener("submit", function (event) {
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
                title: '<h2 style="font-size: 24px; margin: 0;">Project Updated Successfully</h2>',
                html: `<p style="font-size: 16px; color: #555; margin-top: 8px;">${data.message}</p>`,
                showConfirmButton: false,
                timer: 1500
            }).then(() => {
                location.reload();
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


document.addEventListener('DOMContentLoaded', () => {
    initModal();
    initFileUpload();
});

const initModal = () => {
    const modal = document.getElementById("imageModal");
    const modalImg = document.getElementById("modalImage");
    const closeBtn = document.getElementById("closeModal");

    const openModalWithImage = (src) => {
        modal.style.display = "flex";
        modalImg.src = src;
    };

    const contractImg = document.getElementById("contract");
    contractImg.addEventListener('click', () => {
        openModalWithImage(contractImg.src);
    });

    const timeframeImg = document.getElementById("timeframe");
    timeframeImg.addEventListener('click', () => {
        openModalWithImage(timeframeImg.src);
    });

    closeBtn.addEventListener('click', () => {
        modal.style.display = "none";
    });

    window.addEventListener('click', (event) => {
        if (event.target === modal) {
            modal.style.display = "none";
        }
    });
};

const initFileUpload = () => {
    const uploadInput = document.getElementById('upload');
    const fileNameDisplay = document.getElementById('file-name');

    uploadInput.addEventListener('change', (event) => {
        const file = event.target.files[0]; // Get the first file
        fileNameDisplay.textContent = file ? file.name : ''; // Display the file name or clear
    });
}
