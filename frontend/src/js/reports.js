$(document).ready(function() {
    const API_BASE_URL = "http://localhost:8000/admin";
    const authToken = localStorage.getItem('authToken');
    
    
    if (!authToken) { window.location.href = 'index.html'; return; }
    
    const today = new Date();
    const pastDate = new Date();
    pastDate.setDate(today.getDate() - 7);
    $('#dateFrom').val(formatDateTimeLocal(pastDate));
    $('#dateTo').val(formatDateTimeLocal(today));
    
    loadEmployeesList();

    $('#reportFiltersForm').on('submit', function(e) {
        e.preventDefault();
        generateReport();
    });


    function loadEmployeesList() {
        $.ajax({
            url: `${API_BASE_URL}/all_employees`,
            method: 'GET',
            success: function(employees) {
                const $select = $('#employeeSelect');
                $select.empty();
                $select.append('<option value="">All employees</option>');
                employees.forEach(function(emp) {
                    $select.append(`<option value="${emp.id}">${emp.first_name} ${emp.last_name}</option>`);
                });
            }
        });
    }

    function generateReport() {
        const employeeId = $('#employeeSelect').val();
        
        const dateFromVal = $('#dateFrom').val().split('T')[0];
        const dateToVal = $('#dateTo').val().split('T')[0];

        const reportData = {
            employee_id: employeeId ? parseInt(employeeId) : null,
            date_from: dateFromVal,
            date_to: dateToVal
        };

        $('#reportsTableContainer').html('<p class="loading">Loading...</p>');

        $.ajax({
            url: `${API_BASE_URL}/reports/display_raports`,
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(reportData),
            success: function(reports) {
                displayReports(reports);
            },
            error: function(xhr) {
                console.error("Report error:", xhr);
                $('#reportsTableContainer').html('<p class="loading" style="color:red">Error.</p>');
            }
        });
    }

    function formatDateTimeLocal(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        return `${year}-${month}-${day}T${hours}:${minutes}`;
    }
    
    function displayReports(reports) {
         if (!reports || reports.length === 0) {
            $('#reportsTableContainer').html('<p class="loading">Brak wyników.</p>');
            return;
        }

        let tableHTML = `<table class="workers-table"><thead><tr><th>ID</th><th>Employee</th><th>Status</th><th>Date</th><th>Description</th></tr></thead><tbody>`;
        reports.forEach(r => {
             const status = r.status || "Unknown";
             const desc = r.denial_reason || r.description || "-";
             tableHTML += `<tr><td>${r.id}</td><td>${r.employee_id}</td><td>${status}</td><td>${new Date(r.created_at).toLocaleString()}</td><td>${desc}</td></tr>`;
        });
        tableHTML += `</tbody></table>`;
        $('#reportsTableContainer').html(tableHTML);
    }

    $("#backBtn").on("click", function () {
        window.location.href = "dashboard.html";
    });
});