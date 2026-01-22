import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.databases.db import init_all_db
from backend.routers import admin, identification
from backend.routers.identification import face_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_all_db()
    face_service.preload_model()
    yield


app = FastAPI(title="User Identification System", lifespan=lifespan)

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin.router)
app.include_router(identification.router)


@app.get("/")
def read_root():
    return {"message": "System backend is running"}


async def background_expiration_checker():
    while True:
        print("🕒 [SCHEDULER] Checking for expired accounts...")
        try:
            async with async_session_maker() as db:
                today = date.today()
                stmt = select(Employees).where(
                    Employees.dismissed == False,
                    Employees.expiration_date != None,
                    Employees.expiration_date < today,
                )
                result = await db.execute(stmt)
                expired_employees = result.scalars().all()

                if expired_employees:
                    for emp in expired_employees:
                        emp.dismissed = True
                        emp.dismissal_date = today
                        emp.qr_value = None
                        print(f"⚠️ [SCHEDULER] Auto-dismiss: {emp.email}")

                    await db.commit()
                else:
                    print("✅ [SCHEDULER] No expired accounts found.")

        except Exception as e:
            print(f"❌ [SCHEDULER ERROR] {e}")

        await asyncio.sleep(86400)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(background_expiration_checker())
