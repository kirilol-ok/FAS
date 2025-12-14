// edit.js - Logika strony edycji pracownika

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

    // Pobierz ID pracownika z URL
    const urlParams = new URLSearchParams(window.location.search);
    const employeeId = urlParams.get('id');

    if (!employeeId) {
        alert('Brak ID pracownika');
        window.location.href = 'dashboard.html';
        return;
    }

    // Załaduj dane pracownika
    loadEmployeeData(employeeId);

    // Obsługa checkboxa "Zwolnij"
    $('#dismissCheckbox').on('change', function() {
        if ($(this).is(':checked')) {
            $('#dismissDateGroup').show();
            const today = new Date().toISOString().split('T')[0];
            $('#dismissDate').val(today);
        } else {
            $('#dismissDateGroup').hide();
            $('#dismissDate').val('');
        }
    });

    // Przycisk "Zapisz" (PUT)
    $('#saveBtn').on('click', function() {
        saveEmployee(employeeId);
    });

    // Przycisk "Usuń" (DELETE)
    $('#deleteBtn').on('click', function() {
        deleteEmployee(employeeId);
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

// Załaduj dane pracownika z API
function loadEmployeeData(employeeId) {
    $.ajax({
        url: `${API_BASE_URL}/employees/${employeeId}`,
        method: 'GET',
        success: function(employee) {
            $('#employeeId').val(employee.id);
            $('#firstName').val(employee.first_name);
            $('#lastName').val(employee.last_name);
            $('#email').val(employee.email);

            // Jeśli pracownik ma datę zwolnienia
            if (employee.dismissal_date) {
                $('#dismissCheckbox').prop('checked', true);
                $('#dismissDateGroup').show();
                $('#dismissDate').val(employee.dismissal_date.split('T')[0]);
            }
        },
        error: function(xhr) {
            showMessage('Błąd wczytywania danych pracownika', 'error');
            console.error('Błąd:', xhr);
        }
    });
}

// Zapisz zmiany (PUT/PATCH)
function saveEmployee(employeeId) {
    const updateData = {
        first_name: $('#firstName').val(),
        last_name: $('#lastName').val(),
        email: $('#email').val(),
        dismissal_date: $('#dismissCheckbox').is(':checked') ? $('#dismissDate').val() : null
    };

    $.ajax({
        url: `${API_BASE_URL}/employees/${employeeId}`,
        method: 'PATCH',
        contentType: 'application/json',
        data: JSON.stringify(updateData),
        success: function(response) {
            showMessage('Dane pracownika zostały zaktualizowane!', 'success');
            setTimeout(() => {
                window.location.href = 'dashboard.html';
            }, 1500);
        },
        error: function(xhr) {
            showMessage('Błąd podczas zapisywania zmian', 'error');
            console.error('Błąd:', xhr);
        }
    });
}

// Usuń pracownika (DELETE)
function deleteEmployee(employeeId) {
    if (!confirm('Czy na pewno chcesz usunąć tego pracownika?')) {
        return;
    }

    $.ajax({
        url: `${API_BASE_URL}/employees/${employeeId}`,
        method: 'DELETE',
        success: function() {
            showMessage('Pracownik został usunięty', 'success');
            setTimeout(() => {
                window.location.href = 'dashboard.html';
            }, 1500);
        },
        error: function(xhr) {
            showMessage('Błąd podczas usuwania pracownika', 'error');
            console.error('Błąd:', xhr);
        }
    });
}

// Wyświetl wiadomość
function showMessage(message, type) {
    const $messageDiv = $('#formMessage');
    $messageDiv.text(message)
        .removeClass('success error')
        .addClass(type);
}