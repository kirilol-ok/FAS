from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.routers import identification

app = FastAPI(title="Camera Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(identification.router)

app.mount("/static", StaticFiles(directory="frontend/src"), name="static")

@app.get("/", include_in_schema=False)
def camera_page():
    return FileResponse("frontend/src/camera.html")
