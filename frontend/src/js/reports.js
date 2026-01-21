$(document).ready(function() {
    const API_BASE_URL = "http://localhost:8000/admin";
    const authToken = localStorage.getItem('authToken');
    
    let currentReportData = [];
    
    if (!authToken) { 
        window.location.href = 'index.html'; 
        return; 
    }
    
    const today = new Date();
    const pastDate = new Date();
    pastDate.setDate(today.getDate() - 7);
    $('#dateFrom').val(formatDateTimeLocal(pastDate));
    $('#dateTo').val(formatDateTimeLocal(today));
    
    loadEmployeesList();
    setupMultiSelectBehavior();

    $('#reportFiltersForm').on('submit', function(e) {
        e.preventDefault();
        generateReport();
    });

    $('#exportCsvBtn').on('click', function() {
        exportToCSV();
    });

    function setupMultiSelectBehavior() {
        // Handle "All employees" selection
        $('#employeeSelect').on('change', function() {
            const selected = $(this).val() || [];
            
            if (selected.includes('')) {
                // If "All employees" is clicked, select only "All"
                $(this).val(['']);
            } else if (selected.length === 0) {
                // If nothing selected, default to "All"
                $(this).val(['']);
            }
        });

        // Handle "All statuses" selection
        $('#statusSelect').on('change', function() {
            const selected = $(this).val() || [];
            
            if (selected.includes('')) {
                // If "All statuses" is clicked, select only "All"
                $(this).val(['']);
            } else if (selected.length === 0) {
                // If nothing selected, default to "All"
                $(this).val(['']);
            }
        });
    }

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
                // Select "All employees" by default
                $select.val(['']);
            }
        });
    }

    function generateReport() {
        const employeeIds = $('#employeeSelect').val() || [];
        const statuses = $('#statusSelect').val() || [];
        
        const dateFromVal = $('#dateFrom').val().split('T')[0];
        const dateToVal = $('#dateTo').val().split('T')[0];

        // Prepare employee_ids array (null if "All employees" selected)
        let employeeIdsToSend = null;
        if (employeeIds.length > 0 && !employeeIds.includes('')) {
            employeeIdsToSend = employeeIds.map(id => parseInt(id));
        }

        // Prepare statuses array (null if "All statuses" selected)
        let statusesToSend = null;
        if (statuses.length > 0 && !statuses.includes('')) {
            statusesToSend = statuses;
        }

        const reportData = {
            employee_ids: employeeIdsToSend,
            statuses: statusesToSend,
            date_from: dateFromVal,
            date_to: dateToVal
        };

        console.log('Sending report data:', reportData); // Debug

        $('#reportsTableContainer').html('<p class="loading">Loading...</p>');
        $('#exportCsvBtn').prop('disabled', true);

        $.ajax({
            url: `${API_BASE_URL}/reports/display_raports`,
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(reportData),
            success: function(reports) {
                console.log('Received reports:', reports); // Debug
                currentReportData = reports;
                displayReports(reports);
                
                if (reports && reports.length > 0) {
                    $('#exportCsvBtn').prop('disabled', false);
                }
            },
            error: function(xhr) {
                console.error("Report error:", xhr);
                $('#reportsTableContainer').html('<p class="loading" style="color:red">Error loading reports.</p>');
                currentReportData = [];
                $('#exportCsvBtn').prop('disabled', true);
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
            $('#reportsTableContainer').html('<p class="loading">No results found.</p>');
            return;
        }

        let tableHTML = `<table class="workers-table">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Employee</th>
                    <th>Status</th>
                    <th>Date</th>
                    <th>Description</th>
                </tr>
            </thead>
            <tbody>`;
        
        reports.forEach(r => {
            const status = r.status || "Unknown";
            const statusClass = status === "OK" ? "status-active" : (status === "Error" ? "status-inactive" : "");
            const desc = r.denial_reason || r.description || "-";
            
            tableHTML += `<tr>
                <td>${r.id}</td>
                <td>${r.employee_id}</td>
                <td><span class="status-badge ${statusClass}">${status}</span></td>
                <td>${new Date(r.created_at).toLocaleString()}</td>
                <td>${desc}</td>
            </tr>`;
        });
        
        tableHTML += `</tbody></table>`;
        $('#reportsTableContainer').html(tableHTML);
    }

    function exportToCSV() {
        if (!currentReportData || currentReportData.length === 0) {
            alert('No data to export');
            return;
        }

        const headers = ['ID', 'Employee ID', 'Status', 'Date', 'Description'];
        
        const rows = currentReportData.map(r => {
            const status = r.status || 'Unknown';
            const desc = (r.denial_reason || r.description || '-').replace(/"/g, '""');
            const date = new Date(r.created_at).toLocaleString();
            
            return [
                r.id,
                r.employee_id,
                status,
                date,
                `"${desc}"`
            ];
        });

        const csvContent = [
            headers.join(','),
            ...rows.map(row => row.join(','))
        ].join('\n');

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        
        const dateFrom = $('#dateFrom').val().split('T')[0];
        const dateTo = $('#dateTo').val().split('T')[0];
        const statuses = $('#statusSelect').val() || [];
        const statusSuffix = (statuses.length > 0 && !statuses.includes('')) ? `_${statuses.join('-')}` : '';
        const filename = `reports_${dateFrom}_to_${dateTo}${statusSuffix}.csv`;
        
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    $("#backBtn").on("click", function () {
        window.location.href = "dashboard.html";
    });

    $("#logoutBtn").on("click", function () {
        localStorage.removeItem("authToken");
        localStorage.removeItem("adminEmail");
        localStorage.removeItem("adminName");
        window.location.href = "index.html";
    });
});