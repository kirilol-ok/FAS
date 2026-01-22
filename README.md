# Uruchominie Docker'a

## Szybki start 

Aby uruchomić całe środowisko wraz ze wszystkimi usługami, wykonaj poniższe kroki:

### 1. Wymagania wstępne
* Zainstalowany **Docker Desktop**.

### 2. Uruchomienie kontenerów
Otwórz terminal w głównym folderze projektu i wykonaj komendę:

```bash
docker-compose up --build

````

## 🛠️ Przydatne komendy Docker

Poniżej znajduje się lista najczęściej używanych komend do zarządzania środowiskiem projektu:

| Akcja | Komenda | Opis |
| :--- | :--- | :--- |
| **Zatrzymanie projektu** | `docker-compose down` | Zatrzymuje i usuwa kontenery oraz sieci utworzone przez `up`. |
| **Szybkie zatrzymanie** | `Ctrl + C` | Zatrzymuje procesy w bieżącym oknie terminala. |
| **Restart usługi** | `docker-compose restart <nazwa_usługi>` | Ponownie uruchamia konkretny kontener (np. `frontend_dev`). |
| **Podgląd logów** | `docker-compose logs -f` | Wyświetla strumień logów ze wszystkich kontenerów w czasie rzeczywistym. |
| **Logi jednej usługi** | `docker-compose logs -f <nazwa_usługi>` | Śledzi logi tylko wybranego komponentu. |
| **Czyszczenie wolumenów** | `docker-compose down -v` | Zatrzymuje kontenery i czyści dane (np. resetuje bazę danych). |

---

### Jak sprawdzić nazwy usług?
Jeśli nie pamiętasz dokładnej nazwy usługi do restartu, wpisz:
```bash
docker-compose ps
````
---

# Instrukcja uruchomienia modułu kamery 

## 1. Wymagania wstępne

* Upewnij się, że kontenery Docker są uruchomione.
* Posiadasz zainstalowanego Pythona.

---

## 2. Przygotowanie środowiska (wykonywane raz)

Otwórz terminal w głównym folderze projektu i wykonaj poniższe komendy:

1.  **Wejdź do folderu modułu:**
    ```bash
    cd webcam
    ```
2.  **Utwórz wirtualne środowisko:**
    ```bash
    python -m venv .venv
    ```
3.  **Aktywuj środowisko:**
    * **Windows:** `.venv\Scripts\activate`
    * **Linux/macOS:** `source .venv/bin/activate`
4.  **Zainstaluj biblioteki:**
    ```bash
    python -m pip install -r requirements.txt
    ```
    *Uwaga: Jeśli wystąpi błąd `ModuleNotFoundError: No module named 'requests'`, zainstaluj go ręcznie:*
    `python -m pip install requests opencv-python`

---

## 3. Uruchomienie strumienia

Aby "ożywić" czarny ekran na stronie **Live Stream**, uruchom skrypt proxy:

```bash
python webcam_proxy.py
```


