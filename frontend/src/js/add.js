$(document).ready(function() {
    console.log("✅ add.js v9 - Auto-korekta dat");
    const API_BASE_URL = "http://localhost:8000/admin";

    // --- DATA HELPERS ---
    function getTodayString() { return new Date().toISOString().split('T')[0]; }
    function getFutureString(months = 6) {
        const d = new Date();
        d.setMonth(d.getMonth() + months);
        return d.toISOString().split('T')[0];
    }

    // INIT: Domyślne wartości
    $("#hireDate").val(getTodayString());
    $("#expirationDate").val(getFutureString(6));
    
    // Inicjalizacja blokady kalendarza na starcie
    $("#expirationDate").attr("min", getTodayString());

    // --- AUTO-KOREKTA I BLOKADY (Logika z edit.js przeniesiona tutaj) ---
    $("#hireDate").on("change", function() {
        const hireVal = $(this).val();
        
        if (hireVal) {
            // 1. Ustawiamy MINIMUM w kalendarzu wygaśnięcia (żeby nie dało się kliknąć wstecz)
            $("#expirationDate").attr("min", hireVal);

            // 2. AUTO-KOREKTA WARTOŚCI
            // Sprawdzamy, czy aktualnie wpisana data wygaśnięcia nie stała się "przestarzała"
            const expireVal = $("#expirationDate").val();
            
            if (expireVal && expireVal < hireVal) {
                console.log("⚠️ Data wygaśnięcia była wcześniejsza niż zatrudnienie - automatyczna korekta.");
                // Przesuwamy datę wygaśnięcia na datę zatrudnienia (bezpieczne minimum)
                // Można też ustawić np. hireVal + 6 miesięcy, ale bezpieczniej po prostu wyrównać.
                $("#expirationDate").val(hireVal);
            }
        }
    });

    // --- BUTTONS ---
    $("#backBtn, #cancelBtn").on("click", function(e) {
        e.preventDefault();
        window.location.href = "dashboard.html";
    });

    // --- ADD ACTION ---
    $("#addBtn").on("click", async function(e) {
        e.preventDefault();

        // 1. Zabezpieczenie pustych dat (fallback)
        if (!$("#hireDate").val()) $("#hireDate").val(getTodayString());
        
        // 2. Pobranie wartości
        const hireVal = $("#hireDate").val();
        const expireVal = $("#expirationDate").val();

        // 3. TWARDA WALIDACJA (Bezpiecznik)
        // Mimo auto-korekty, zostawiamy to sprawdzenie na wypadek wpisania daty z klawiatury
        if (hireVal && expireVal) {
            if (expireVal < hireVal) {
                alert("⛔ BŁĄD DATY: Data wygaśnięcia konta (" + expireVal + ") \nnie może być wcześniejsza niż data zatrudnienia (" + hireVal + ")!");
                
                // Jeśli auto-korekta z jakiegoś powodu nie zadziałała, naprawiamy to teraz
                $("#expirationDate").val(hireVal).focus(); 
                return; // STOP
            }
        }

        // 4. Walidacja HTML5 (wymagane pola tekstowe)
        const form = document.getElementById("addEmployeeForm");
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }

        // 5. Blokada przycisku
        const $btn = $(this);
        $btn.prop("disabled", true).text("Wysyłanie...");

        // 6. Payload
        const employeeData = {
            first_name: $("#firstName").val(),
            last_name: $("#lastName").val(),
            email: $("#email").val(),
            hire_date: hireVal,
            expiration_date: expireVal || null
        };

        try {
            // KROK 1: Create
            const createResponse = await $.ajax({
                url: `${API_BASE_URL}/create_employee`, 
                method: "POST",
                contentType: "application/json",
                data: JSON.stringify(employeeData)
            });

            console.log("✅ Utworzono:", createResponse.id);
            let message = "Pracownik dodany pomyślnie.";

            // KROK 2: Photo
            const fileInput = document.getElementById("employeePhoto");
            if (fileInput && fileInput.files.length > 0) {
                const formData = new FormData();
                formData.append("file", fileInput.files[0]);
                try {
                    await $.ajax({
                        url: `${API_BASE_URL}/employees/${createResponse.id}/upload_photo`,
                        method: "POST",
                        processData: false, contentType: false, data: formData
                    });
                    message += "\nZdjęcie wgrane.";
                } catch (err) {
                    console.error(err);
                    message += "\n(Błąd zdjęcia)";
                }
            }

            alert(message);
            window.location.href = "dashboard.html";

        } catch (error) {
            console.error("Błąd:", error);
            $btn.prop("disabled", false).text("Add Employee");
            let msg = error.responseJSON?.detail || "Błąd serwera";
            alert("Błąd: " + msg);
        }
    });
});