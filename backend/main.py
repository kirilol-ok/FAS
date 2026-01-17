from fastapi import FastAPI

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from backend.routers import admin, identification
from backend.databases.db import init_all_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_all_db()
    
    yield
    

app = FastAPI(title="User Identification System", lifespan=lifespan)

origins = [
    "http://localhost:3000",      # Python http.server
    "http://127.0.0.1:3000",
    "http://localhost:3001",      # добавляем порт 3001
    "http://127.0.0.1:3001",
    "http://localhost:5500",      # VS Code Live Server
    "http://127.0.0.1:5500",
    "http://localhost:8000",      # 
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,     # 
    allow_credentials=True,
    allow_methods=["*"],       # 
    allow_headers=["*"],       # 
)

app.include_router(admin.router)
app.include_router(identification.router)

@app.get("/")
def read_root():
    return {"message": "System backend is running"}