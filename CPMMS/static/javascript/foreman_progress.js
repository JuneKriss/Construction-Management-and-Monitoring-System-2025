document.addEventListener("DOMContentLoaded", function () {
  const detailsModal = document.getElementById("taskDetailsModal");
  const closeModalButtons = document.querySelectorAll(".closeModal");
  const detailsProgressFill = document.getElementById("detailsProgressFill");
  const detailsProgressPercentage = document.getElementById(
    "detailsProgressPercentage"
  );
  const startDateInput = document.getElementById("start_date");
  const dueDateInput = document.getElementById("due_date");
  const assigneeBody = document.getElementById("assignee-body");
  const workerProgressInput = document.getElementById("worker_progress");
  const percentFromInput = document.getElementById("percentage_from_project");
  const remarksTextarea = document.getElementById("remarks");
  const projectSelect = document.getElementById("projects");
  const progressBar = document.getElementById("progress-bar");
  const progressFill = document.getElementById("ProgressFill");
  const progressPercentage = document.getElementById("ProgressPercentage");
  let currentTaskId = null;
  const editButton = document.querySelector(".edit_btn");
  const saveButton = document.querySelector(".save_btn");

  const openDetailsModal = (taskId) => {
    currentTaskId = taskId;
    fetch(`/foreman_progress/get-task-details/${taskId}/`)
      .then((response) => response.json())
      .then((data) => {
        document.querySelector(".head_title h2").textContent = data.task_name;

        detailsProgressFill.style.width = `${data.worker_progress}%`;
        detailsProgressPercentage.textContent = `${data.worker_progress}%`;

        startDateInput.value = data.start_date;
        dueDateInput.value = data.deadline;

        assigneeBody.innerHTML = "";
        data.workers.forEach((worker) => {
          const workerFName = worker.Fname || "Not Provided";
          const workerLName = worker.Lname || "Not Provided";
          const workerRole = worker.role;
          const workerId = worker.worker_id;

          let displayWorkerName = "";

          if (
            workerFName !== "Not Provided" &&
            workerLName === "Not Provided"
          ) {
            displayWorkerName = workerFName;
          } else if (
            workerLName !== "Not Provided" &&
            workerFName === "Not Provided"
          ) {
            displayWorkerName = workerLName;
          } else if (
            workerFName === "Not Provided" &&
            workerLName === "Not Provided"
          ) {
            displayWorkerName = "Names Not Provided";
          } else {
            displayWorkerName = `${workerFName} ${workerLName}`;
          }

          const row = document.createElement("tr");
          row.dataset.workerId = workerId;
          row.innerHTML = `
                        <td>${displayWorkerName} (${worker.account_name})</td>
                        <td>${workerRole}</td>
                    `;
          assigneeBody.appendChild(row);
        });

        workerProgressInput.value = data.worker_progress;
        percentFromInput.value = data.percent_from;
        remarksTextarea.value = data.remarks || "";

        const saveChangesButton = document.querySelector(".submit");

        if (data.can_edit) {
          workerProgressInput.readOnly = false;
          remarksTextarea.readOnly = false;
          percentFromInput.readOnly = false;
          saveChangesButton.style.display = "inline-block";
          editButton.style.display = "none";
        } else {
          remarksTextarea.value = data.remarks;
          workerProgressInput.readOnly = true;
          remarksTextarea.readOnly = true;
          percentFromInput.readOnly = true;
          editButton.style.display = "inline-block";
          saveChangesButton.style.display = "none";
        }

        updateTaskStatus(data.task_status);

        detailsModal.style.display = "flex";
      })
      .catch((error) => console.error("Error fetching task details:", error));
  };

  const closeDetailsModal = () => {
    detailsModal.style.display = "none";
    saveButton.style.display = "none";

    workerProgressInput.style.border = "1px solid #c1c1c1";
    percentFromInput.style.border = "1px solid #c1c1c1";
    remarksTextarea.style.border = "1px solid #c1c1c1";
  };

  document
    .getElementById("task-table-body")
    .addEventListener("click", function (e) {
      if (e.target.classList.contains("openModal")) {
        const taskId = e.target.dataset.taskId;
        openDetailsModal(taskId);
      }
    });

  closeModalButtons.forEach((button) => {
    button.addEventListener("click", closeDetailsModal);
  });

  window.onclick = function (event) {
    if (event.target === detailsModal) {
      closeDetailsModal();
    }
  };

  editButton.addEventListener("click", () => {
    workerProgressInput.readOnly = false;
    remarksTextarea.readOnly = false;
    percentFromInput.readOnly = false;

    workerProgressInput.style.border = "1px solid #4379f2";
    remarksTextarea.style.border = "1px solid #4379f2";
    percentFromInput.style.border = "1px solid #4379f2";

    saveButton.style.display = "inline-block";
    editButton.style.display = "none";
  });

  /**
   * Function to update the task status inside the modal
   */
  const updateTaskStatus = (status) => {
    const taskStatus = document.querySelector(".task_status");
    const taskCircle = taskStatus.querySelector(".status-circle");
    const taskText = taskStatus.querySelector("p");

    // Clear existing status classes
    taskCircle.className = "status-circle";
    taskText.className = "";

    switch (status) {
      case "not_started":
        taskCircle.classList.add("status-not-started");
        taskText.classList.add("not-started-text");
        taskText.textContent = "Not Started";
        break;
      case "in_progress":
        taskCircle.classList.add("status-in-progress");
        taskText.classList.add("in-progress-text");
        taskText.textContent = "In Progress";
        break;
      case "halfway":
        taskCircle.classList.add("status-halfway");
        taskText.classList.add("halfway-text");
        taskText.textContent = "Halfway Completed";
        break;
      case "nearly_completed":
        taskCircle.classList.add("status-nearly-completed");
        taskText.classList.add("nearly-completed-text");
        taskText.textContent = "Nearly Completed";
        break;
      case "completed":
        taskCircle.classList.add("status-completed");
        taskText.classList.add("completed-text");
        taskText.textContent = "Completed";
        break;
      default:
        taskText.textContent = "Unknown Status";
        break;
    }
  };

  ///////////////////////////////////////////////////////////////////////////////////////////////////////////////// SEARCH FUNCTION
  const searchTasks = () => {
    const query = document.getElementById("search").value;

    fetch(`/foreman_progress/search-tasks/?query=${encodeURIComponent(query)}`)
      .then((response) => response.json())
      .then((data) => {
        const tableBody = document.getElementById("task-table-body");
        tableBody.innerHTML = "";

        if (data.tasks.length > 0) {
          data.tasks.forEach((task) => {
            const row = document.createElement("tr");
            row.classList.add("table_row");

            row.innerHTML = `
                            <td colspan="2">${task.task_name}</td>
                            <td>
                                <div class="status-container">
                                    ${task.progress_status}
                                </div>
                            </td>
                            <td>${task.deadline}</td>
                            <td>${task.worker_progress}%</td>
                            <td>
                                ${
                                  task.workers.length > 0
                                    ? task.workers
                                        .slice(0, 2)
                                        .map((worker) => {
                                          if (
                                            worker.first_name !==
                                              "Not Provided" &&
                                            worker.last_name !== "Not Provided"
                                          ) {
                                            return `${worker.first_name} ${worker.last_name}`;
                                          } else if (
                                            worker.first_name !== "Not Provided"
                                          ) {
                                            return worker.first_name;
                                          } else if (
                                            worker.last_name !== "Not Provided"
                                          ) {
                                            return worker.last_name;
                                          } else {
                                            return "Names Not Provided";
                                          }
                                        })
                                        .join(", ")
                                    : "Names Not Provided"
                                }
                                ${
                                  task.workers.length > 2
                                    ? `<span class="worker_count">+${
                                        task.workers.length - 2
                                      } more workers</span>`
                                    : ""
                                }
                            </td>
                            <td><a href="#" class="btn">View</a></td>
                        `;
            tableBody.appendChild(row);
          });
        } else {
          const noTasksRow = document.createElement("tr");
          noTasksRow.innerHTML =
            '<td colspan="7">No tasks made by this Foreman.</td>';
          tableBody.appendChild(noTasksRow);
        }
      })
      .catch((error) => console.error("Error:", error));
  };

  document.getElementById("search").addEventListener("input", searchTasks);
  ///////////////////////////////////////////////////////////////////////////////////////////////////////////////// SEARCH FUNCTION

  ///////////////////////////////////////////////////////////////////////////////////////////////////////////////// MODAL FORM SUBMIT
  document
    .querySelector(".submit")
    .addEventListener("click", async function (event) {
      event.preventDefault();

      if (!currentTaskId) {
        console.error("Task ID is not available");
        return;
      }

      const workerProgress = parseInt(workerProgressInput.value, 10);
      const percentFromProject = percentFromInput.value.trim();
      const remarks = document.getElementById("remarks").value || null;

      if (isNaN(workerProgress) || workerProgress < 0 || workerProgress > 100) {
        Swal.fire({
          icon: "error",
          title: "Invalid Progress",
          html: `<p style="font-size: 16px; color: #555;">Progress must be a number between 0 and 100.</p>`,
          showConfirmButton: true,
        });
        return;
      }

      try {
        const response = await fetch(
          `/foreman_progress/update-progress/${currentTaskId}/`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": document.querySelector(
                "[name=csrfmiddlewaretoken]"
              ).value,
            },
            body: JSON.stringify({
              worker_progress: workerProgress,
              percentage_from_project: percentFromProject,
              remarks: remarks,
            }),
          }
        );

        if (response.ok) {
          const data = await response.json();

          Swal.fire({
            position: "top-end",
            icon: "success",
            title:
              '<h2 style="font-size: 24px; margin: 0;">Progress Updated Successfully</h2>',
            html: `<p style="font-size: 16px; color: #555; margin-top: 8px;">The progress has been successfully updated.</p>`,
            showConfirmButton: false,
            timer: 1500,
          });
          setTimeout(function () {
            location.reload();
          }, 1500);
        } else {
          console.error("Error updating progress");
          Swal.fire({
            icon: "error",
            title: "Error Updating Progress",
            html: `<p style="font-size: 16px; color: #555;">There was an error updating the progress. Please try again.</p>`,
            showConfirmButton: true,
          });
        }
      } catch (error) {
        console.error("Error:", error);
        Swal.fire({
          icon: "error",
          title: "Error",
          html: `<p style="font-size: 16px; color: #555;">There was an error updating the progress. Please try again.</p>`,
          showConfirmButton: true,
        });
      }
    });
  ///////////////////////////////////////////////////////////////////////////////////////////////////////////////// MODAL SAVE CHANGES  SUBMIT

  ///////////////////////////////////////////////////////////////////////////////////////////////////////////////// TASK FILTER
  $(document).ready(function () {
    $("#projects").on("change", function () {
      var projectId = $(this).val();

      $.ajax({
        url: "/foreman_progress/filter-task/",
        data: { project_id: projectId },
        success: function (data) {
          $("#task-table-body").html(data.html);
        },
      });
    });
  });

  projectSelect.addEventListener("change", async () => {
    const projectId = projectSelect.value;

    try {
      const response = await fetch(
        `/foreman_progress/filter-task/?project_id=${projectId}`
      );
      const data = await response.json();

      if (
        data.progress !== null &&
        data.progress >= 0 &&
        data.progress <= 100
      ) {
        progressBar.classList.remove("hidden");
        progressFill.style.width = `${data.progress}%`;
        progressPercentage.textContent = `${data.progress}%`;
      } else {
        progressBar.classList.add("hidden");
      }
    } catch (error) {
      console.error("Error:", error);
    }
  });
  ///////////////////////////////////////////////////////////////////////////////////////////////////////////////// TASK FILTER

  ///////////////////////////////////////////////////////////////////////////////////////////////////////////////// MODAL SAVE SUBMIT
  saveButton.addEventListener("click", async function (event) {
    event.preventDefault(); // Prevent default form submission

    const workerProgress = workerProgressInput.value.trim();
    const percentFromProject = percentFromInput.value.trim();
    const remarks = remarksTextarea.value.trim();

    if (!workerProgress || !percentFromProject) {
      Swal.fire({
        icon: "warning",
        title: "Missing Fields",
        html: `<p style="font-size: 16px; color: #555;">Please fill in all required fields before submitting.</p>`,
        showConfirmButton: true,
      });
      return;
    }

    try {
      const response = await fetch(
        `/foreman_progress/update-progress-after-completed/${currentTaskId}/`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]")
              .value, // CSRF token for Django
          },
          body: JSON.stringify({
            worker_progress: workerProgress,
            percentage_from_project: percentFromProject,
            remarks: remarks,
          }),
        }
      );

      if (response.ok) {
        const data = await response.json();

        Swal.fire({
          position: "top-end",
          icon: "success",
          title:
            '<h2 style="font-size: 24px; margin: 0;">Progress Updated Successfully</h2>',
          html: `<p style="font-size: 16px; color: #555; margin-top: 8px;">The progress has been successfully updated.</p>`,
          showConfirmButton: false,
          timer: 1500,
        });
        setTimeout(function () {
          location.reload();
        }, 1500);
      } else {
        console.error("Error updating progress");
        Swal.fire({
          icon: "error",
          title: "Error Updating Progress",
          html: `<p style="font-size: 16px; color: #555;">There was an error updating the progress. Please try again.</p>`,
          showConfirmButton: true,
        });
      }
    } catch (error) {
      console.error("Error:", error);
      Swal.fire({
        icon: "error",
        title: "Error",
        html: `<p style="font-size: 16px; color: #555;">There was an error updating the progress. Please try again.</p>`,
        showConfirmButton: true,
      });
    }
  });
  ///////////////////////////////////////////////////////////////////////////////////////////////////////////////// MODAL SAVE SUBMIT
});
