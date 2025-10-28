from whatsAppService import WhatsAppService
from fastapi import Response
from typing import Optional, List, Dict, Any
from geminiService import GeminiService
from langChainService import LangChainGemini
from azureNiutomCompendium import AzureNiutomCompendium
from tavilySearch import TavilySearch
from db import SessionDep
from sqlmodel import select
from models import Profesor

class MessageHandler:

    def __init__(self, message, sender_info, session):
        self.message                     = message                   
        self.sender_info                 = sender_info
        self.message_from: str           = message.get("from")
        self.message_id                  = message.get("id")
        self.message_type: str           = message.get("type")
        self.message_body: Optional[str] = message.get("text", {}).get("body", {})
        self.session                     = session


    @classmethod
    async def handleIncomingMessage(cls, message, sender_info, session):

        handle = cls(message, sender_info, session)
        await WhatsAppService.markMessageAsRead(handle.message_id)

        sender_data  = handle.getSenderData()
        chatmode     = handle.getChatMode(sender_data)
        _user_exists = handle.searchUser(sender_data)

        if not _user_exists:
            handle.create_user(sender_data["name"], sender_data["wa_id"])

        if message and handle.message_type == "text":

            if chatmode == "niutom_basico": 
                await handle.sendProcessingMessage()
                await handle.handleAssistantMessageNiutomBasico()
                await handle.sendChatMenu()
            elif chatmode == 'niutom_pro':
                await handle.sendProcessingMessage()
                await handle.handleAssistantMessageNiutomPro()
                await handle.sendChatMenuPro()
            elif chatmode == 'tavily_mode': 
                await handle.sendProcessingMessage()
                await handle.handleAssistantMessageSearchFonts()
                await handle.sendChatMenuPro()
            elif chatmode == 'niutom_resumen':
                await handle.sendProcessingMessage()
                await handle.handleAssistantMessageNiutomCompendium()
                await handle.sendChatMenu()
            elif "hola" in handle.message_body.lower().strip() and len(handle.message_body.lower().strip()) <= 12:
                await handle.sendWelcomeMessage()
                await handle.sendWelcomeMenu()
            else:
                await handle.handleAssistantMessageNiutomDefault()
                await handle.sendWelcomeMenu()

        elif handle.message_type == "interactive":

            option_id = message.get("interactive", {}).get("button_reply", {}).get("id")
            await handle.handleMenuOption(option_id)

        elif handle.message_type == "audio":

            await handle.sendListeningMessage()
            download_content = await WhatsAppService.downloadMedia(handle.message.get("audio", {}).get("id"))
            temp_file_path   = await GeminiService.processAudioMessage(download_content)
            await handle.handleMessageAudio(temp_file_path)
            await handle.sendChatMenu()

        return Response(content = "Mensaje enviado", status_code=200)
    

    def getSenderName(self) -> bool:
        return self.sender_info.get("profile", {})["name"].split(" ")[0] or self.sender_info.get("wa_id") or ""
    

    def getSenderData(self) -> dict:
        return {
            "name": self.sender_info.get("profile", {})["name"].split(" ")[0] or None,
            "wa_id": self.sender_info.get("wa_id") or None
        }
    

    def getChatMode(self, sender_data):
        mode = self.session.exec(select(Profesor.mode).where(Profesor.wa_id == sender_data["wa_id"])).first()
        return mode

    
    def searchUser(self, sender_data) -> bool:

        try:
            
            user = self.session.exec(select(Profesor).where(Profesor.wa_id == sender_data["wa_id"])).first()

            if user:
                return True
            return False
        
        except Exception as e:

            print(f"Ha ocurrido un error al buscar al usuario: \n\n {e}")


    def getUserByWaID(self):
        result = select(Profesor).where(Profesor.wa_id == self.getSenderData()["wa_id"])
        return self.session.exec(result).first()


    def create_user(self, name, wa_id):
        try: 
            new_user = Profesor(name = name, wa_id = wa_id)
            self.session.add(new_user)
            self.session.commit()
            self.session.refresh(new_user)
        except Exception as e:
            print(e)


    def updateUser(self, user, option_id):
        user.mode       = option_id
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)


    async def sendProcessingMessage(self):
        await WhatsAppService.sendWhatsappMessage(self.message_from, "Procesando 🧠", self.message_id)


    async def sendListeningMessage(self):
        await WhatsAppService.sendWhatsappMessage(self.message_from, "Escuchando 👂🏽", self.message_id)


    async def sendWelcomeMessage(self):
        name_user = self.getSenderName()
        message = f"*¡Hola {name_user}!* Un gusto en saludar, ¿Qué te gustaría hacer?"
        await WhatsAppService.sendWhatsappMessage(self.message_from, message)


    async def sendChatMenu(self):
        menu_message = "¿Quieres cambiar de modo?"
        buttons = [
            {
                "type": "reply",
                "reply": {
                    "id": "cambiar_modelo",
                    "title": "Cambiar Modelo"
                }
            }
        ]
        await WhatsAppService.sendInteractiveButtons(self.message_from, menu_message, buttons)


    async def sendChatMenuPro(self):
        menu_message = "¿Quieres cambiar de modo?"
        buttons = [
            {
                "type": "reply",
                "reply": {
                    "id": "tavily_mode",
                    "title": "Buscar fuentes"
                }
            },
            {
                "type": "reply",
                "reply": {
                    "id": "niutom_pro",
                    "title": "Terminar búsqueda"
                }
            },
            {
                "type": "reply",
                "reply": {
                    "id": "cambiar_modelo",
                    "title": "Cambiar Modelo"
                }
            }
        ]
        await WhatsAppService.sendInteractiveButtons(self.message_from, menu_message, buttons)


    async def sendWelcomeMenu(self):

        menu_message = f"Por favor elije un modelo para conversar conmigo:"
        buttons = [
            {
                "type": "reply",
                "reply": {
                    "id": "niutom_basico",
                    "title": "Niutom Básico 🐣"
                }
            },
            {
                "type": "reply",
                "reply": {
                    "id": "niutom_pro",
                    "title": "Niutom Pro 🐥"
                }
            },
            {
                "type": "reply",
                "reply": {
                    "id": "niutom_resumen",
                    "title": "Niutom Compendium 📚"
                }
            }
        ]
        
        await WhatsAppService.sendInteractiveButtons(self.message_from, menu_message, buttons)


    async def handleMenuOption(self, option_id):

        user            = self.getUserByWaID()
        message_reply   = "Disculpa, no he entendido tu respuesta"
        self.updateUser(user, option_id)

        if option_id == 'cambiar_modelo':
            message_reply   = f"Elije otro modelo"
            await self.sendWelcomeMenu()     
        elif option_id == 'niutom_basico':
            message_reply = await GeminiService.queryChatSimple("Hola", user, self.session)
        elif option_id == 'niutom_pro': 
            message_reply = "Ahora has cambiado al modo Niutom Pro, puedo ayudarte de manera más eficiente"
        elif option_id == 'niutom_resumen':
            message_reply = (
                                "¿Qué te gustaría resumir? Tengo gran parte del repertorio de temas dados hasta el primer Lapso.\n\n"
                                "Debes preguntar algo y con base a mis conocimientos cargados te daré respuesta"
                             )
        elif option_id == "tavily_mode":
            message_reply = "¿Qué te gustaría buscar?"


        await WhatsAppService.sendWhatsappMessage(self.message_from, message_reply)

        if user.new_user:
            user.new_user = False 
            self.session.add(user)
            self.session.commit()
            self.session.refresh(user)

            message_info = "Niutom Básico es mi modo más simple para poder entender tus requerimientos"

            if option_id == "niutom_pro":
                message_info = "Niutom Pro es un modo más avanzado que me permite dar respuestas más acertadas a lo que necesitas"
            elif option_id == "niutom_resumen":
                message_info = "Niutom Compendium es un modo entrenado con gran parte del repertorio de temas de la escuela, pudes preguntar lo que quieras de los temarios en el U.E.I.S.A y buscaré en mis registros"

            await WhatsAppService.sendWhatsappMessage(self.message_from, message_info)


    async def handleAssistantMessageNiutomDefault(self):
        user = self.getUserByWaID()

        try:
            response = await GeminiService.queryChatSimpleDefault(self.message_body, user, self.session)
            await WhatsAppService.sendWhatsappMessage(self.message_from, response)
        except Exception as e:
            print(e)

    
    async def handleAssistantMessageNiutomBasico(self):
        user = self.getUserByWaID()

        try:
            response = await GeminiService.queryChatSimple(self.message_body, user, self.session)
            await WhatsAppService.sendWhatsappMessage(self.message_from, response)
        except Exception as e:
            print(e)

    
    async def handleAssistantMessageNiutomPro(self):
        user = self.getUserByWaID()

        try:
            response = await LangChainGemini.queryChatSimple(self.message_body, user, self.session)
            await WhatsAppService.sendWhatsappMessage(self.message_from, response)
        except Exception as e:
            print(e)


    async def handleAssistantMessageSearchFonts(self):
        user = self.getUserByWaID()

        try:
            response = await TavilySearch.queryChatSimple(self.message_body, user, self.session)
            await WhatsAppService.sendWhatsappMessage(self.message_from, response)
        except Exception as e:
            print(e)


    async def handleAssistantMessageNiutomCompendium(self):
        user = self.getUserByWaID()

        try:
            response = await AzureNiutomCompendium.queryCompendium(self.message_body, user, self.session)
            await WhatsAppService.sendWhatsappMessage(self.message_from, response)
        except Exception as e:
            print(e)

    async def handleMessageAudio(self, temp_file_path):
        user = self.getUserByWaID()

        try:
            response = await GeminiService.queryChatAudio(temp_file_path, user, self.session)
            await WhatsAppService.sendWhatsappMessage(self.message_from, response)
        except Exception as e:
            print(e)
    

