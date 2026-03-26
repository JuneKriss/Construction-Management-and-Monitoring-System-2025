//SEARCH FUNCTIKON
$(document).ready(function() {
    $("#search").on('keyup', function() {
        let query = $(this).val();

        $.ajax({
            url: '/admin_accounts/search_accounts/', 
            method: 'GET',
            data: { 'query': query },
            success: function(response) {
                $("#accounts-body").empty();

                response.accounts.forEach(function(account) {
                    let row = `
                        <tr>
                            <td><img src="${account.profile_image}" class="profile"></td>
                            <td><p>${account.username}</p></td>
                            <td><p class="password">${account.password}</p></td>
                            <td><p>${account.role}</p></td>
                            <td>
                                <a href="accountDetails_page/${account.account_id}" class="details btn">View Details</a>
                                <a href="#" class="deactivate btn">Deactivate</a>
                            </td>
                        </tr>
                    `;
                    $("#accounts-body").append(row);
                });
                if (response.accounts.length == 0) {
                    $("#accounts-body").append('<tr><td colspan="5" class="no_results">No results found</td></tr>');
                }
            }
        });
    });
});

//FILTER FUNCTION
$(document).ready(function() {
    $("#filterbtn").on('click', function(e) {
        e.preventDefault(); 

        let selectedRole = $("#roles").val();  

        $.ajax({
            url: '/admin_accounts/filter_accounts/',
            method: 'GET',
            data: { 'role': selectedRole },
            success: function(response) {
                $("#accounts-body").empty();

                response.accounts.forEach(function(account) {
                    let row = `
                        <tr>
                            <td><img src="${account.profile_image}" class="profile"></td>
                            <td><p>${account.username}</p></td>
                            <td><p class="password">${account.password}</p></td>
                            <td><p>${account.role}</p></td>
                            <td>
                                <a href="accountDetails_page/${account.account_id}" class="details btn">View Details</a>
                                <a href="#" class="deactivate btn">Deactivate</a>
                            </td>
                        </tr>
                    `;
                    $("#accounts-body").append(row);
                });
                if (response.accounts.length == 0) {
                    $("#accounts-body").append('<tr><td colspan="5">No results found</td></tr>');
                }
            }
        });
    });
});

// DEACTIVATE ALERTS
document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.deactivate').forEach(button => {
        button.addEventListener('click', function (event) {
            event.preventDefault();
            const url = this.getAttribute('href');
            Swal.fire({
                title: 'Are you sure?',
                text: "This will deactivate the account.",
                icon: 'warning',
                showCancelButton: true,
                confirmButtonText: 'Yes, deactivate it!',
            }).then(result => {
                if (result.isConfirmed) {
                    window.location.href = url;
                }
            });
        });
    });
});

// DJANGO MESSAGE ALERTS
if (typeof djangoMessages !== 'undefined' && djangoMessages.length > 0) {
    djangoMessages.forEach(message => {
        if (message.level === 'success') {
            Swal.fire({
                icon: 'success',
                title: 'Success',
                text: message.text,
                timer: 3000,
                showConfirmButton: false
            });
        } else if (message.level === 'error') {
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: message.text,
                timer: 3000,
                showConfirmButton: false
            });
        }
    });
}
