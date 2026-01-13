import cv2
from flask import Flask, Response

app = Flask(__name__)

# 0 = первая камера. CAP_DSHOW обычно стабильнее на Windows
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

def gen_frames():
    while True:
        ok, frame = cap.read()
        if not ok:
            continue

        ok, jpg = cv2.imencode(".jpg", frame)
        if not ok:
            continue

        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + jpg.tobytes() + b"\r\n")

@app.get("/")
def index():
    # простая HTML-страница с <img>, который тянет /video
    return """
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8" />
        <title>Webcam preview</title>
        <style>
          body { font-family: Arial; padding: 20px; }
          img { max-width: 100%; height: auto; border-radius: 12px; }
          .hint { color: #666; margin-top: 10px; }
        </style>
      </head>
      <body>
        <h2>Webcam preview</h2>
        <img src="/video" />
        <div class="hint">If you see video — camera works. Endpoint: <code>/video</code></div>
      </body>
    </html>
    """

@app.get("/video")
def video():
    return Response(gen_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")

@app.get("/health")
def health():
    return {"ok": True, "camera_opened": bool(cap.isOpened())}

if __name__ == "__main__":
    # host=127.0.0.1 достаточно для браузера на Windows-хосте
    app.run(host="127.0.0.1", port=8090, threaded=True)
