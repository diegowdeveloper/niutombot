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

class HandleAssistantMedia:

    async def getBytes(self, media_id):
        download_url = await WhatsAppService.downloadMedia(media_id)
        audio_bytes  = await WhatsAppService.getBytesOfFile(download_url)
        return audio_bytes


    async def handleMessageAudio(self, session, user_pointer, sender_data, to, transcription, chatmode):
        user = user_pointer.getUserByWaID(session, sender_data)

        try:
            response = "Elije un modo primero" 

            if chatmode == "niutom_basico":
                response = await GeminiService.queryChat(transcription, user, session)
            elif chatmode == "niutom_pro":
                response = await LangChainGemini.queryChat(transcription, user, session)
            elif chatmode == "niutom_resumen":
                response = await AzureNiutomCompendium.queryChat(transcription, user, session)
            elif chatmode == "tavily_mode":
                response = await TavilySearch.queryChat(transcription, user, session)

            await WhatsAppService.sendWhatsappMessage(to, response)

        except Exception as e:
            await WhatsAppService.sendWhatsappMessage(to, f"He tenido un inconveniente al procesar el audio \n\n _Error:_ _{e}_")


    async def handleMessageImage(self, session, user_pointer, sender_data, to, image_bytes, mime_type, caption, chatmode):
        user = user_pointer.getUserByWaID(session, sender_data)

        try:
            response = await GeminiService.queryChatMedia(image_bytes, mime_type, user, session, caption)
            await WhatsAppService.sendWhatsappMessage(to, response)
        except Exception as e:
            print(e)

        # try:
        #     response = "Elije un modo primero" 

        #     if chatmode == "niutom_basico":
        #         response = await GeminiService.queryChat(transcription, user, session)
        #     elif chatmode == "niutom_pro":
        #         response = await LangChainGemini.queryChat(transcription, user, session)
        #     elif chatmode == "niutom_resumen":
        #         response = await AzureNiutomCompendium.queryChat(transcription, user, session)
        #     elif chatmode == "tavily_mode":
        #         response = await TavilySearch.queryChat(transcription, user, session)

        #     await WhatsAppService.sendWhatsappMessage(to, response)

        # except Exception as e:
        #     await WhatsAppService.sendWhatsappMessage(to, f"He tenido un inconveniente al procesar el audio \n\n _Error:_ _{e}_")