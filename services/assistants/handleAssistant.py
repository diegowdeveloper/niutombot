from ..whatsAppService import WhatsAppService
from fastapi import Response
from typing import Optional, List, Dict, Any
from ..geminiService import GeminiService
from ..langChainService import LangChainGemini
from ..azureNiutomCompendium import AzureNiutomCompendium
from ..tavilySearch import TavilySearch
from db import SessionDep
from sqlmodel import select
from models import Profesor

class HandleAssistant:
    async def handleAssistantMessageSearchFonts(self, session, to, sender_data, user_pointer, message_body):
        user = user_pointer.getUserByWaID(session, sender_data)

        try:
            response = await TavilySearch.queryChat(message_body, user, session)
            await WhatsAppService.sendWhatsappMessage(to, response)
        except Exception as e:
            print(e)


    async def handleAssistantMessageNiutomDefault(self, to, sender_data, user_pointer, session, message_body):
        user = user_pointer.getUserByWaID(session, sender_data)

        try:
            response = await GeminiService.queryChatSimpleDefault(message_body, user, session)
            await WhatsAppService.sendWhatsappMessage(to, response)
        except Exception as e:
            print(e)


    async def handleAssistantMessageNiutomBasico(self, to, sender_data, user_pointer, session, message_body):
        user = user_pointer.getUserByWaID(session, sender_data)

        try:
            response = await GeminiService.queryChat(message_body, user, session)
            await WhatsAppService.sendWhatsappMessage(to, response)
        except Exception as e:
            print(e)


    async def handleAssistantMessageNiutomPro(self, to, sender_data, user_pointer, session, message_body):
            user = user_pointer.getUserByWaID(session, sender_data)

            try:
                response = await LangChainGemini.queryChat(message_body, user, session)
                await WhatsAppService.sendWhatsappMessage(to, response)
            except Exception as e:
                await WhatsAppService.sendWhatsappMessage(to, f"He tenido un inconveniente para procesar la petición. \n\n _código de error: {e}_")


    async def handleAssistantMessageNiutomCompendium(self, to, sender_data, user_pointer, session, message_body):
        user = user_pointer.getUserByWaID(session, sender_data)

        try:
            response = await AzureNiutomCompendium.queryChat(message_body, user, session)
            await WhatsAppService.sendWhatsappMessage(to, response)
        except Exception as e:
            print(e)