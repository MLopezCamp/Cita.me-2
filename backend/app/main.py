from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, pacientes, medicos, horarios, citas
from app.models.database import init_db

app = FastAPI(title="Cita Médica Distribuida", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(pacientes.router)
app.include_router(medicos.router)
app.include_router(horarios.router)
app.include_router(citas.router)

@app.on_event("startup")
def startup():
    init_db()

@app.get("/")
def root():
    return {"message": "API de Citas Médicas Distribuidas funcionando"}