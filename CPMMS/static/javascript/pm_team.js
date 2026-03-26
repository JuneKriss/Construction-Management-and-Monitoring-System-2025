document.addEventListener("DOMContentLoaded", () => {
  const modal = document.getElementById("modal");
  const closeModal = document.getElementById("closeModal");
  const bonusModal = document.getElementById("bonus-modal");
  const deductionModal = document.getElementById("deduction-modal");
  const openBonusBtn = document.getElementById("open-bonus-modal");
  const openDeductionBtn = document.getElementById("open-deduction-modal");
  const closeBtns = document.querySelectorAll(".closeModal");

  const openModal = (modal) => {
    modal.style.display = "flex";
    document.body.classList.add("modal-open");
  };

  openBonusBtn.addEventListener("click", (e) => {
    e.preventDefault();
    openModal(bonusModal);
  });

  openDeductionBtn.addEventListener("click", (e) => {
    e.preventDefault();
    openModal(deductionModal);
  });

  closeBtns.forEach((btn) => {
    btn.addEventListener("click", (event) => {
      const modal = event.target.closest(".payrollModal");
      if (modal) {
        modal.style.display = "none";
        document.body.classList.remove("modal-open");
      }
    });
  });

  window.addEventListener("click", (event) => {
    if (event.target === modal) {
      modal.classList.remove("show");
      document.body.classList.remove("modal-open");
    }
    if (event.target === bonusModal) {
      bonusModal.style.display = "none";
      document.body.classList.remove("modal-open");
    }
    if (event.target === deductionModal) {
      deductionModal.style.display = "none";
      document.body.classList.remove("modal-open");
    }
  });

  document.addEventListener("click", (event) => {
    if (event.target.id === "openModalText") {
      const teamBox = event.target.closest(".team_box");
      const workerRow = event.target.closest("tr");

      const projectId = teamBox
        ? teamBox.getAttribute("data-project-id")
        : null;
      const workerId = workerRow
        ? workerRow.getAttribute("data-worker-id")
        : null;

      fetch(
        `/project-manager-team/project/${projectId}/worker/${workerId}/info/`
      )
        .then((response) => response.json())
        .then((data) => {
          let displayWorkerName = "";

          if (
            data.worker.first_name !== "Not Provided" &&
            data.worker.last_name === "Not Provided"
          ) {
            displayWorkerName = data.worker.first_name;
          }
          if (
            data.worker.last_name !== "Not Provided" &&
            data.worker.first_name === "Not Provided"
          ) {
            displayWorkerName = data.worker.last_name;
          }
          if (
            data.worker.first_name === "Not Provided" &&
            data.worker.last_name === "Not Provided"
          ) {
            displayWorkerName = "Names Not Provided";
          }
          if (
            data.worker.first_name !== "Not Provided" &&
            data.worker.last_name !== "Not Provided"
          ) {
            displayWorkerName = `${data.worker.first_name} ${data.worker.last_name}`;
          }

          document.querySelector("#modal .name h4").innerText =
            displayWorkerName + " " + "(" + `${data.worker.account}` + ")";
          document.querySelector("#modal .name span").innerText =
            data.worker.role;
          document.querySelector("#modal .info_box:nth-child(1) p").innerText =
            data.worker.address;
          document.querySelector("#modal .info_box:nth-child(2) p").innerText =
            data.worker.contact;
          document.querySelector(
            "#modal .body_title"
          ).innerText = `${data.project.name} - ${data.project.client}`;

          const tableBody = document.querySelector("#worker_attendance tbody");
          tableBody.innerHTML = "";

          if (data.worker.attendance && data.worker.attendance.length > 0) {
            data.worker.attendance.forEach((attendance) => {
              const row = document.createElement("tr");
              row.innerHTML = `
                                <td>${attendance.time_in}</td>
                                <td style="color: ${
                                  attendance.time_in_status === "Late"
                                    ? "red"
                                    : "green"
                                };">${attendance.time_in_status}</td>
                                <td>${attendance.time_out}</td>
                                <td>${attendance.date}</td>
                            `;
              tableBody.appendChild(row);
            });
          } else {
            const row = document.createElement("tr");
            row.innerHTML = `
                            <td colspan="4" style="text-align: center;">No Record of Recent Attendance</td>
                        `;
            tableBody.appendChild(row);
          }

          const tasksTableBody = document.querySelector(
            "#worker_progress tbody"
          );
          tasksTableBody.innerHTML = "";

          if (data.worker.tasks && data.worker.tasks.length > 0) {
            data.worker.tasks.forEach((task) => {
              const row = document.createElement("tr");
              row.innerHTML = `
                                <td>${task.task_name}</td>
                                <td>
                                    <div class="status-container">
                                        <span class="status-circle ${getTaskStatusClass(
                                          task.task_status
                                        )}"></span>
                                        <p class="${getTaskStatusTextClass(
                                          task.task_status
                                        )}">${task.task_status}</p>
                                    </div>
                                </td>
                                <td>${task.start_date}</td>
                                <td>${task.deadline}</td>
                            `;
              tasksTableBody.appendChild(row);
            });
          } else {
            const row = document.createElement("tr");
            row.innerHTML = `
                            <td colspan="4" style="text-align: center;">No Tasks Assigned</td>
                        `;
            tasksTableBody.appendChild(row);
          }

          const payrollLink = document.querySelector(".view-payroll-link");
          payrollLink.setAttribute("data-worker-id", workerId);
          payrollLink.setAttribute("data-project-id", projectId);

          document.querySelector(
            ".estimated-salary"
          ).innerText = `₱ ${data.worker.payroll.total_amount}`;
          document
            .querySelector(".view-payroll-link")
            .setAttribute(
              "href",
              `/project-manager-team/fetch-payroll-details/${workerId}/${projectId}/`
            );

          const bonusButton = document.querySelector("#open-bonus-modal");
          const deductionButton = document.querySelector(
            "#open-deduction-modal"
          );

          if (
            data.project.finalization_status === "Completed" &&
            data.project.isFinished
          ) {
            bonusButton.style.display = "none";
            deductionButton.style.display = "none";
          } else {
            bonusButton.style.display = "inline-block";
            deductionButton.style.display = "inline-block";
          }

          modal.classList.add("show");
          document.body.classList.add("modal-open");
        });
    }
  });

  closeModal.addEventListener("click", () => {
    modal.classList.remove("show");
    document.body.classList.remove("modal-open");
  });

  function getTaskStatusClass(status) {
    switch (status) {
      case "completed":
        return "status-completed";
      case "in_progress":
        return "status-in-progress";
      case "halfway":
        return "status-halfway";
      case "nearly_completed":
        return "status-nearly-completed";
      default:
        return "";
    }
  }

  function getTaskStatusTextClass(status) {
    switch (status) {
      case "completed":
        return "completed-text";
      case "in_progress":
        return "in-progress-text";
      case "halfway":
        return "halfway-text";
      case "nearly_completed":
        return "nearly-completed-text";
      default:
        return "";
    }
  }

  //Handle bonus form submission
  document
    .getElementById("bonusPayrollForm")
    .addEventListener("submit", function (event) {
      event.preventDefault();

      const bonusName = document.getElementById(
        "payroll-total-amount-bonus"
      ).value;
      const bonusAmount = document.getElementById("payroll-bonus").value;

      const payrollLink = document.querySelector(".view-payroll-link");
      const workerId = payrollLink.getAttribute("data-worker-id");
      const projectId = payrollLink.getAttribute("data-project-id");

      if (!bonusName || !bonusAmount) {
        Swal.fire("Error", "Please fill out all fields", "error");
        return;
      }

      fetch(`/project-manager-team/add-bonus/${projectId}/${workerId}/`, {
        method: "POST",
        headers: {
          "X-CSRFToken": getCSRFToken(),
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({
          payrollTotalAmountBonus: bonusName,
          payrollBonus: bonusAmount,
        }),
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.success) {
            Swal.fire({
              position: "top-end",
              icon: "success",
              title:
                '<h2 style="font-size: 24px; margin: 0;">Payroll Updated Successfully</h2>',
              html: `<p style="font-size: 16px; color: #555; margin-top: 8px;">${data.message}</p>`,
              showConfirmButton: false,
              timer: 1500,
            }).then(() => {
              location.reload();
            });
          } else {
            Swal.fire({
              position: "top-end",
              icon: "error",
              title: '<h2 style="font-size: 24px; margin: 0;">Error</h2>',
              html: `<p style="font-size: 16px; color: #555; margin-top: 8px;">${data.message}</p>`,
              showConfirmButton: false,
              timer: 1500,
            });
          }
        })
        .catch((error) => {
          Swal.fire("Error", "Something went wrong", "error");
          console.error("Error:", error);
        });
    });

  //Handle deduction form submission
  document
    .getElementById("deductionPayrollForm")
    .addEventListener("submit", function (event) {
      event.preventDefault();

      const deductionName = document.getElementById(
        "payroll-total-amount-deduction"
      ).value;
      const deductionAmount =
        document.getElementById("payroll-deduction").value;

      const payrollLink = document.querySelector(".view-payroll-link");
      const workerId = payrollLink.getAttribute("data-worker-id");
      const projectId = payrollLink.getAttribute("data-project-id");

      if (!deductionName || !deductionAmount) {
        Swal.fire("Error", "Please fill out all fields", "error");
        return;
      }

      fetch(`/project-manager-team/add-deduction/${projectId}/${workerId}/`, {
        method: "POST",
        headers: {
          "X-CSRFToken": getCSRFToken(),
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({
          payrollTotalAmountDeduction: deductionName,
          payrollDeduction: deductionAmount,
        }),
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.success) {
            Swal.fire({
              position: "top-end",
              icon: "success",
              title:
                '<h2 style="font-size: 24px; margin: 0;">Payroll Updated Successfully</h2>',
              html: `<p style="font-size: 16px; color: #555; margin-top: 8px;">${data.message}</p>`,
              showConfirmButton: false,
              timer: 1500,
            }).then(() => {
              location.reload();
            });
          } else {
            Swal.fire({
              position: "top-end",
              icon: "error",
              title: '<h2 style="font-size: 24px; margin: 0;">Error</h2>',
              html: `<p style="font-size: 16px; color: #555; margin-top: 8px;">${data.message}</p>`,
              showConfirmButton: false,
              timer: 1500,
            });
          }
        })
        .catch((error) => {
          Swal.fire({
            position: "top-end",
            icon: "error",
            title: '<h2 style="font-size: 24px; margin: 0;">Error</h2>',
            html: `<p style="font-size: 16px; color: #555; margin-top: 8px;">Something went wrong</p>`,
            showConfirmButton: false,
            timer: 1500,
          });
          console.error("Error:", error);
        });
    });

  // Function to get CSRF token
  function getCSRFToken() {
    return document.querySelector("[name=csrfmiddlewaretoken]").value;
  }

  /*
    document.querySelector('#updatePayrollForm').addEventListener('submit', function (e) {
        e.preventDefault();
    
        const workerId = document.querySelector('.view-payroll-link').getAttribute('data-worker-id');
        const projectId = document.querySelector('.view-payroll-link').getAttribute('data-project-id');
        const bonus = document.getElementById('payroll-bonus').value;
        const deductions = document.getElementById('payroll-deductions').value;
        
        fetch(`/project-manager-team/fetch-payroll-details/update-payroll/${workerId}/${projectId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: new URLSearchParams({
                updatePayrollBonus: bonus,
                updatePayrollDeductions: deductions,

            })
        })
        .then(response => {
            console.log("Response received:", response);
            return response.json();
        })
        .then(data => {
            if (data.message) {
                Swal.fire({
                    position: "top-end",
                    icon: "success",
                    title: '<h2 style="font-size: 24px; margin: 0;">Payroll Updated Successfully</h2>',
                    html: `<p style="font-size: 16px; color: #555; margin-top: 8px;">${data.message}</p>`,
                    showConfirmButton: false,
                    timer: 1500
                }).then(() => {
                    location.reload();
                });
    
                document.getElementById('payroll-modal').style.display = 'none';
            } else {
                throw new Error(data.error || "Failed to update payroll.");
            }
        })
        .catch(error => {
            console.error("Error:", error);
            Swal.fire({
                icon: "error",
                title: "An error occurred",
                text: error.message || "Please try again."
            });
        });
    });
    
    function getCookie(name) {
        const cookieValue = document.cookie.match(`(^|;)\\s*${name}\\s*=\\s*([^;]+)`);
        return cookieValue ? cookieValue.pop() : '';
    }
    */
});
