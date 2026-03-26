// SEARCH FUNCTION
$(document).ready(function() {
    $("#projectSearch").on('keyup', function() {
        let query = $(this).val().trim();

        $.ajax({
            url: '/admin-projects/search-projects/',
            method: 'GET',
            data: { 'query': query },
            success: function(response) {
                $("#project-body").empty();

                response.projects.forEach(function(project) {
                    let row = `
                        <tr>
                            <td>${project.project_name}</td>
                            <td>${project.client}</td>
                            <td>${project.start_date}</td>
                            <td>${project.due_date}</td>
                            <td>
                                ${project.project_percent == 0 ? '<p class="not_started">Not Started</p>' : ''}
                                ${project.project_percent > 0 && project.project_percent <= 25 ? '<p class="initial">Initial Phase</p>' : ''}
                                ${project.project_percent > 25 && project.project_percent <= 50 ? '<p class="in_progress">In Progress</p>' : ''}
                                ${project.project_percent > 50 && project.project_percent <= 75 ? '<p class="midway">Midway</p>' : ''}
                                ${project.project_percent > 75 && project.project_percent < 100 ? '<p class="near_complete">Near Completion</p>' : ''}
                                ${project.project_percent == 100 ? '<p class="completed">Completed</p>' : ''}
                            </td>
                            <td><a href="#" class="btn">View</a></td>
                        </tr>
                    `;
                    $("#project-body").append(row);
                });

                if (response.projects.length === 0 && query !== "") {
                    $("#project-body").append('<tr><td colspan="6" class="no_results">No results found</td></tr>');
                }
            },
            error: function(xhr, status, error) {
                console.error("Error fetching projects:", xhr.responseText);
                console.error("Status:", status);
                console.error("Error:", error);
            }
        });
    });
});

