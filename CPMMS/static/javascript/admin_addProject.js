const today = new Date().toISOString().split('T')[0];

document.getElementById('start').setAttribute('min', today);
document.getElementById('end').setAttribute('min', today);

document.querySelector("#registerProjectForm").addEventListener("submit", function(event) {
    event.preventDefault(); 

    const formData = new FormData(this);
    const url = this.getAttribute("action");
    const redirectUrl = this.getAttribute("data-redirect-url");
    const csrfToken = "{{ csrf_token }}";

    fetch(url, {
        method: "POST",
        body: formData,
        headers: {
            "X-CSRFToken": csrfToken,
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            Swal.fire({
                icon: "success",
                title: "Success",
                text: data.message,
                timer: 1300,
                showConfirmButton: false
            }).then(() => {
                window.location.href = redirectUrl;
            });
        } else {
            Swal.fire({
                icon: "error",
                title: "An error occurred",
                text: data.message || "Please try again."
            });
        }
    })
    .catch(error => {
        Swal.fire({
            icon: "error",
            title: "An error occurred",
            text: error.message || "Please try again."
        });
    });
});
