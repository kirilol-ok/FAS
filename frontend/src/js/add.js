$(document).ready(function() {
    console.log("✅ add.js v6 - Z funkcją dodawania zdjęcia");
    const API_BASE_URL = "http://localhost:8000/admin";

    // --- 1. FUNKCJE POMOCNICZE (DATY) ---
    function getTodayString() {
        return new Date().toISOString().split('T')[0];
    }
    function getFutureString(months = 6) {
        const d = new Date();
        d.setMonth(d.getMonth() + months);
        return d.toISOString().split('T')[0];
    }

    // Ustawienie domyślnych dat przy wejściu na stronę
    $("#hireDate").val(getTodayString());
    $("#expirationDate").val(getFutureString(6));

    // --- 2. OBSŁUGA PRZYCISKÓW ---
    $("#backBtn, #cancelBtn").on("click", function(e) {
        e.preventDefault();
        window.location.href = "dashboard.html";
    });

    // --- 3. GŁÓWNA LOGIKA DODAWANIA ---
    $("#addBtn").on("click", async function(e) {
        e.preventDefault(); // Blokada przeładowania

        // A. ZABEZPIECZENIE DAT (Wpisz domyślne, jeśli puste)
        if (!$("#hireDate").val()) $("#hireDate").val(getTodayString());
        if (!$("#expirationDate").val()) $("#expirationDate").val(getFutureString(6));

        // B. WALIDACJA FORMULARZA
        const form = document.getElementById("addEmployeeForm");
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }

        // C. BLOKADA PRZYCISKU
        const $btn = $(this);
        $btn.prop("disabled", true).text("Wysyłanie...");

        // D. PRZYGOTOWANIE DANYCH
        const employeeData = {
            first_name: $("#firstName").val(),
            last_name: $("#lastName").val(),
            email: $("#email").val(),
            hire_date: $("#hireDate").val(),
            expiration_date: $("#expirationDate").val() || null
        };

        try {
            console.log("🚀 KROK 1: Tworzenie pracownika...", employeeData);

            // --- KROK 1: AJAX - CREATE EMPLOYEE ---
            const createResponse = await $.ajax({
                url: `${API_BASE_URL}/create_employee`, 
                method: "POST",
                contentType: "application/json",
                data: JSON.stringify(employeeData)
            });

            console.log("✅ Pracownik utworzony. ID:", createResponse.id);
            let message = "Pracownik dodany pomyślnie.";

            // --- KROK 2: AJAX - UPLOAD ZDJĘCIA ---
            const fileInput = document.getElementById("employeePhoto");
            
            // Sprawdzamy, czy użytkownik wybrał plik
            if (fileInput && fileInput.files.length > 0) {
                console.log("📸 KROK 2: Wykryto zdjęcie. Wysyłanie...");
                
                const formData = new FormData();
                formData.append("file", fileInput.files[0]);

                try {
                    await $.ajax({
                        // Używamy ID utworzonego przed chwilą pracownika
                        url: `${API_BASE_URL}/employees/${createResponse.id}/upload_photo`,
                        method: "POST",
                        processData: false, // Ważne dla plików!
                        contentType: false, // Ważne dla plików!
                        data: formData
                    });
                    
                    console.log("✅ Zdjęcie wgrane i embedding utworzony.");
                    message += "\nZdjęcie zostało dodane.";
                } catch (photoError) {
                    console.error("❌ Błąd zdjęcia:", photoError);
                    message += "\nUWAGA: Pracownik dodany, ale wystąpił błąd przy wgrywaniu zdjęcia.";
                }
            } else {
                console.log("ℹ️ Nie wybrano zdjęcia - pomijam ten krok.");
            }

            // E. FINALIZACJA
            alert(message);
            window.location.href = "dashboard.html";

        } catch (error) {
            console.error("❌ BŁĄD:", error);
            $btn.prop("disabled", false).text("Add Employee");
            
            let errMsg = "Błąd: " + (error.responseJSON?.detail || "Nieznany błąd serwera");
            alert(errMsg);
        }
    });
});