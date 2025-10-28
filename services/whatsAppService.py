import os
from .geminiService import GeminiService
from .httpRequets import HttpRequest
from typing import Optional, Dict, Any
import httpx

class WhatsAppService:

    @staticmethod
    async def downloadMedia(media_id: str) -> Optional[bytes]:
        metadata_response = await HttpRequest.sendToFile(media_id)
        metadata          = metadata_response.json()
        download_url      = metadata.get("url")
        download_content  = await HttpRequest.getBytesFile(download_url)
        return download_content


    @staticmethod
    async def sendWhatsappMessage(to: str, text_body: str, context_message_id: str = None):
        """
        Envía una respuesta de texto a un usuario de WhatsApp.
        """
        data = {
            "messaging_product": "whatsapp",
            "to": to,
            "text": {
                "body": text_body
            }
        }

        if context_message_id:
            # Esto hace que el mensaje de respuesta aparezca como una respuesta al original
            data["context"] = {"message_id": context_message_id}

        try:

            response = await HttpRequest.sendToWhatsApp(data)
            response.raise_for_status() # Lanza una excepción para códigos de estado 4xx/5xx
            print("Mensaje de respuesta enviado con éxito.")

        except Exception as e:
            
            return f"Error de conexión al enviar el mensaje: {e}"


    @staticmethod
    async def markMessageAsRead(message_id: str):
        """
        Marca un mensaje entrante como leído en WhatsApp.
        """

        data = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        }
        try:

            response = await HttpRequest.sendToWhatsApp(data)
            response.raise_for_status()
            print(f"Mensaje {message_id} marcado como leído.")

        except Exception as e:
            
            print(f"Error al marcar como leído: {e.response.text}")

    
    @staticmethod
    async def sendInteractiveButtons(to, body_text, buttons):

        data = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {
                    "text": body_text
                },
                "action": {
                    "buttons": buttons
                }
            }
        }

        try:
            response = await HttpRequest.sendToWhatsApp(data)
            response.raise_for_status()
        except Exception as e:
            print(f"Error al enviar el mensaje de WhatsApp: {e.response.text}")
        except Exception as e:
            print(f"Error de conexión al enviar el mensaje: {e}")


    @staticmethod
    async def sendMediaMessage(to: str, type: str, media_url: str, caption: str = None):
        try:
            pass
        except Exception as e:
            print(e)