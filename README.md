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
