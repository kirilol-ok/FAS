$(document).ready(function() {
    const API_BASE_URL = "http://localhost:8000/admin";

    $("#backBtn, #cancelBtn").on("click", function() {
        window.location.href = "dashboard.html";
    });

    $("#addEmployeeForm").on("submit", function(e) {
        e.preventDefault();

        const employeeData = {
            first_name: $("#firstName").val(),
            last_name: $("#lastName").val(),
            email: $("#email").val()
        };

        $.ajax({
            url: `${API_BASE_URL}/create_employee`, 
            method: "POST",
            contentType: "application/json",
            data: JSON.stringify(employeeData),
            success: function(response) {
                alert(`Employee added: ${response.first_name} ${response.last_name}`);
                window.location.href = "dashboard.html";
            },
            error: function(xhr) {
                console.error("Addition error: ", xhr);
                let msg = "Error adding employee.";
                if (xhr.responseJSON && xhr.responseJSON.detail) {
                    msg += "\nDetails: " + xhr.responseJSON.detail;
                }
                alert(msg);
            }
        });
    });
});