$(document).ready(function() {
    console.log("✅ edit.js v10 - Delete button fixed");
    const API_BASE_URL = "http://localhost:8000/admin";

    // --- HELPERS ---
    function safeDate(value) {
        if (!value) return "";
        const strVal = String(value);
        return strVal.includes("T") ? strVal.split("T")[0] : strVal;
    }

    // Update min constraints and auto-correct invalid dates
    function updateDateConstraintsAndCorrect() {
        const hireVal = $("#hireDate").val();

        if (hireVal) {
            // 1) Set MIN constraints
            $("#dismissDate").attr("min", hireVal);
            $("#expirationDate").attr("min", hireVal);

            // 2) Auto-correct dismissal date if earlier than hire date
            const dismissVal = $("#dismissDate").val();
            if (dismissVal && dismissVal < hireVal) {
                console.log("⚠️ Dismissal date was earlier than hire date — auto-correcting.");
                $("#dismissDate").val(hireVal);
            }

            // 3) Auto-correct expiration date if earlier than hire date
            const expireVal = $("#expirationDate").val();
            if (expireVal && expireVal < hireVal) {
                console.log("⚠️ Expiration date was earlier than hire date — auto-correcting.");
                $("#expirationDate").val(hireVal);
            }
        }
    }

    // --- INIT ---
    const authToken = localStorage.getItem("authToken");
    if (!authToken) { window.location.href = "index.html"; return; }

    const adminName = localStorage.getItem("adminName");
    if (adminName) $("#adminName").text(adminName);

    const urlParams = new URLSearchParams(window.location.search);
    const employeeId = urlParams.get("id");

    if (!employeeId) {
        alert("Missing employee ID.");
        window.location.href = "dashboard.html";
        return;
    }

    // Load employee data
    loadEmployeeData(employeeId);

    // --- UI EVENTS ---

    // Key moment: hire date change triggers corrections
    $("#hireDate").on("change", function() {
        updateDateConstraintsAndCorrect();
    });

    $("#dismissCheckbox").on("change", function() {
        if ($(this).is(":checked")) {
            $("#dismissDateGroup").slideDown();

            // If empty, set a default date
            if (!$("#dismissDate").val()) {
                const today = new Date().toISOString().split("T")[0];
                const hireVal = $("#hireDate").val();

                // If "today" is earlier than hire date, use hire date
                if (hireVal && today < hireVal) {
                    $("#dismissDate").val(hireVal);
                } else {
                    $("#dismissDate").val(today);
                }
            }
        } else {
            $("#dismissDateGroup").slideUp();
            $("#dismissDate").val("");
        }
    });

    // DELETE EMPLOYEE
    $("#deleteBtn").on("click", async function() {
        if (!confirm("Are you sure you want to permanently delete this employee? This action cannot be undone.")) {
            return;
        }

        try {
            await $.ajax({
                url: `${API_BASE_URL}/delete_employees/${employeeId}`,
                method: "DELETE"
            });

            alert("Employee deleted successfully!");
            window.location.href = "dashboard.html";

        } catch (xhr) {
            console.error("Delete error:", xhr);
            
            let msg = xhr.responseJSON && xhr.responseJSON.detail
                ? xhr.responseJSON.detail
                : "An error occurred while deleting the employee.";
            
            alert(msg);
        }
    });

    $("#backBtn, #cancelBtn").on("click", function() {
        window.location.href = "dashboard.html";
    });

    $("#logoutBtn").on("click", function() {
        localStorage.clear();
        window.location.href = "index.html";
    });

    // --- SAVE ---
    $("#editEmployeeForm").on("submit", async function(e) {
        e.preventDefault();

        const hireDateVal = $("#hireDate").val();
        const expirationDateVal = $("#expirationDate").val();

        // Dismissal logic
        const isDismissed = $("#dismissCheckbox").is(":checked");
        let finalDismissalDate = null;

        if (isDismissed) {
            finalDismissalDate = $("#dismissDate").val();
            if (!finalDismissalDate) finalDismissalDate = new Date().toISOString().split("T")[0];
        }

        // FINAL VALIDATION (in case auto-correction didn't run)
        if (hireDateVal) {
            if (isDismissed && finalDismissalDate && finalDismissalDate < hireDateVal) {
                alert("⛔ ERROR: Dismissal date cannot be earlier than hire date!");
                $("#dismissDate").val(hireDateVal);
                return;
            }
            if (expirationDateVal && expirationDateVal < hireDateVal) {
                alert("⛔ ERROR: Expiration date cannot be earlier than hire date!");
                $("#expirationDate").val(hireDateVal);
                return;
            }
        }

        const updateData = {
            first_name: $("#firstName").val(),
            last_name: $("#lastName").val(),
            email: $("#email").val(),
            dismissed: isDismissed,
            dismissal_date: finalDismissalDate,
            hire_date: hireDateVal ? hireDateVal : null,
            expiration_date: expirationDateVal ? expirationDateVal : null
        };

        try {
            await $.ajax({
                url: `${API_BASE_URL}/update_employees/${employeeId}`,
                method: "PATCH",
                contentType: "application/json",
                data: JSON.stringify(updateData)
            });

            const fileInput = document.getElementById("employeePhoto");
            if (fileInput && fileInput.files.length > 0) {
                const formData = new FormData();
                formData.append("file", fileInput.files[0]);
                await $.ajax({
                    url: `${API_BASE_URL}/employees/${employeeId}/upload_photo`,
                    method: "POST",
                    processData: false,
                    contentType: false,
                    data: formData
                });
            }

            alert("Changes saved!");
            window.location.href = "dashboard.html";

        } catch (xhr) {
            console.error("Save error:", xhr);

            let msg =
                xhr.responseJSON && xhr.responseJSON.detail
                    ? xhr.responseJSON.detail
                    : "An error occurred.";

            // If FastAPI validation errors come as array -> join messages
            alert(Array.isArray(msg) ? msg.map(e => e.msg).join("\n") : msg);
        }
    });

    function loadEmployeeData(id) {
        $.ajax({
            url: `${API_BASE_URL}/employees/${id}`,
            method: "GET",
            success: function(employee) {
                $("#employeeId").val(employee.id);
                $("#firstName").val(employee.first_name);
                $("#lastName").val(employee.last_name);
                $("#email").val(employee.email);
                $("#hireDate").val(safeDate(employee.hire_date));
                $("#expirationDate").val(safeDate(employee.expiration_date));

                if (employee.dismissed) {
                    $("#dismissCheckbox").prop("checked", true);
                    $("#dismissDateGroup").show();
                    $("#dismissDate").val(safeDate(employee.dismissal_date));
                }

                // Apply constraints after load
                updateDateConstraintsAndCorrect();
            },
            error: function() {
                alert("Employee not found.");
                window.location.href = "dashboard.html";
            }
        });
    }
});