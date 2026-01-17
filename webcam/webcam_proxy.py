import cv2
import numpy as np
import time
import requests
import threading
from flask import Flask, Response
from flask_cors import CORS

app = Flask(__name__)
# Pozwalamy na dostęp z dowolnego źródła dla wygody deweloperskiej
CORS(app, resources={r"/*": {"origins": "*"}})

# --- KONFIGURACJA ---
CAMERA_INDEX = 0 
API_URL = "http://localhost:8000/identify/qr" # Adres Twojego głównego backendu
SCAN_COOLDOWN = 5.0  # Ile sekund czekać po udanym skanie przed kolejnym

cap = None
detector = cv2.QRCodeDetector()
last_scan_time = 0  # Znacznik czasu ostatniego wysłania

def get_camera():
    global cap
    if cap is None or not cap.isOpened():
        print(f"Otwieranie kamery {CAMERA_INDEX}...")
        cap = cv2.VideoCapture(CAMERA_INDEX)
    return cap

def send_qr_to_backend(qr_text, image_bytes):
    """Wysyła kod i zdjęcie do głównego API w tle."""
    try:
        print(f"--- [WYSYŁANIE] Wysyłam kod '{qr_text}' do {API_URL} ...")
        
        # Przygotowanie danych (zgodnie z tym, co ustawiliśmy w identification.py)
        # 'file' to zdjęcie twarzy, 'qr_code' to tekst kodu
        files = {'file': ('scan.jpg', image_bytes, 'image/jpeg')}
        data = {'qr_code': qr_text}

        response = requests.post(API_URL, files=files, data=data)
        
        if response.status_code == 200:
            worker = response.json()
            print(f"✅ [SUKCES] Zalogowano pracownika: {worker.get('first_name')} {worker.get('last_name')}")
        elif response.status_code == 403:
            detail = response.json().get('detail', 'Brak szczegółów')
            print(f"⛔ [ODMOWA] Backend odrzucił: {detail}")
        else:
            print(f"⚠️ [BŁĄD API] Status: {response.status_code}, Treść: {response.text}")

    except Exception as e:
        print(f"❌ [BŁĄD POŁĄCZENIA] Nie udało się połączyć z API: {e}")

def gen_frames():
    global last_scan_time
    print("Start strumienia wideo z automatycznym skanowaniem...")
    
    while True:
        camera = get_camera()
        if not camera.isOpened():
            time.sleep(2)
            continue

        ok, frame = camera.read()
        if not ok:
            print("Błąd odczytu klatki.")
            if camera: camera.release()
            time.sleep(1)
            continue

        # --- DETEKCJA QR ---
        try:
            text, points, _ = detector.detectAndDecode(frame)
            
            if points is not None:
                # 1. Rysowanie (wizualizacja)
                points = points.astype(np.int32)
                cv2.polylines(frame, [points], isClosed=True, color=(0, 255, 0), thickness=4)
                
                if text:
                    # Wizualizacja tekstu na ekranie
                    msg = f"QR: {text}"
                    cv2.putText(frame, msg, (points[0][0][0], points[0][0][1] - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

                    # 2. LOGIKA AUTOMATYCZNEJ WYSYŁKI
                    current_time = time.time()
                    
                    # Sprawdzamy czy minął czas od ostatniego skanu (COOLDOWN)
                    if (current_time - last_scan_time) > SCAN_COOLDOWN:
                        print(f"\n📸 [DETEKCJA] Wykryto kod: {text}. Robię zdjęcie twarzy...")
                        
                        # Kodujemy AKTUALNĄ klatkę (z twarzą) do JPG
                        success, jpg_encoded = cv2.imencode(".jpg", frame)
                        
                        if success:
                            # Uruchamiamy wysyłanie w OSOBNYM wątku
                            # Dzięki temu wideo nie zatnie się podczas czekania na odpowiedź serwera
                            threading.Thread(
                                target=send_qr_to_backend, 
                                args=(text, jpg_encoded.tobytes())
                            ).start()
                            
                            last_scan_time = current_time
                        else:
                            print("Błąd kodowania obrazu do wysyłki.")
                    
        except Exception as e:
            # Ignorujemy błędy detekcji, żeby nie przerywać wideo
            pass

        # --- STRUMIENIOWANIE DO PRZEGLĄDARKI ---
        try:
            ok, jpg = cv2.imencode(".jpg", frame)
            if ok:
                yield (b"--frame\r\n"
                       b"Content-Type: image/jpeg\r\n\r\n" + jpg.tobytes() + b"\r\n")
        except Exception:
            pass

@app.get("/video")
def video():
    return Response(gen_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")

@app.get("/snapshot")
def snapshot():
    """Zwraca po prostu bieżącą klatkę jako zdjęcie (dla celów debugowania)"""
    camera = get_camera()
    ok, frame = camera.read()
    if not ok: return ("No frame", 500)
    _, buf = cv2.imencode(".jpg", frame)
    return Response(buf.tobytes(), mimetype="image/jpeg")

if __name__ == "__main__":
    # Uruchamiamy na porcie 8090
    app.run(host="127.0.0.1", port=8090, threaded=True)