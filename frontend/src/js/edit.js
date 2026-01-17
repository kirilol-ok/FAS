$(document).ready(function() {
    const API_BASE_URL = "http://localhost:8000/admin";

    // 1. ZACHOWANE: Weryfikacja autoryzacji
    const authToken = localStorage.getItem('authToken');
    if (!authToken) {
        window.location.href = 'index.html';
        return;
    }

    const adminName = localStorage.getItem('adminName');
    if (adminName) $('#adminName').text(adminName);

    // 2. ZACHOWANE: Pobieranie ID z URL
    const urlParams = new URLSearchParams(window.location.search);
    const employeeId = urlParams.get('id');

    if (!employeeId) {
        alert("Błąd: Brak ID pracownika.");
        window.location.href = "dashboard.html";
        return;
    }

    // Ładowanie danych (funkcja na dole pliku)
    loadEmployeeData(employeeId);

    // 3. ZACHOWANE: Logika interfejsu (ukrywanie daty zwolnienia)
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

    // Przyciski nawigacyjne
    $("#backBtn, #cancelBtn").on("click", function() {
        window.location.href = "dashboard.html";
    });

    $("#logoutBtn").on("click", function() {
        localStorage.clear();
        window.location.href = "index.html";
    });

    // --- GŁÓWNA ZMIANA: OBSŁUGA ZAPISU (ASYNC) ---
    $("#editEmployeeForm").on("submit", async function(e) {
        e.preventDefault();

        // 4. ZACHOWANE: Logika przygotowania danych (data zwolnienia)
        let finalDate = null;
        let isDismissed = $('#dismissCheckbox').is(':checked');

        if (isDismissed) {
            finalDate = $('#dismissDate').val();
            if (!finalDate) {
                finalDate = new Date().toISOString().split('T')[0]; // Domyślnie dzisiaj
            }
        }

        // Obiekt z danymi do PATCH (stara logika)
        const updateData = {
            first_name: $("#firstName").val(),
            last_name: $("#lastName").val(),
            email: $("#email").val(),
            dismissed: isDismissed,
            dismissal_date: finalDate 
        };

        try {
            // KROK 1: Aktualizacja danych tekstowych i statusu (PATCH)
            await $.ajax({
                url: `${API_BASE_URL}/update_employees/${employeeId}`,
                method: "PATCH",
                contentType: "application/json",
                data: JSON.stringify(updateData)
            });

            // KROK 2: NOWOŚĆ - Upload zdjęcia (tylko jeśli wybrano plik)
            const fileInput = document.getElementById("employeePhoto");
            
            if (fileInput && fileInput.files.length > 0) {
                console.log("Wykryto nowe zdjęcie. Wysyłanie...");
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

            // Sukces - powrót
            alert("Zapisano zmiany!");
            window.location.href = "dashboard.html";

        } catch (xhr) {
            // ZACHOWANE: Obsługa błędów z backendu (Pydantic validation errors)
            console.error("Błąd zapisu:", xhr);
            let msg = "Wystąpił błąd.";
            
            if (xhr.responseJSON && xhr.responseJSON.detail) {
                if (Array.isArray(xhr.responseJSON.detail)) {
                    // Jeśli lista błędów walidacji
                    msg += "\n" + xhr.responseJSON.detail.map(e => e.msg).join(", ");
                } else {
                    msg += "\n" + xhr.responseJSON.detail;
                }
            }
            alert(msg);
        }
    });

    // 5. ZACHOWANE: Logika usuwania pracownika
    $("#deleteBtn").on("click", function() {
        if (confirm("Czy na pewno chcesz usunąć pracownika?")) {
            $.ajax({
                url: `${API_BASE_URL}/delete_employees/${employeeId}`,
                method: "DELETE",
                success: function() {
                    alert("Pracownik został usunięty.");
                    window.location.href = "dashboard.html";
                },
                error: function(xhr) {
                    alert("Błąd usuwania.");
                    console.error(xhr);
                }
            });
        }
    });

    // 6. ZACHOWANE: Funkcja ładująca dane do formularza
    function loadEmployeeData(id) {
        $.ajax({
            url: `${API_BASE_URL}/employees/${id}`,
            method: "GET",
            success: function(employee) {
                $('#employeeId').val(employee.id);
                $('#firstName').val(employee.first_name);
                $('#lastName').val(employee.last_name);
                $('#email').val(employee.email);

                // Ustawienie checkboxa i daty, jeśli pracownik zwolniony
                if (employee.dismissed) {
                    $('#dismissCheckbox').prop('checked', true);
                    $('#dismissDateGroup').show();
                    
                    if (employee.dismissal_date) {
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