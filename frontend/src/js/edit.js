$(document).ready(function() {
    const API_BASE_URL = "http://localhost:8000/admin";

    // Sprawdzenie autoryzacji
    const authToken = localStorage.getItem('authToken');
    if (!authToken) {
        window.location.href = 'index.html';
        return;
    }

    const adminName = localStorage.getItem('adminName');
    if (adminName) $('#adminName').text(adminName);

    // Pobranie ID z URL
    const urlParams = new URLSearchParams(window.location.search);
    const employeeId = urlParams.get('id');

    if (!employeeId) {
        alert("Błąd: Brak ID pracownika.");
        window.location.href = "dashboard.html";
        return;
    }

    // Załaduj dane
    loadEmployeeData(employeeId);

    // --- OBSŁUGA CHECKBOXA ---
    $('#dismissCheckbox').on('change', function() {
        if ($(this).is(':checked')) {
            $('#dismissDateGroup').slideDown();
            // Jeśli data jest pusta, wstaw dzisiejszą
            if (!$('#dismissDate').val()) {
                const today = new Date().toISOString().split('T')[0];
                $('#dismissDate').val(today);
            }
        } else {
            $('#dismissDateGroup').slideUp();
            $('#dismissDate').val(''); // Wyczyść input
        }
    });

    $("#backBtn, #cancelBtn").on("click", function() {
        window.location.href = "dashboard.html";
    });

    $("#logoutBtn").on("click", function() {
        localStorage.clear();
        window.location.href = "index.html";
    });

    // --- ZAPISYWANIE (PATCH) ---
    $("#editEmployeeForm").on("submit", function(e) {
        e.preventDefault();

        // 1. Logika daty: Musi być NULL albo poprawny string YYYY-MM-DD.
        // Pusty string "" spowoduje błąd backendu.
        let finalDate = null;
        let isDismissed = $('#dismissCheckbox').is(':checked');

        if (isDismissed) {
            finalDate = $('#dismissDate').val();
            // Zabezpieczenie: jeśli checkbox zaznaczony, a data pusta -> wstaw dzisiejszą
            if (!finalDate) {
                finalDate = new Date().toISOString().split('T')[0];
            }
        }

        const updateData = {
            first_name: $("#firstName").val(),
            last_name: $("#lastName").val(),
            email: $("#email").val(),
            dismissed: isDismissed,
            dismissal_date: finalDate // Tu trafi albo null albo "2023-01-01"
        };

        $.ajax({
            // UWAGA: Twój backend ma endpoint /update_employees/{id}
            url: `${API_BASE_URL}/update_employees/${employeeId}`,
            method: "PATCH",
            contentType: "application/json",
            data: JSON.stringify(updateData),
            success: function(response) {
                alert("Zapisano zmiany!");
                window.location.href = "dashboard.html";
            },
            error: function(xhr) {
                console.error("Błąd zapisu:", xhr);
                let msg = "Wystąpił błąd.";
                
                // Wyświetl dokładny błąd z serwera, jeśli dostępny
                if (xhr.responseJSON && xhr.responseJSON.detail) {
                    // Czasem detail to tablica błędów walidacji
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

    // --- USUWANIE (DELETE) ---
    $("#deleteBtn").on("click", function() {
        if (confirm("Czy na pewno usunąć pracownika?")) {
            $.ajax({
                // UWAGA: Twój backend ma endpoint /delete_employees/{id}
                url: `${API_BASE_URL}/delete_employees/${employeeId}`,
                method: "DELETE",
                success: function() {
                    alert("Usunięto pracownika.");
                    window.location.href = "dashboard.html";
                },
                error: function(xhr) {
                    alert("Błąd usuwania.");
                    console.error(xhr);
                }
            });
        }
    });

    // --- POBIERANIE DANYCH ---
    function loadEmployeeData(id) {
        $.ajax({
            // Twój backend ma endpoint /employees/{id} do pobierania
            url: `${API_BASE_URL}/employees/${id}`,
            method: "GET",
            success: function(employee) {
                $('#employeeId').val(employee.id);
                $('#firstName').val(employee.first_name);
                $('#lastName').val(employee.last_name);
                $('#email').val(employee.email);

                // Ustawienie stanu checkboxa
                if (employee.dismissed) {
                    $('#dismissCheckbox').prop('checked', true);
                    $('#dismissDateGroup').show();
                    
                    if (employee.dismissal_date) {
                        // Formatowanie daty (ucięcie czasu, jeśli jest)
                        $('#dismissDate').val(employee.dismissal_date.split('T')[0]);
                    }
                }
            },
            error: function(xhr) {
                alert("Nie znaleziono pracownika.");
                window.location.href = "dashboard.html";
            }
        });
    }
});