document.addEventListener("DOMContentLoaded", function () {
    const searchInput = document.getElementById("search");
    const projectsTableBody = document.querySelector("#projects-body");

    searchInput.addEventListener("keyup", function () {
        const query = searchInput.value.trim();

        fetch(`/project-manager-projects/search-project?query=${encodeURIComponent(query)}`, {
            headers: {
                "X-Requested-With": "XMLHttpRequest",
            },
        })
            .then((response) => response.json())
            .then((data) => {
                projectsTableBody.innerHTML = "";

                if (data.projects && data.projects.length > 0) {
                    data.projects.forEach((project) => {
                        const row = document.createElement("tr");

                        row.innerHTML = `
                            <td>${project.name}</td>
                            <td>${project.client}</td>
                            <td>
                                <div class="progress">
                                    <div class="progress-fill" style="width: ${project.progress}%;">
                                        <span class="progress-percentage">${project.progress}%</span>
                                    </div>
                                </div>
                            </td>
                            <td>${project.status}</td>
                            <td>
                                <span class="material-symbols-outlined">edit</span>
                            </td>
                        `;

                        projectsTableBody.appendChild(row);
                    });
                } else {
                    const row = document.createElement("tr");
                    row.innerHTML = `<td colspan="5" style="text-align: center;">No project found.</td>`;
                    projectsTableBody.appendChild(row);
                }
            })
            .catch((error) => {
                console.error("Error fetching project data:", error);
            });
    });
});