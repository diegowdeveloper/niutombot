from ..whatsAppService import WhatsAppService
from fastapi import Response
from ..geminiService import GeminiService
from db import SessionDep
from sqlmodel import select

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
        elif option_id == "limitaciones":
            message_reply = "https://trescomasagency.com/niutom/#limitaciones\n Aquí tienes...\n Limitaciones de Niutom 🐢"
        elif option_id == "reportar_falla":
            message_reply = "Pido disculpas por el inconveniente"
            await WhatsAppService.sendWhatsappMessage("584122106687", f"Un docente ha tenido un error con el asistente Niutom: https://wa.me/{to}")
        elif option_id == "actualizar_index":
            message_reply = "Un Ingeniero te estará contactando en los próximos cinco minutos"
            await WhatsAppService.sendWhatsappMessage("584122106687", f"Un docente quiere añadir nuevos índices a Niutom: https://wa.me/{to}")

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
                    },
                    {
                        "id": "limitaciones",
                        "title": "Limitaciones del asistente 🐢",
                        "description": "Pros y contras"
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
            },
            {
                "type": "reply",
                "reply": {
                    "id": "actualizar_index",
                    "title": "Agregar contenido"
                }
            },
            {
                "type": "reply",
                "reply": {
                    "id": "reportar_falla",
                    "title": "Reportar problema"
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