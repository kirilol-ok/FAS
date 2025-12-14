<<<<<<< Updated upstream
const API_BASE_URL = "/admin";

function loginUser(credentials) {
  return $.ajax({
    url: `${API_BASE_URL}/login`,
    method: "POST",
    contentType: "application/json",
    data: JSON.stringify({
      email: credentials.login,
      password: credentials.password,
    }),
  });
}

function getCurrentAdmin(email) {
  return $.ajax({
    url: `${API_BASE_URL}/me`,
    method: "GET",
    data: { email: email },
  });
}

function getWorkersTable() {
  return $.ajax({
    url: `${API_BASE_URL}/employees`,
    method: "GET",
  });
}

function getEmployeeDetails(employeeId) {
  return $.ajax({
    url: `${API_BASE_URL}/employees/${employeeId}`,
    method: "GET",
  });
}

function updateEmployee(employeeId, updateData) {
  return $.ajax({
    url: `${API_BASE_URL}/employees/${employeeId}`,
    method: "PATCH",
    contentType: "application/json",
    data: JSON.stringify(updateData),
  });
}

function generateReport(reportData) {
  return $.ajax({
    url: `${API_BASE_URL}/reports/generate`,
    method: "POST",
    contentType: "application/json",
    data: JSON.stringify(reportData),
  });
}

function generateWorkersTableHTML(workers) {
  if (!workers || workers.length === 0) {
    return '<p class="loading">No employees found in the database.</p>';
  }

  let tableHTML = `
        <table class="workers-table">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>First Name</th>
                    <th>Last Name</th>
                    <th>Email</th>
                    <th>Status</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
    `;

  workers.forEach(function (worker) {
    const isActive = !worker.dismissal_date;
    const statusClass = isActive ? "status-active" : "status-inactive";
    const statusText = isActive ? "Active" : "Inactive";

    tableHTML += `
            <tr>
                <td>${worker.id}</td>
                <td>${worker.first_name || ""}</td>
                <td>${worker.last_name || ""}</td>
                <td>${worker.email || ""}</td>
                <td><span class="status-badge ${statusClass}">${statusText}</span></td>
                <td><button class="btn btn-secondary btn-edit-worker" data-id="${worker.id}">Edit</button></td>
            </tr>
        `;
  });

  tableHTML += `
            </tbody>
        </table>
    `;

  return tableHTML;
}

$(document).ready(function () {
  if ($("#loginForm").length) {
    $("#loginForm").on("submit", function (e) {
      e.preventDefault();

      const credentials = {
        login: $("#login").val(),
        password: $("#password").val(),
      };

      if (!credentials.login || !credentials.password) {
        $("#errorMessage").text("Please fill in all fields").addClass("show");
        return;
      }

      $("#errorMessage").removeClass("show");

      loginUser(credentials)
        .done(function (response) {
          localStorage.setItem("authToken", response.access_token);
          localStorage.setItem("adminEmail", credentials.login);
          localStorage.setItem("adminName", response.admin_name);

          window.location.href = "dashboard.html";
        })
        .fail(function (xhr) {
          if (xhr.status === 401) {
            $("#errorMessage")
              .text("Invalid login or password")
              .addClass("show");
          } else {
            $("#errorMessage")
              .text("Connection error. Please try again.")
              .addClass("show");
          }
        });
    });
  }

  if ($("#adminName").length) {
    const authToken = localStorage.getItem("authToken");
    if (!authToken) {
      window.location.href = "index.html";
      return;
    }

    const adminEmail = localStorage.getItem("adminEmail");
    const adminName = localStorage.getItem("adminName");

    if (adminName) {
      $("#adminName").text(adminName);
    } else if (adminEmail) {
      getCurrentAdmin(adminEmail)
        .done(function (adminData) {
          $("#adminName").text(adminData.first_name);
          localStorage.setItem("adminName", adminData.first_name);
        })
        .fail(function () {
          $("#adminName").text("Admin");
        });
    }

    //it will be changed
    getWorkersTable()
      .done(function (workers) {
        const tableHTML = generateWorkersTableHTML(workers);
        $("#workersTableContainer").html(tableHTML);

        $(".btn-edit-worker").on("click", function () {
          const employeeId = $(this).data("id");
          alert(
            `Editing employee ID: ${employeeId}\n\nIn full version redirect to edit.html?id=${employeeId}`,
          );
        });
      })
      .fail(function (xhr) {
        $("#workersTableContainer").html(
          '<p class="loading">Error loading employee data.</p>',
        );
        console.error("Error fetching employees:", xhr);
      });

    $("#editBtn").on("click", function () {
      alert(
        'Redirecting to employee edit page\n\nIn full version: window.location.href = "edit.html"',
      );
    });

    $("#reportsBtn").on("click", function () {
      alert(
        'Redirecting to reports page\n\nIn full version: window.location.href = "reports.html"',
      );
    });

    $("#logoutBtn").on("click", function () {
      localStorage.removeItem("authToken");
      localStorage.removeItem("adminEmail");
      localStorage.removeItem("adminName");
      window.location.href = "index.html";
    });
  }
});
=======
// Konfiguracja API
const API_BASE_URL = 'http://localhost:8000/admin'; // Zmień na właściwy URL jeśli potrzeba

// ==========================================
// ID AKCJI: 1 - Login (POST)
// ==========================================
function loginUser(credentials) {
    return $.ajax({
        url: `${API_BASE_URL}/login`,
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            email: credentials.login,
            password: credentials.password
        })
    });
}

// ==========================================
// ID AKCJI: 2 - Pobierz dane aktualnego admina (GET)
// ==========================================
function getCurrentAdmin(email) {
    return $.ajax({
        url: `${API_BASE_URL}/me`,
        method: 'GET',
        data: { email: email }
    });
}

// ==========================================
// ID AKCJI: 3 - Pobierz tabelę pracowników (GET)
// ==========================================
function getWorkersTable() {
    return $.ajax({
        url: `${API_BASE_URL}/employees`,
        method: 'GET'
    });
}

// ==========================================
// ID AKCJI: 4 - Pobierz dane pracownika do edycji (GET)
// ==========================================
function getEmployeeDetails(employeeId) {
    return $.ajax({
        url: `${API_BASE_URL}/employees/${employeeId}`,
        method: 'GET'
    });
}

// Aktualizacja danych pracownika (PATCH)
function updateEmployee(employeeId, updateData) {
    return $.ajax({
        url: `${API_BASE_URL}/employees/${employeeId}`,
        method: 'PATCH',
        contentType: 'application/json',
        data: JSON.stringify(updateData)
    });
}

// ==========================================
// ID AKCJI: 5 - Generuj raport (POST)
// ==========================================
function generateReport(reportData) {
    return $.ajax({
        url: `${API_BASE_URL}/reports/generate`,
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(reportData)
    });
}

// ==========================================
// Funkcje pomocnicze
// ==========================================

// Generowanie HTML tabeli pracowników
function generateWorkersTableHTML(workers) {
    if (!workers || workers.length === 0) {
        return '<p class="loading">Brak pracowników w bazie danych.</p>';
    }

    let tableHTML = `
        <table class="workers-table">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Imię</th>
                    <th>Nazwisko</th>
                    <th>Email</th>
                    <th>Status</th>
                    <th>Akcje</th>
                </tr>
            </thead>
            <tbody>
    `;

    workers.forEach(function(worker) {
        const isActive = !worker.dismissal_date;
        const statusClass = isActive ? 'status-active' : 'status-inactive';
        const statusText = isActive ? 'Aktywny' : 'Nieaktywny';
        
        tableHTML += `
            <tr>
                <td>${worker.id}</td>
                <td>${worker.first_name || ''}</td>
                <td>${worker.last_name || ''}</td>
                <td>${worker.email || ''}</td>
                <td><span class="status-badge ${statusClass}">${statusText}</span></td>
                <td><button class="btn btn-secondary btn-edit-worker" data-id="${worker.id}">Edytuj</button></td>
            </tr>
        `;
    });

    tableHTML += `
            </tbody>
        </table>
    `;

    return tableHTML;
}

// ==========================================
// Event handlers dla index.html (Login Page)
// ==========================================
$(document).ready(function() {
    
    // Sprawdzamy, czy jesteśmy na stronie logowania
    if ($('#loginForm').length) {
        $('#loginForm').on('submit', function(e) {
            e.preventDefault();
            
            const credentials = {
                login: $('#login').val(),
                password: $('#password').val()
            };

            // Walidacja podstawowa
            if (!credentials.login || !credentials.password) {
                $('#errorMessage').text('Proszę wypełnić wszystkie pola').addClass('show');
                return;
            }

            // Ukryj poprzednie błędy
            $('#errorMessage').removeClass('show');

            // ID AKCJI: 1 - Wykonanie logowania
            loginUser(credentials)
                .done(function(response) {
                    // Zapisanie danych w localStorage
                    localStorage.setItem('authToken', response.access_token);
                    localStorage.setItem('adminEmail', credentials.login);
                    localStorage.setItem('adminName', response.admin_name);
                    
                    // Przekierowanie do dashboard
                    window.location.href = 'dashboard.html';
                })
                .fail(function(xhr) {
                    if (xhr.status === 401) {
                        $('#errorMessage').text('Nieprawidłowy login lub hasło').addClass('show');
                    } else {
                        $('#errorMessage').text('Błąd połączenia. Spróbuj ponownie.').addClass('show');
                    }
                });
        });
    }

    // ==========================================
    // Event handlers dla dashboard.html (Panel zarządzania)
    // ==========================================
    if ($('#adminName').length) {
        
        // Sprawdź czy użytkownik jest zalogowany
        const authToken = localStorage.getItem('authToken');
        if (!authToken) {
            window.location.href = 'index.html';
            return;
        }

        const adminEmail = localStorage.getItem('adminEmail');
        const adminName = localStorage.getItem('adminName');

        // ID AKCJI: 2 - Pobierz i wyświetl nazwę admina
        if (adminName) {
            // Jeśli mamy imię z localStorage (z logowania)
            $('#adminName').text(adminName);
        } else if (adminEmail) {
            // Jeśli nie ma w localStorage, pobierz z API
            getCurrentAdmin(adminEmail)
                .done(function(adminData) {
                    $('#adminName').text(adminData.first_name);
                    localStorage.setItem('adminName', adminData.first_name);
                })
                .fail(function() {
                    $('#adminName').text('Admin');
                });
        }

        // ID AKCJI: 3 - Pobierz i wyświetl tabelę pracowników
        getWorkersTable()
            .done(function(workers) {
                const tableHTML = generateWorkersTableHTML(workers);
                $('#workersTableContainer').html(tableHTML);

                // Dodaj event listener do przycisków edycji
                $('.btn-edit-worker').on('click', function() {
                    const employeeId = $(this).data('id');
                    window.location.href = `edit.html?id=${employeeId}`;
                });
            })
            .fail(function(xhr) {
                $('#workersTableContainer').html('<p class="loading">Błąd wczytywania danych pracowników.</p>');
                console.error('Błąd pobierania pracowników:', xhr);
            });

        // ID AKCJI: 4 - Przycisk "Edytuj"
        $('#editBtn').on('click', function() {
            // W prawdziwej aplikacji przekierowanie do strony edycji
            alert('Przekierowanie do strony edycji pracowników\n\nW pełnej wersji: window.location.href = "edit.html"');
            // window.location.href = 'edit.html';
        });

        // ID AKCJI: 5 - Przycisk "Raporty"
        $('#reportsBtn').on('click', function() {
            // W prawdziwej aplikacji przekierowanie do strony raportów
            alert('Przekierowanie do strony raportów\n\nW pełnej wersji: window.location.href = "reports.html"');
            // window.location.href = 'reports.html';
        });

        // Przycisk wylogowania
        $('#logoutBtn').on('click', function() {
            localStorage.removeItem('authToken');
            localStorage.removeItem('adminEmail');
            localStorage.removeItem('adminName');
            window.location.href = 'index.html';
        });
    }
});

// ==========================================
// Przykład użycia funkcji raportów (dla przyszłej strony reports.html)
// ==========================================
/*
function loadReports() {
    const reportData = {
        date_from: '2024-01-01T00:00:00',
        date_to: '2024-12-31T23:59:59',
        employee_id: null // null = wszyscy pracownicy
    };

    generateReport(reportData)
        .done(function(reports) {
            console.log('Otrzymane raporty:', reports);
            // Tutaj wygeneruj tabelę z raportami
        })
        .fail(function(xhr) {
            console.error('Błąd generowania raportu:', xhr);
        });
}
*/
>>>>>>> Stashed changes
