// add.js - Logika strony dodawania pracownika

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

    // Przycisk "Dodaj Pracownika" (POST)
    $('#addBtn').on('click', function() {
        addEmployee();
    });

    // Przycisk "Anuluj"
    $('#cancelBtn').on('click', function() {
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

    // Walidacja formularza przy submit
    $('#addEmployeeForm').on('submit', function(e) {
        e.preventDefault();
        addEmployee();
    });
});

// Dodaj nowego pracownika (POST)
function addEmployee() {
    const newEmployee = {
        first_name: $('#firstName').val().trim(),
        last_name: $('#lastName').val().trim(),
        email: $('#email').val().trim()
    };

    // Walidacja
    if (!newEmployee.first_name || !newEmployee.last_name || !newEmployee.email) {
        showMessage('Proszę wypełnić wszystkie pola', 'error');
        return;
    }

    // Walidacja email
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailPattern.test(newEmployee.email)) {
        showMessage('Proszę podać poprawny adres email', 'error');
        return;
    }

    $.ajax({
        url: `${API_BASE_URL}/create_employee`,
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(newEmployee),
        success: function(response) {
            showMessage('Pracownik został dodany pomyślnie!', 'success');
            
            // Wyczyść formularz
            $('#addEmployeeForm')[0].reset();
            
            // Przekieruj po 2 sekundach
            setTimeout(() => {
                window.location.href = 'dashboard.html';
            }, 2000);
        },
        error: function(xhr) {
            if (xhr.status === 409 || xhr.status === 400) {
                showMessage(xhr.responseJSON?.detail || 'Pracownik z takim emailem już istnieje', 'error');
            } else {
                showMessage('Błąd podczas dodawania pracownika', 'error');
            }
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