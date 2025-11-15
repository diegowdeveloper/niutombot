from ..whatsAppService import WhatsAppService
from typing import Optional, List, Dict, Any

class SenderMessage:
    async def sendProcessingMessage(self, message_from, message_id):
        await WhatsAppService.sendWhatsappMessage(message_from, "Pensando 🧠", message_id)


    async def sendListeningMessage(self, message_from, message_id):
        await WhatsAppService.sendWhatsappMessage(message_from, "Escuchando👂🏽", message_id)


    async def sendViewImage(self, message_from, message_id):
        await WhatsAppService.sendWhatsappMessage(message_from, "Analizando la imagen 👀", message_id)


    async def sendWelcomeMessage(self, message_from, sender_name):
        message = f"*¡Hola {sender_name}!* Un gusto en saludar, ¿Qué te gustaría hacer?"
        await WhatsAppService.sendWhatsappMessage(message_from, message)