from .whatsAppService import WhatsAppService
from fastapi import Response
from typing import Optional, List, Dict, Any
from .geminiService import GeminiService
from .langChainService import LangChainGemini
from .azureNiutomCompendium import AzureNiutomCompendium
from .tavilySearch import TavilySearch
from db import SessionDep
from sqlmodel import select
from models import Profesor

from abc import ABC

# Recibe datos del message
class UserHandler:
    def getSenderData(self, sender_info) -> dict:
        sender_data = {
            "name" : sender_info.get("profile", {})["name"].split(" ")[0] or None,
            "wa_id": sender_info.get("wa_id") or None
        }
        return sender_data
    

    def getSenderName(self, sender_info) -> bool:
        return sender_info.get("profile", {})["name"].split(" ")[0] or sender_info.get("wa_id") or ""
    

# Puntero que se integra con la tabla profesor
class UserPointer:

    def sessionAction(self, session, model):
        session.add(model)
        session.commit()
        session.refresh(model)


    def getChatMode(self, session, sender_data):
        mode = session.exec(select(Profesor.mode).where(Profesor.wa_id == sender_data["wa_id"])).first()
        return mode
    

    def create_user(self, session, name, wa_id):
        try: 
            new_user = Profesor(name=name, wa_id=wa_id)
            self.sessionAction(session, new_user)
        except Exception as e:
            print(e)


    def updateUser(self, session, user, option_id):
        user.mode = option_id
        self.sessionAction(session, user)
    

    def searchUser(self, session, sender_data) -> bool:
        try:
            user = session.exec(select(Profesor).where(Profesor.wa_id == sender_data["wa_id"])).first()

            if user:
                return 
            
            return False
        
        except Exception as e:
            print(f"Ha ocurrido un error al buscar al usuario: \n\n {e}")

    
    def getUserByWaID(self, session, sender_data):
        result = select(Profesor).where(Profesor.wa_id == sender_data["wa_id"])
        return session.exec(result).first()


class HandleAssistant:
    async def handleAssistantMessageSearchFonts(self, session, to, sender_data, user_pointer, message_body):
        user = user_pointer.getUserByWaID(session, sender_data)

        try:
            response = await TavilySearch.queryChatSimple(message_body, user, session)
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
            response = await GeminiService.queryChatSimple(message_body, user, session)
            await WhatsAppService.sendWhatsappMessage(to, response)
        except Exception as e:
            print(e)


    async def handleAssistantMessageNiutomPro(self, to, sender_data, user_pointer, session, message_body):
            user = user_pointer.getUserByWaID(session, sender_data)

            try:
                response = await LangChainGemini.queryChatSimple(message_body, user, session)
                await WhatsAppService.sendWhatsappMessage(to, response)
            except Exception as e:
                await WhatsAppService.sendWhatsappMessage(to, f"He tenido un inconveniente para procesar la petición. \n\n _código de error: {e}_")


    async def handleAssistantMessageNiutomCompendium(self, to, sender_data, user_pointer, session, message_body):
        user = user_pointer.getUserByWaID(session, sender_data)

        try:
            response = await AzureNiutomCompendium.queryCompendium(message_body, user, session)
            await WhatsAppService.sendWhatsappMessage(to, response)
        except Exception as e:
            print(e)


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

            await WhatsAppService.sendWhatsappMessage(to, response)

        except Exception as e:
            await WhatsAppService.sendWhatsappMessage(to, f"He tenido un inconveniente al procesar el audio \n\n _Error:_ _{e}_")


# Controlador del chat
class HandleMenu:
    async def handleMenuOption(self, session, user_pointer, sender_data, option_id, to):
        user            = user_pointer.getUserByWaID(session, sender_data)
        message_reply   = "Disculpa, no he entendido tu respuesta"

        if option_id == 'cambiar_modelo':
            message_reply   = f"Volvamos al comienzo"
            await self.sendWelcomeListMenu(to)     
        elif option_id == 'niutom_basico':
            user_pointer.updateUser(session, user, option_id)
            message_reply = await GeminiService.queryChatSimple("¡Hola Niutom! ☺", user, session)
        elif option_id == 'niutom_pro': 
            user_pointer.updateUser(session, user, option_id)
            message_reply = "Ahora has cambiado al modo Niutom Pro, puedo ayudarte de manera más eficiente"
        elif option_id == 'niutom_resumen':
            user_pointer.updateUser(session, user, option_id)
            message_reply = (
                                "¿Qué te gustaría resumir? Tengo gran parte del repertorio de temas dados hasta el primer Lapso.\n\n"
                                "Debes preguntar algo y con base a mis conocimientos cargados te daré respuesta"
                             )
        elif option_id == "tavily_mode":
            user_pointer.updateUser(session, user, option_id)
            message_reply = "¿Qué te gustaría buscar?"
        elif option_id == "que_es":
            message_reply = "https://trescomasagency.com/niutom/\n Aquí tienes...\n ¿Qué es Niutom? 🤷\n"
        elif option_id == "uso":
            message_reply = "https://trescomasagency.com/niutom/#uso\n Aquí tienes...\n ¿Cómo usarlo? 📖"
        elif option_id == "funcion":
            message_reply = "https://trescomasagency.com/niutom/#funcion\n Aquí tienes...\n ¿Cuál es la función de Niutom? ⚙️"
        elif option_id == "historia":
            message_reply = "https://trescomasagency.com/niutom/#historia\n Aquí tienes...\n Orígenes de Niutom 🗂"

        await WhatsAppService.sendWhatsappMessageURL(to, message_reply)

        if user.new_user:
            user.new_user = False 
            session.add(user)
            session.commit()
            session.refresh(user)

            message_info = "Niutom Básico es mi modo más simple para poder entender tus requerimientos"

            if option_id == "niutom_pro":
                message_info = "Niutom Pro es un modo más avanzado que me permite dar respuestas más acertadas a lo que necesitas"
            elif option_id == "niutom_resumen":
                message_info = "Niutom Compendium es un modo entrenado con gran parte del repertorio de temas de la escuela, puedes preguntar lo que quieras de los temarios en el U.E.I.S.A y buscaré en mis registros"

            await WhatsAppService.sendWhatsappMessage(to, message_info)


    async def sendWelcomeListMenu(self, message_from):
        list_menu_message = f"Elije una opción 👇🏽"
        sections          = [
            {
                "title": "Modelos",
                "rows": [
                    {
                        "id": "niutom_basico",
                        "title": "Niutom básico 🐣",
                        "description": "Ligero"
                    }, {
                        "id": "niutom_pro",
                        "title": "Niutom Pro 🐥",
                        "description": "Me pongo las 'pilas'" 
                    }, {
                        "id": "niutom_resumen",
                        "title": "Niutom Compendium 📚",
                        "description": "Soy un erudito"
                    }
                ]
            }, {
                "title": "Manual de uso",
                "rows": [
                    {
                        "id": "que_es",
                        "title": "¿Qué es? 🤷",
                        "description": "Definición del asistente"
                    },
                    {
                        "id": "uso",
                        "title": "¿Cómo usarlo? 📖",
                        "description": "Descubre el uso que le puedes dar"
                    },
                    {
                        "id": "funcion",
                        "title": "Función de Niutom ⚙️",
                        "description": "Descubre cuál es la función de este bot"
                    },
                    {
                        "id": "historia",
                        "title": "Orígenes 🗂",
                        "description": "Un poco de historia"
                    }
                ]
            }
        ]

        await WhatsAppService.sendInteractiveList(message_from, list_menu_message, sections)


    async def sendChatMenu(self, message_from):
        menu_message = "¿Quieres cambiar de modo?"
        buttons = [
            {
                "type": "reply",
                "reply": {
                    "id": "cambiar_modelo",
                    "title": "Volver al inicio"
                }
            }
        ]
        await WhatsAppService.sendInteractiveButtons(message_from, menu_message, buttons)


    async def sendChatMenuPro(self, message_from):
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
        await WhatsAppService.sendInteractiveButtons(message_from, menu_message, buttons)


class SenderMessage:
    async def sendProcessingMessage(self, message_from, message_id):
        await WhatsAppService.sendWhatsappMessage(message_from, "Pensando🧠", message_id)


    async def sendListeningMessage(self, message_from, message_id):
        await WhatsAppService.sendWhatsappMessage(message_from, "Escuchando👂🏽", message_id)


    async def sendWelcomeMessage(self, message_from, sender_name):
        message = f"*¡Hola {sender_name}!* Un gusto en saludar, ¿Qué te gustaría hacer?"
        await WhatsAppService.sendWhatsappMessage(message_from, message)


# Clase principal
class MessageHandler:
    user_handler     = UserHandler()
    user_pointer     = UserPointer()
    handle_assistant = HandleAssistant()
    handle_menu      = HandleMenu()
    handle_audio     = HandleAssistantAudio()
    sender_message   = SenderMessage()

    def __init__(self, message, sender_info, session):
        self.session                     = session
        self.message                     = message                   
        self.sender_info                 = sender_info
        self.message_from: str           = message.get("from")
        self.message_id                  = message.get("id")
        self.message_type: str           = message.get("type")
        self.message_body: Optional[str] = message.get("text", {}).get("body", {})


    @classmethod
    async def handleIncomingMessage(cls, message, sender_info, session):

        handle = cls(message, sender_info, session)
        await WhatsAppService.markMessageAsRead(handle.message_id)

        sender_data  = cls.user_handler.getSenderData(sender_info)
        chatmode     = cls.user_pointer.getChatMode(session, sender_data)
        _user_exists = cls.user_pointer.searchUser(session, sender_data)

        if not _user_exists:
            cls.user_pointer.create_user(handle.session, sender_data["name"], sender_data["wa_id"])

        if message and handle.message_type == "text":
            if chatmode == "niutom_basico":
                await cls.sender_message.sendProcessingMessage(handle.message_from, handle.message_id)
                await cls.handle_assistant.handleAssistantMessageNiutomBasico(handle.message_from, sender_data, cls.user_pointer, handle.session, handle.message_body)
                await cls.handle_menu.sendChatMenu(handle.message_from)
            elif chatmode == 'niutom_pro':
                await cls.sender_message.sendProcessingMessage(handle.message_from, handle.message_id)
                await cls.handle_assistant.handleAssistantMessageNiutomPro(handle.message_from, sender_data, cls.user_pointer, handle.session, handle.message_body)
                await cls.handle_menu.sendChatMenuPro(handle.message_from)
            elif chatmode == 'tavily_mode': 
                await cls.sender_message.sendProcessingMessage(handle.message_from, handle.message_id)
                await cls.handle_assistant.handleAssistantMessageSearchFonts(handle.session, handle.message_from, sender_data, cls.user_pointer, handle.message_body)
                await cls.handle_menu.sendChatMenuPro(handle.message_from)
            elif chatmode == 'niutom_resumen':
                await cls.sender_message.sendProcessingMessage(handle.message_from, handle.message_id)
                await cls.handle_assistant.handleAssistantMessageNiutomCompendium(handle.message_from, sender_data, cls.user_pointer, handle.session, handle.message_body)
                await cls.handle_menu.sendChatMenu(handle.message_from)
            elif "hola" in handle.message_body.lower().strip() and len(handle.message_body.lower().strip()) <= 12:
                sender_name = cls.user_handler.getSenderName(handle.sender_info)
                await cls.sender_message.sendWelcomeMessage(handle.message_from, sender_name)
                await cls.handle_menu.sendWelcomeListMenu(handle.message_from)
            else:
                await cls.handle_assistant.handleAssistantMessageNiutomDefault(handle.message_from, sender_data, cls.user_pointer, handle.session, handle.message_body)
                await cls.handle_menu.sendWelcomeListMenu(handle.message_from)


        elif handle.message_type == "interactive":
            type_interactive = message.get("interactive", {}).get("type", "")
            option_id        = False

            if type_interactive == "button_reply":
                option_id = message.get("interactive", {}).get("button_reply", {}).get("id")
            elif type_interactive == "list_reply":
                option_id = message.get("interactive", {}).get("list_reply", {}).get("id")
            
            await cls.handle_menu.handleMenuOption(handle.session, cls.user_pointer, sender_data, option_id, handle.message_from)


        elif handle.message_type == "audio":

            await cls.sender_message.sendListeningMessage(handle.message_from, handle.message_id)

            audio_id         = handle.message.get("audio", {}).get("id")
            audio_bytes      = await cls.handle_audio.getAudioBytes(audio_id)
            transcription    = await GeminiService.processAudioMessage(audio_bytes)
            await cls.handle_audio.handleMessageAudio(handle.session, cls.user_pointer, sender_data, handle.message_from, transcription, chatmode)
            await cls.handle_menu.sendChatMenu(handle.message_from)

        return Response(content = "Mensaje enviado", status_code=200)

    

