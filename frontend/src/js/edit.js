$(document).ready(function() {
    console.log("✅ edit.js v-FINAL załadowany");
    const API_BASE_URL = "http://localhost:8000/admin";

    // --- FUNKCJE POMOCNICZE ---

    // Ta funkcja naprawia problem z wyświetlaniem daty
    function safeDate(value) {
        if (!value) return ""; // Jeśli null/undefined -> puste pole
        
        // Konwertujemy na string (dla bezpieczeństwa)
        const strVal = String(value);
        
        // Jeśli format to ISO (np. 2026-01-21T14:30:00), bierzemy tylko pierwszą część
        if (strVal.includes("T")) {
            return strVal.split("T")[0];
        }
        
        // Jeśli to już jest "2026-01-21", zwracamy bez zmian
        return strVal;
    }

    // --- 1. WERYFIKACJA I INIT ---
    const authToken = localStorage.getItem('authToken');
    if (!authToken) {
        window.location.href = 'index.html';
        return;
    }

    const adminName = localStorage.getItem('adminName');
    if (adminName) $('#adminName').text(adminName);

    const urlParams = new URLSearchParams(window.location.search);
    const employeeId = urlParams.get('id');

    if (!employeeId) {
        alert("Błąd: Brak ID pracownika.");
        window.location.href = "dashboard.html";
        return;
    }

    // --- 2. ŁADOWANIE DANYCH (To naprawia puste pola) ---
    loadEmployeeData(employeeId);

    // --- 3. OBSŁUGA INTERFEJSU ---
    $('#dismissCheckbox').on('change', function() {
        if ($(this).is(':checked')) {
            $('#dismissDateGroup').slideDown();
            // Jeśli zaznaczono, a data pusta -> wstaw dzisiejszą
            if (!$('#dismissDate').val()) {
                $('#dismissDate').val(new Date().toISOString().split('T')[0]);
            }
        } else {
            $('#dismissDateGroup').slideUp();
            $('#dismissDate').val('');
        }
    });

    $("#backBtn, #cancelBtn").on("click", function() {
        window.location.href = "dashboard.html";
    });

    $("#logoutBtn").on("click", function() {
        localStorage.clear();
        window.location.href = "index.html";
    });

    // --- 4. ZAPISYWANIE DANYCH (SAVE) ---
    $("#editEmployeeForm").on("submit", async function(e) {
        e.preventDefault();

        // Logika daty zwolnienia
        let finalDismissalDate = null;
        const isDismissed = $('#dismissCheckbox').is(':checked');
        
        if (isDismissed) {
            finalDismissalDate = $('#dismissDate').val();
            // Fallback na dzisiaj, jeśli puste
            if (!finalDismissalDate) {
                finalDismissalDate = new Date().toISOString().split('T')[0];
            }
        }

        // Pobieranie wartości z inputów (NAPRAWIONE: definicje zmiennych)
        const hireDateVal = $("#hireDate").val();
        const expirationDateVal = $("#expirationDate").val();

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
            console.log("🚀 Wysyłanie update:", updateData);

            // KROK 1: PATCH danych tekstowych
            await $.ajax({
                url: `${API_BASE_URL}/update_employees/${employeeId}`,
                method: "PATCH",
                contentType: "application/json",
                data: JSON.stringify(updateData)
            });

            // KROK 2: Upload zdjęcia (jeśli wybrano nowe)
            const fileInput = document.getElementById("employeePhoto");
            if (fileInput && fileInput.files.length > 0) {
                console.log("📸 Wykryto nowe zdjęcie. Wysyłanie...");
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

            alert("Zapisano zmiany!");
            window.location.href = "dashboard.html";

        } catch (xhr) {
            console.error("❌ Błąd zapisu:", xhr);
            let msg = "Wystąpił błąd.";
            
            if (xhr.responseJSON && xhr.responseJSON.detail) {
                const detail = xhr.responseJSON.detail;
                if (Array.isArray(detail)) {
                    msg += "\n" + detail.map(e => e.msg).join(", ");
                } else {
                    msg += "\n" + detail;
                }
            }
            alert(msg);
        }
    });

    // --- 5. USUWANIE ---
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

    // --- 6. FUNKCJA ŁADUJĄCA DANE ---
    function loadEmployeeData(id) {
        console.log("📥 Pobieranie danych dla ID:", id);
        
        $.ajax({
            url: `${API_BASE_URL}/employees/${id}`,
            method: "GET",
            success: function(employee) {
                console.log("✅ Otrzymano dane z backendu:", employee);

                // ID (readonly)
                $('#employeeId').val(employee.id);
                
                // Teksty
                $('#firstName').val(employee.first_name);
                $('#lastName').val(employee.last_name);
                $('#email').val(employee.email);

                // DATY - Używamy funkcji safeDate!
                // To kluczowy moment - funkcja przytnie "T" jeśli trzeba
                $('#hireDate').val(safeDate(employee.hire_date));
                $('#expirationDate').val(safeDate(employee.expiration_date));

                // Zwolnienie
                if (employee.dismissed) {
                    $('#dismissCheckbox').prop('checked', true);
                    $('#dismissDateGroup').show();
                    $('#dismissDate').val(safeDate(employee.dismissal_date));
                }
            },
            error: function(xhr) {
                console.error("Błąd pobierania:", xhr);
                alert("Nie udało się pobrać danych pracownika.");
                window.location.href = "dashboard.html";
            }
        });
    }
});