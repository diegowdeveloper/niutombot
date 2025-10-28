from fastapi import FastAPI, Request, Response
from .routers import webhook
from .db import SessionDep, create_all_tables


app = FastAPI(
    title       ="Asistente virtual inteligente Niutom",
    description ="Agente Inteligente entrenado para asistir a los docentes",
    lifespan    = create_all_tables
)
app.include_router(webhook.router)

@app.get("/")
async def root():
    return Response(content="Bienvenido a Niutom, un asistente virtual que te ayudará a gestionar tu trabajo como docente", media_type="text/plain")
    
