from .whatsAppService import WhatsAppService
from fastapi import Response
from typing import Optional, List, Dict, Any
from .geminiService import GeminiService
from .langChainService import LangChainGemini
from .azureNiutomCompendium import AzureNiutomCompendium
from .tavilySearch import TavilySearch
from db import SessionDep
from sqlmodel import select
from models import Mensaje

# librerías personales
from .menues.handleMenu import HandleMenu
from .assistants.handleAssistant import HandleAssistant
from .assistants.handleAssistantMedia import HandleAssistantMedia
from .users.userHandler import UserHandler
from .users.userPointer import UserPointer
from .senders import SenderMessage

# Clase principal
class MessageHandler:
    user_handler     = UserHandler()
    user_pointer     = UserPointer()
    handle_assistant = HandleAssistant()
    handle_menu      = HandleMenu()
    handle_media     = HandleAssistantMedia()
    sender_message   = SenderMessage()


    def __init__(self, message, sender_info, session):
        self.session                     = session
        self.message                     = message                   
        self.sender_info                 = sender_info
        self.message_from: str           = message.get("from")
        self.message_id                  = message.get("id")
        self.message_type: str           = message.get("type")
        self.message_body: Optional[str] = message.get("text", {}).get("body", {})


    def checkMessage(self):
        try:
            _message_exists = self.session.exec(select(Mensaje).where(Mensaje.message_id == self.message_id)).first()

            if _message_exists:
                return True
            else:
                return False
            
        except Exception as e:
            print(f"Ha ocurrido un error: {e}")


    def saveMessage(self):
        new_message = Mensaje(message_id=self.message_id)
        self.session.add(new_message)
        self.session.commit()
        self.session.refresh(new_message)


    @classmethod
    async def handleIncomingMessage(cls, message, sender_info, session):

        handle = cls(message, sender_info, session)
        await WhatsAppService.markMessageAsRead(handle.message_id)

        _message_exists = handle.checkMessage()

        if _message_exists:
            return
        
        handle.saveMessage()

        sender_data  = cls.user_handler.getSenderData(sender_info)
        chatmode     = cls.user_pointer.getChatMode(session, sender_data)
        _user_exists = cls.user_pointer.searchUser(session, sender_data)

        end_message = "¡Hola! Gracias por usar Niutom. Este asistente virtual ha finalizado su período de uso. Con base a las respuestas que dejaste en la encuesta este bot fue presentado como trabajo de grado por Diego Castro para optar al título de Ingeniero en Informática en la Universidad Alejandro de Humboldt. De antemano quiero agradecerte por usar el asistente ya que me ayudaste a completar mi carrera, fueron años de trabajo duro y dedicación. Sin más, quiero decirte que no claudiques en el ejercicio de dar clase, es un pilar fundamental para la sociedad, y espero que este proyecto sea el antecedente de una cadena de investigaciones que permitan ayudar a los docentes en su labor. 👨🏼‍🏫🎆🎊👩🏼‍🏫🎇🎉"

        WhatsAppService.sendWhatsappMessage(handle.message_from, end_message, handle.message_id)

        if not _user_exists:
            cls.user_pointer.create_user(handle.session, sender_data["name"], sender_data["wa_id"])

        if message and handle.message_type == "text":
            if "hola" in handle.message_body.lower().strip() and len(handle.message_body.lower().strip()) <= 12 and not _user_exists:
                sender_name = cls.user_handler.getSenderName(handle.sender_info)
                await cls.sender_message.sendWelcomeMessage(handle.message_from, sender_name)
                await cls.handle_menu.sendWelcomeListMenu(handle.message_from)
            elif chatmode == "niutom_basico":
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
            audio_bytes      = await cls.handle_media.getBytes(audio_id)
            transcription    = await GeminiService.processAudioMessage(audio_bytes)
            await cls.handle_media.handleMessageAudio(handle.session, cls.user_pointer, sender_data, handle.message_from, transcription, chatmode)
            await cls.handle_menu.sendChatMenu(handle.message_from)

        elif handle.message_type == "image":

            await cls.sender_message.sendViewImage(handle.message_from, handle.message_id)

            image_id        = handle.message.get("image", {}).get("id")
            image_bytes     = await cls.handle_media.getBytes(image_id)
            mime_type       = message.get("image", {}).get("mime_type")
            caption         = message.get("image", {}).get("caption", "Analiza esta imagen")
            await cls.handle_media.handleMessageImage(handle.session, cls.user_pointer, sender_data, handle.message_from, image_bytes, mime_type, caption, chatmode)
            await cls.handle_menu.sendChatMenu(handle.message_from)

        return Response(content = "Mensaje enviado", status_code=200)

    

