/*
$(document).ready(function() {
    // FILTER FUNCTION
    $('#projects').on('change', function() {
        const projectId = $(this).val();
        
        $.ajax({
            url: "/foreman_attendance/filter-attendance/",
            data: { 'project_id': projectId },
            success: function(data) {
                $('#workers-body').html(data.html);
            }
        });
    });

    const searchInput = document.getElementById('search');
    searchInput.addEventListener('input', (event) => {
        const query = event.target.value.toLowerCase();
        const rows = document.querySelectorAll('#workers-body .table_row');
        let found = false;

        rows.forEach(row => {
            const workerName = row.querySelector('.worker_profile h4').innerText.toLowerCase();
            if (workerName.includes(query)) {
                row.style.display = '';
                found = true;
            } else {
                row.style.display = 'none';
            }
        });

        // If no results, display "No workers found"
        const emptyRow = document.querySelector('.empty');
        if (!found && query) {
            if (!emptyRow) {
                const newRow = document.createElement('tr');
                newRow.classList.add('empty');
                newRow.innerHTML = '<td colspan="4">No workers found.</td>';
                document.querySelector('#workers-body').appendChild(newRow);
            }
        } else if (emptyRow && !query) {
            emptyRow.remove();
        }
    });
});
*/

document.addEventListener("DOMContentLoaded", () => {
  const viewButtons = document.querySelectorAll(".view_btn");
  viewButtons.forEach((button) => {
    button.addEventListener("click", (e) => {
      const workerId = e.target.getAttribute("data-worker-id");
      fetchAttendanceData(workerId);
    });
  });

  const closeModal = document.querySelector(".closeModal");
  closeModal.addEventListener("click", () => {
    document.getElementById("workerModal").style.display = "none";
  });
});

// Function to fetch attendance data
function fetchAttendanceData(workerId) {
  fetch(`/foreman_attendance/get-attendance-data/${workerId}/`)
    .then((response) => response.json())
    .then((data) => {
      const workerName = data.workerName;
      console.log(workerName);
      document.getElementById(
        "workerName"
      ).innerText = `${workerName}'s Attendances`;

      const attendanceTable = document.getElementById("attendanceData");
      attendanceTable.innerHTML = "";

      data.attendances.forEach((attendance) => {
        const row = document.createElement("tr");
        row.innerHTML = `
                    <td>${attendance.time_in}</td>
                    <td class="${attendance.timeIn_status_class}">${attendance.timeIn_status}</td>
                    <td>${attendance.time_out}</td>
                    <td>${attendance.period}</td>
                    <td>${attendance.recorded_at}</td>
                `;
        attendanceTable.appendChild(row);
      });

      document.getElementById("workerModal").style.display = "flex";
    })
    .catch((error) => console.error("Error fetching attendance data:", error));
}
