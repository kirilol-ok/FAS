// reports.js - Logika strony raportów

$(document).ready(function() {
    // Sprawdź autoryzację
    const authToken = localStorage.getItem('authToken');
    if (!authToken) {
        window.location.href = 'index.html';
        return;
    }

    // Wyświetl nazwę admina
    const adminName = localStorage.getItem('adminName');
    if (adminName) {
        $('#adminName').text(adminName);
    }

    // Ustaw domyślne daty (ostatnie 6 miesięcy zgodnie z diagramem)
    const today = new Date();
    const sixMonthsAgo = new Date();
    sixMonthsAgo.setMonth(today.getMonth() - 6);

    $('#dateFrom').val(formatDateTimeLocal(sixMonthsAgo));
    $('#dateTo').val(formatDateTimeLocal(today));

    // Załaduj listę pracowników do selecta
    loadEmployeesList();

    // Przycisk "Generuj Raport"
    $('#generateReportBtn').on('click', function() {
        generateReport();
    });

    // Przycisk "Zamknij Raport"
    $('#closeReportBtn').on('click', function() {
        window.location.href = 'dashboard.html';
    });

    // Przycisk "Powrót"
    $('#backBtn').on('click', function() {
        window.location.href = 'dashboard.html';
    });

    // Przycisk "Wyloguj"
    $('#logoutBtn').on('click', function() {
        localStorage.clear();
        window.location.href = 'index.html';
    });
});

// Formatuj datę do datetime-local input
function formatDateTimeLocal(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day}T${hours}:${minutes}`;
}

// Załaduj listę pracowników
function loadEmployeesList() {
    $.ajax({
        url: `${API_BASE_URL}/employees`,
        method: 'GET',
        success: function(employees) {
            const $select = $('#employeeSelect');
            $select.empty();
            $select.append('<option value="">Wszyscy pracownicy</option>');
            
            employees.forEach(function(employee) {
                $select.append(
                    `<option value="${employee.id}">${employee.first_name} ${employee.last_name} (ID: ${employee.id})</option>`
                );
            });
        },
        error: function(xhr) {
            console.error('Błąd wczytywania listy pracowników:', xhr);
        }
    });
}

// Generuj raport
function generateReport() {
    const employeeId = $('#employeeSelect').val();
    const dateFrom = $('#dateFrom').val();
    const dateTo = $('#dateTo').val();

    if (!dateFrom || !dateTo) {
        alert('Proszę wypełnić daty "od" i "do"');
        return;
    }

    const reportData = {
        employee_id: employeeId ? parseInt(employeeId) : null,
        date_from: new Date(dateFrom).toISOString(),
        date_to: new Date(dateTo).toISOString()
    };

    // Wyświetl loading
    $('#reportsTableContainer').html('<p class="loading">Generowanie raportu...</p>');

    $.ajax({
        url: `${API_BASE_URL}/reports/generate`,
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(reportData),
        success: function(reports) {
            displayReports(reports);
        },
        error: function(xhr) {
            $('#reportsTableContainer').html('<p class="loading">Błąd generowania raportu</p>');
            console.error('Błąd:', xhr);
        }
    });
}

// Wyświetl raporty w tabeli
function displayReports(reports) {
    if (!reports || reports.length === 0) {
        $('#reportsTableContainer').html('<p class="loading">Brak raportów dla wybranych kryteriów</p>');
        return;
    }

    // Opcjonalnie filtruj tylko Lock/Unlock jeśli checkbox zaznaczony
    const filterLockUnlock = $('#lockUnlockFilter').is(':checked');
    let filteredReports = reports;
    
    if (filterLockUnlock) {
        filteredReports = reports.filter(report => 
            report.event_type === 'lock' || report.event_type === 'unlock'
        );
    }

    if (filteredReports.length === 0) {
        $('#reportsTableContainer').html('<p class="loading">Brak raportów typu Lock/Unlock</p>');
        return;
    }

    let tableHTML = `
        <table class="workers-table">
            <thead>
                <tr>
                    <th>ID Raportu</th>
                    <th>ID Pracownika</th>
                    <th>Typ Zdarzenia</th>
                    <th>Data i Czas</th>
                    <th>Opis</th>
                </tr>
            </thead>
            <tbody>
    `;

    filteredReports.forEach(function(report) {
        const eventDate = new Date(report.created_at).toLocaleString('pl-PL');
        const eventType = report.event_type || 'N/A';
        const description = report.description || '-';

        tableHTML += `
            <tr>
                <td>${report.id}</td>
                <td>${report.employee_id}</td>
                <td><span class="status-badge ${eventType === 'lock' || eventType === 'unlock' ? 'status-active' : 'status-inactive'}">${eventType}</span></td>
                <td>${eventDate}</td>
                <td>${description}</td>
            </tr>
        `;
    });

    tableHTML += `
            </tbody>
        </table>
        <div style="margin-top: 20px; text-align: center; color: white;">
            <strong>Liczba rekordów: ${filteredReports.length}</strong>
        </div>
    `;

    $('#reportsTableContainer').html(tableHTML);
}