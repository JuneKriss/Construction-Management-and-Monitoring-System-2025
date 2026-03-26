    const qrModal = document.getElementById("qrModal");

    const qr_code = document.getElementById("qr_code");
    const modalImg_qr = document.getElementById("qrImg");

    qr_code.addEventListener('click', function() {
        qrModal.style.display = "flex";
        modalImg_qr.src = this.src;   
    });
        

    const span = document.getElementsByClassName("close")[0];

    span.addEventListener('click', function() {
        qrModal.style.display = "none";
    });

