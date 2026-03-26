const delayBetweenScans = 4000;

let scannerPaused = false;
const onScanSuccess = (qrMessage) => {
    if (scannerPaused) return;

    const accountId = qrMessage;
    scannerPaused = true;

    fetch(`/foreman_attendance/QRcamera/get-worker-info/${accountId}/`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Network response was not ok: ${response.statusText} (status: ${response.status})`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                let firstName = data.first_name;
                let lastName = data.last_name;
                let fullName;

                if (firstName !== "Not Provided" && lastName !== "Not Provided") {
                    fullName = `${firstName} ${lastName}`;
                } else if (firstName !== "Not Provided") {
                    fullName = firstName;
                } else if (lastName !== "Not Provided") {
                    fullName = lastName;
                } else {
                    fullName = "Not Provided";
                }

                document.querySelector(".worker_information").innerHTML = `
                    <div class="info_group"><h4>Full Name: </h4><p>${fullName}</p></div>
                    <div class="info_group"><h4>Age: </h4><p>${data.age} Years Old</p></div>
                    <div class="info_group"><h4>Gender: </h4><p>${data.gender}</p></div>
                    <div class="info_group"><h4>Contact: </h4><p>${data.contact}</p></div>
                    <div class="info_group"><h4>Address: </h4><p>${data.address}</p></div>
                `;
                
                return fetch(`/foreman_attendance/QRcamera/record-attendance/${accountId}/`);
            } else {
                throw new Error("Worker information not found.");
            }
        })
        .then(response => {
            if (!response.ok){
                return response.json().then(errorData => {
                    throw new Error(errorData.message || `Failed to record attendance: ${response.statusText}`);
                });
            }
            return response.json();
        })
        .then(attendanceData => {
            if (attendanceData.success) {
                Swal.fire({
                    position: "top-end",
                    icon: "success",
                    title: '<h2 style="font-size: 24px; margin: 0;">Attendance Recorded Successfully</h2>',
                    html: `<p style="font-size: 16px; color: #555; margin-top: 8px;">${attendanceData.message}</p>`,
                    showConfirmButton: false,
                    timer: 3000
                });
            } else {
                throw new Error(attendanceData.message || "Failed to record attendance.");
            }
        })
        .catch(error => {
            console.error("Error in onScanSuccess:", error);
            Swal.fire({
                icon: "error",
                title: "An error occurred",
                text: error.message || "Please try again."
            });
        });

    setTimeout(() => {
        scannerPaused = false;
    }, delayBetweenScans);
};

let errorDisplayed = false;

const onScanError = (errorMessage) => {
    if (!errorDisplayed) {
        Swal.fire({
            icon: "error",
            title: "No QR code detected",
            text: "Please try positioning the code properly.",
            timer: 1500,
            showConfirmButton: false
        });
        errorDisplayed = true;

        setTimeout(() => {
            errorDisplayed = false;
        }, 20000);
    }
};

const qrCodeScanner = new Html5Qrcode("qr-reader");
qrCodeScanner.start(
    { facingMode: "environment" },
    { fps: 10, qrbox: 300 },
    onScanSuccess,
    onScanError
);

