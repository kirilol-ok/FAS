$(document).ready(function() {
    const API_BASE_URL = "http://localhost:8000/admin";

    // Zachowane: Obsługa przycisków powrotu
    $("#backBtn, #cancelBtn").on("click", function() {
        window.location.href = "dashboard.html";
    });

    $("#addEmployeeForm").on("submit", async function(e) {
        e.preventDefault();

        // 1. ZACHOWANE: Pobieranie danych tekstowych tak jak wcześniej
        const employeeData = {
            first_name: $("#firstName").val(),
            last_name: $("#lastName").val(),
            email: $("#email").val()
        };

        try {
            // KROK 1: Tworzenie pracownika (stara logika)
            const createResponse = await $.ajax({
                url: `${API_BASE_URL}/create_employee`, 
                method: "POST",
                contentType: "application/json",
                data: JSON.stringify(employeeData)
            });

            console.log("Pracownik utworzony, ID:", createResponse.id);

            // KROK 2: NOWOŚĆ - Sprawdzenie i wysyłka zdjęcia
            // Musisz dodać <input type="file" id="employeePhoto"> w pliku HTML
            const fileInput = document.getElementById("employeePhoto");
            
            if (fileInput && fileInput.files.length > 0) {
                console.log("Wykryto zdjęcie. Rozpoczynam upload...");
                
                const formData = new FormData();
                formData.append("file", fileInput.files[0]);

                // Wysyłamy na nowy endpoint (zakładając, że dodałeś go do admin.py)
                await $.ajax({
                    url: `${API_BASE_URL}/employees/${createResponse.id}/upload_photo`,
                    method: "POST",
                    processData: false, // Wymagane dla plików
                    contentType: false, // Wymagane dla plików
                    data: formData
                });
                
                alert(`Dodano pracownika ${createResponse.last_name} oraz wgrano zdjęcie.`);
            } else {
                // Jeśli nie wybrano zdjęcia, komunikat jak dawniej
                alert(`Dodano pracownika: ${createResponse.first_name} ${createResponse.last_name}`);
            }

            // ZACHOWANE: Powrót do dashboardu
            window.location.href = "dashboard.html";

        } catch (xhr) {
            // ZACHOWANE: Obsługa błędów
            console.error("Błąd dodawania: ", xhr);
            let msg = "Błąd podczas dodawania pracownika.";
            if (xhr.responseJSON && xhr.responseJSON.detail) {
                msg += "\nSzczegóły: " + xhr.responseJSON.detail;
            }
            alert(msg);
        }
    });
});