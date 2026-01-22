$(document).ready(function() {
    console.log("✅ add.js v9 - Auto date correction");
    const API_BASE_URL = "http://localhost:8000/admin";

    // --- DATE HELPERS ---
    function getTodayString() { return new Date().toISOString().split('T')[0]; }
    function getFutureString(months = 6) {
        const d = new Date();
        d.setMonth(d.getMonth() + months);
        return d.toISOString().split('T')[0];
    }

    // INIT: Default values
    $("#hireDate").val(getTodayString());
    $("#expirationDate").val(getFutureString(6));
    $("#expirationDate").attr("min", getTodayString());

    // --- AUTO-CORRECTION AND CONSTRAINTS ---
    $("#hireDate").on("change", function() {
        const hireVal = $(this).val();

        if (hireVal) {
            $("#expirationDate").attr("min", hireVal);

            const expireVal = $("#expirationDate").val();
            if (expireVal && expireVal < hireVal) {
                console.log("⚠️ The expiration date was earlier than the hire date — automatic correction.");
                $("#expirationDate").val(hireVal);
            }
        }
    });

    // --- BUTTONS ---
    $("#backBtn, #cancelBtn").on("click", function(e) {
        e.preventDefault();
        window.location.href = "dashboard.html";
    });

    // --- ADD ACTION ---
    $("#addBtn").on("click", async function(e) {
        e.preventDefault();

        if (!$("#hireDate").val()) $("#hireDate").val(getTodayString());

        const hireVal = $("#hireDate").val();
        const expireVal = $("#expirationDate").val();

        // HARD VALIDATION
        if (hireVal && expireVal && expireVal < hireVal) {
            alert(
                "⛔ DATE ERROR: The account expiration date (" + expireVal + ")\n" +
                "cannot be earlier than the hire date (" + hireVal + ")!"
            );
            $("#expirationDate").val(hireVal).focus();
            return;
        }

        const form = document.getElementById("addEmployeeForm");
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }

        const $btn = $(this);
        $btn.prop("disabled", true).text("Sending...");

        const employeeData = {
            first_name: $("#firstName").val(),
            last_name: $("#lastName").val(),
            email: $("#email").val(),
            hire_date: hireVal,
            expiration_date: expireVal || null
        };

        try {
            // ✅ FIX: template string
            const createResponse = await $.ajax({
                url: `${API_BASE_URL}/create_employee`,
                method: "POST",
                contentType: "application/json",
                data: JSON.stringify(employeeData)
            });

            console.log("✅ Created:", createResponse.id);
            let message = "Employee added successfully.";

            const fileInput = document.getElementById("employeePhoto");
            if (fileInput && fileInput.files.length > 0) {
                const formData = new FormData();
                formData.append("file", fileInput.files[0]);
                try {
                    // ✅ FIX: template string
                    await $.ajax({
                        url: `${API_BASE_URL}/employees/${createResponse.id}/upload_photo`,
                        method: "POST",
                        processData: false,
                        contentType: false,
                        data: formData
                    });
                    message += "\nPhoto uploaded.";
                } catch (err) {
                    console.error(err);
                    message += "\n(Photo upload error)";
                }
            }

            alert(message);
            window.location.href = "dashboard.html";

        } catch (error) {
            console.error("Error:", error);
            $btn.prop("disabled", false).text("Add Employee");
            let msg = error.responseJSON?.detail || "Server error";
            alert("Error: " + msg);
        }
    });
});
