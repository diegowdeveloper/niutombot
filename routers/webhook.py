from fastapi import APIRouter, Request, Response
from dotenv import load_dotenv
from ..models import Profesor
from ..models import Pensamiento
from ..db import SessionDep
import os

from ..services import MessageHandler

router = APIRouter()
load_dotenv()

@router.get("/webhook")
async def verify_webhook(req: Request):

    mode        = req.query_params.get("hub.mode")
    token       = req.query_params.get("hub.verify_token")
    challenge   = req.query_params.get("hub.challenge")

    if mode == "subscribe" and token == os.getenv("WEBHOOK_VERIFY_TOKEN"):

        return Response(content = challenge, status_code=200, media_type="text/plain")
    
    else:

        return Response(content = "Ha ocurrido un error al verificar el token de seguridad con la WhatsApp API", status_code=403)
    

@router.post("/webhook")
async def receive_webhook(req: Request, session: SessionDep):
    try:
        
        payload     = await req.json()
        message     = payload.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("messages", [{}])[0]
        sender_info = payload.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("contacts", [{}])[0]

        if message:
            await MessageHandler.handleIncomingMessage(message, sender_info, session)
            

    except Exception as e:

        return Response(content = f"Ha ocurrido un error: {e}", status_code=500)
