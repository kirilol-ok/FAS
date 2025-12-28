$(document).ready(function() {
    const API_BASE_URL = "http://localhost:8000/admin";

    const authToken = localStorage.getItem('authToken');
    if (!authToken) {
        window.location.href = 'index.html';
        return;
    }

    const adminName = localStorage.getItem('adminName');
    if (adminName) $('#adminName').text(adminName);

    const urlParams = new URLSearchParams(window.location.search);
    const employeeId = urlParams.get('id');

    if (!employeeId) {
        alert("Error: No employee ID.");
        window.location.href = "dashboard.html";
        return;
    }

    loadEmployeeData(employeeId);

    $('#dismissCheckbox').on('change', function() {
        if ($(this).is(':checked')) {
            $('#dismissDateGroup').slideDown();
            if (!$('#dismissDate').val()) {
                const today = new Date().toISOString().split('T')[0];
                $('#dismissDate').val(today);
            }
        } else {
            $('#dismissDateGroup').slideUp();
            $('#dismissDate').val('');
        }
    });

    $("#backBtn, #cancelBtn").on("click", function() {
        window.location.href = "dashboard.html";
    });

    $("#logoutBtn").on("click", function() {
        localStorage.clear();
        window.location.href = "index.html";
    });

    $("#editEmployeeForm").on("submit", function(e) {
        e.preventDefault();

        let finalDate = null;
        let isDismissed = $('#dismissCheckbox').is(':checked');

        if (isDismissed) {
            finalDate = $('#dismissDate').val();
            if (!finalDate) {
                finalDate = new Date().toISOString().split('T')[0];
            }
        }

        const updateData = {
            first_name: $("#firstName").val(),
            last_name: $("#lastName").val(),
            email: $("#email").val(),
            dismissed: isDismissed,
            dismissal_date: finalDate 
        };

        $.ajax({
            url: `${API_BASE_URL}/update_employees/${employeeId}`,
            method: "PATCH",
            contentType: "application/json",
            data: JSON.stringify(updateData),
            success: function(response) {
                alert("Changes saved!");
                window.location.href = "dashboard.html";
            },
            error: function(xhr) {
                console.error("Writing error:", xhr);
                let msg = "An error has occurred.";
                
                if (xhr.responseJSON && xhr.responseJSON.detail) {
                    if (Array.isArray(xhr.responseJSON.detail)) {
                        msg += "\n" + xhr.responseJSON.detail.map(e => e.msg).join(", ");
                    } else {
                        msg += "\n" + xhr.responseJSON.detail;
                    }
                }
                alert(msg);
            }
        });
    });

    $("#deleteBtn").on("click", function() {
        if (confirm("Are you sure you want to remove the employee?")) {
            $.ajax({
                url: `${API_BASE_URL}/delete_employees/${employeeId}`,
                method: "DELETE",
                success: function() {
                    alert("The employee has been removed.");
                    window.location.href = "dashboard.html";
                },
                error: function(xhr) {
                    alert("Deletion error.");
                    console.error(xhr);
                }
            });
        }
    });

    function loadEmployeeData(id) {
        $.ajax({
            url: `${API_BASE_URL}/employees/${id}`,
            method: "GET",
            success: function(employee) {
                $('#employeeId').val(employee.id);
                $('#firstName').val(employee.first_name);
                $('#lastName').val(employee.last_name);
                $('#email').val(employee.email);

                if (employee.dismissed) {
                    $('#dismissCheckbox').prop('checked', true);
                    $('#dismissDateGroup').show();
                    
                    if (employee.dismissal_date) {
                        $('#dismissDate').val(employee.dismissal_date.split('T')[0]);
                    }
                }
            },
            error: function(xhr) {
                alert("No employee found.");
                window.location.href = "dashboard.html";
            }
        });
    }
});