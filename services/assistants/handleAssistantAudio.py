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


class HandleAssistantAudio:
    async def getAudioBytes(self, audio_id):
        download_url = await WhatsAppService.downloadMedia(audio_id)
        audio_bytes  = await WhatsAppService.getBytesOfFile(download_url)
        return audio_bytes


    async def handleMessageAudio(self, session, user_pointer, sender_data, to, transcription, chatmode):
        user = user_pointer.getUserByWaID(session, sender_data)

        try:
            response = "Elije un modo primero" 

            if chatmode == "niutom_basico":
                response = await GeminiService.queryChatSimple(transcription, user, session)
            elif chatmode == "niutom_pro":
                response = await LangChainGemini.queryChatSimple(transcription, user, session)
            elif chatmode == "niutom_resumen":
                response = await AzureNiutomCompendium.queryCompendium(transcription, user, session)
            elif chatmode == "tavily_mode":
                response = await TavilySearch.queryChatSimple(transcription, user, session)

            await WhatsAppService.sendWhatsappMessage(to, response)

        except Exception as e:
            await WhatsAppService.sendWhatsappMessage(to, f"He tenido un inconveniente al procesar el audio \n\n _Error:_ _{e}_")