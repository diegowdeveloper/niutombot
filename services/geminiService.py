import os
import json
import tempfile
from google import genai
from google.genai import types
from google.genai.types import UserContent, ModelContent, Part
from dotenv import load_dotenv
from models import Pensamiento
from sqlmodel import select
from google.cloud import speech
from .llmModel import LLMModel
from .azureNiutomCompendium import AzureNiutomCompendium
from azure.search.documents.models import VectorizedQuery, VectorizableTextQuery

load_dotenv()

class GeminiService(LLMModel):

    def __init__(self, session, user):
        super().__init__(session)
        self.model          = "gemini-2.5-flash"
        self.temperature    = .7
        self.chat_history   = [
            UserContent(parts=[types.Part.from_text(text="Hola Niutom, cuál es tu función")]),
            ModelContent(parts=[types.Part.from_text(text=f"¡Hola {user.name}! Mi función es asistirte en las tareas diarias de tu labor.")])
        ]
        self.indicaciones   = "Quiero que el temario de contenidos que hagas siempre debe especificar el siguiente formato: *semana:* (primera semana, segunda semana, tercera semana) *contenido:* *método de evaluación:* por cada uno de estas filas se encontrarán a continuación los valores según correspondan con lo que desea construir el profesor. Para desglosar y plasmar un temario de contenidos tentativos en la fila 'contenido', deberás analizar el tema que te pide el profesor, desglozarlo y con base a fuentes verídicas plasmar el temario de contenidos, por último, puedes sugerir en la fila de 'método de evaluación' cualquier actividad (pruebas, exposiciones, mapas mentales/conceptuales y más) que permita la comprobación de conocimientos. Ofrece SOLO un máximo de cuatro (4) semanas con temas tentativos al docente"
        self.comunicacion   = "Usa emojis pero no en exceso para expresarte, toma en cuenta que hablas con docentes de primaria y bachillerato, por eso, maneja siempre un dialecto acorde a la altura de un docente, pero sin entrar en exceso a la formalidad, quiero que el docente sienta que habla con un agente cercano. No puedes usar símbolos especiales en exceso como *, si vas a marcar en negrilla solo usa un solo par de asteriscos (como por ejemplo *este es un ejemplo*), no se te permite usar exceso de asteriscos como: **este es un ejemplo**, mantén siempre una comunicación de respeto, sin caer en formalismos. Es OBLIGATORIO que expreses el resultado en NO MAS de 450 palabras" 
        self.token_base     = 1500


    def getAllThroughtsByIDProfesor(self, profesor_id) -> list[Pensamiento]:
        return self.session.exec(select(Pensamiento).where(Pensamiento.profesor_id == profesor_id)).all()
    

    def getChatHistory(self, results):
        for row in results:
            if row.role == "user":
                self.chat_history.append(UserContent(parts=[types.Part.from_text(text=row.content)]))
            elif row.role == "model":
                self.chat_history.append(ModelContent(parts=[types.Part.from_text(text=row.content)]))

        if len(self.chat_history) > 4:
            self.chat_history = self.chat_history[-4:]


    def createThought(self, user_id, role, message):
        try: 
            new_thought = Pensamiento(role=role, content=message,profesor_id=user_id)
            self.session.add(new_thought)
            self.session.commit()
            self.session.refresh(new_thought)
        except Exception as e:
            print(e)


    @staticmethod
    def setupCredentialsSpeechToText():
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            json_data                                    = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
            parsed_json                                  = json.loads(json_data)
            json.dump(parsed_json, temp_file)
            temp_file_path                               = temp_file.name
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_file_path


    @staticmethod
    async def processAudioMessage(audio_bytes: bytes):
        try:
            GeminiService.setupCredentialsSpeechToText()
            client_speech    = speech.SpeechClient()
            audio            = speech.RecognitionAudio(content=audio_bytes)
            config           = speech.RecognitionConfig(
                encoding                     = speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
                language_code                = "es-ES",
                sample_rate_hertz            = 16000
            )

            response        = client_speech.recognize(config=config, audio=audio)
            transcription   = ""
            if response.results:
                transcription = response.results[0].alternatives[0].transcript
            else:
                transcription = "Ha habido un error al intentar procesar el audio, hazle saber al docente que ha ocurrido un error y que lo intente ahora por texto"

            return transcription
        except Exception as e:
            return f"Ha ocurrido un error: \n\n _{e}_"


    @classmethod
    async def queryChatMedia(cls, media_bytes, mime_type, user, session, caption) -> str:
        geminiModel = cls(session, user)
        results     = geminiModel.getAllThroughtsByIDProfesor(user.id)

        if results:
            geminiModel.getChatHistory(results)

        rules       = (
            "Te llamas Niutom, eres un asistente virtual que habla siempre en castellano"
            "siempre responderás en castellano sin importar si buscas fuentes en otros idiomas"
            f"comunícate siguiendo SIEMPRE estas reglas: {geminiModel.comunicacion}."
            "analiza la imagen que te han proporcionado"
            "toma en cuenta que el formato de salida es en un mensaje de WhatsApp"
        )

        client      = genai.Client()
        try:
            response = client.models.generate_content(
                model    = geminiModel.model,
                contents = [
                    types.Part.from_bytes(
                        data=media_bytes,
                        mime_type=mime_type
                    ),
                    caption
                ],
                config   = types.GenerateContentConfig(
                    system_instruction = rules
                )
            )
            geminiModel.createThought(user.id, "user", caption)
            geminiModel.createThought(user.id, "model", response.text)
            return response.text

        except Exception as e:
            print(f"Ha ocurrido un error en la línea 96 de gemini.py:\n\n {e}")
            response = client.models.generate_content(
                model       = geminiModel.model, 
                config      = types.GenerateContentConfig(
                    temperature         = geminiModel.temperature,
                    contents            = caption,
                    system_instruction  = (
                        "Imagina que has tenido un inconveniente al intentar cumplir la consulta que te piden"
                        "hazlo saber al usuario de que has tenido un inconveniente al tratar de responder la consulta"
                        f"no debes responder a la siguiente pregunta {user_message}, solo indica que ha ocurrido un error"
                        "sugiere al usuario que vuelva al menú de inicio marcando la opción 'Volver al inicio'"
                        f"comunícate siguiendo SIEMPRE estas reglas: {geminiModel.comunicacion}"
                    )
                )
            )
            return response.text

    
    @classmethod
    async def queryChat(cls, user_message, user, session) -> str:
        geminiModel = cls(session, user)
        results     = geminiModel.getAllThroughtsByIDProfesor(user.id)

        if results: 
            geminiModel.getChatHistory(results)

        context = ""

        if "hola" not in user_message.lower():
            azureSearchClient = AzureNiutomCompendium(session)
            azureSearchClient.setSearchClient()
            search_results    = azureSearchClient.search_client.search(
                None,
                top=3,
                vector_queries=[
                    VectorizableTextQuery(text=user_message, k_nearest_neighbors=3, fields="text_vector")
                ]
            )

            context = "complementa el resultado con el siguiente contexto " + azureSearchClient.obtainContextData(search_results)

        rules       = (
            "Te llamas Niutom, eres un asistente virtual que habla siempre en castellano"
            "siempre responderás en castellano sin importar si buscas fuentes en otros idiomas"
            f"comunícate siguiendo SIEMPRE estas reglas: {geminiModel.comunicacion}."
            f"Usa este contexto como complemento para responder: {context}"
            "toma en cuenta que el formato de salida es en un mensaje de WhatsApp"
        )

        client         = genai.Client()
        token_count    = client.models.count_tokens(model=geminiModel.model, contents=user_message)
        total_tokens = token_count.total_tokens

        try:
            response = client.models.generate_content(
                model    = geminiModel.model,
                contents = geminiModel.chat_history + [UserContent(parts=types.Part.from_text(text=user_message))],
                config   = types.GenerateContentConfig(
                    system_instruction = rules,
                    top_p              = .95,
                    top_k              = 200,
                    temperature        = geminiModel.temperature,
                    max_output_tokens  = int(total_tokens) + 5000
                )
            )
            geminiModel.createThought(user.id, "user", user_message)
            geminiModel.createThought(user.id, "model", response.text)
            return response.text

        except Exception as e:
            print(f"Ha ocurrido un error en la línea 96 de gemini.py:\n\n {e}")
            response = client.models.generate_content(
                model       = geminiModel.model, 
                config      = types.GenerateContentConfig(
                    temperature         = geminiModel.temperature,
                    contents            = user_message,
                    system_instruction  = (
                        "Imagina que has tenido un inconveniente al intentar cumplir la consulta que te piden"
                        "hazlo saber al usuario de que has tenido un inconveniente al tratar de responder la consulta"
                        f"no debes responder a la siguiente pregunta {user_message}, solo indica que ha ocurrido un error"
                        "sugiere al usuario que vuelva al menú de inicio marcando la opción 'Volver al inicio'"
                        f"comunícate siguiendo SIEMPRE estas reglas: {geminiModel.comunicacion}"
                    )
                )
            )
            return response.text
        

    @classmethod
    async def queryChatSimpleDefault(cls, user_message, user, session):
        geminiService = cls(session)

        system_instruction = (
            "Te llamas Niutom y estás en 'modo básico', eres un asistente virtual en español" 
            "que permite susgerir actividades escolares, métodos de evaluación, asistencia en"
            "conceptos y temas, resúmenes sobre algún tema en particular y permite asistir a la"
            "planificación escolar de los profesores para con sus cursos, estás listo para hablar" 
            "con un profesor de la Unidad Educativa Instituto San Antonio,"
            "tu objetivo en el modo básico es entender lo que te pide el profesor"
            "mientras más hables con el profesor más podrás entenderlo"
            "toma en cuenta que ya hiciste un saludaste y estás a la espera de que te hagan una pregunta,"
            "si el profesor(a) quiere hacer un resumen sobre algún tema puedes hacerlo pero siempre indica"
            "al final que el modo 'Niutom Compendium' puede hacer resúmenes sobre el repertorio de temas"
            "que hay en la escuela."
            "toma en cuenta que tu ámbito escolar es para la localidad geográfica de Venezuela",
            "y en Venezuela la escuela se ordena por kinder, primaria de 1er a 6to grado y bachillerato de 1er a 5o año,"
            "usa emojis su es necesario para enriquecer la respusta y no uses caracteres especiales como * por ejemplo"
            "busca siembre que las respuestas sean expresadas como si escribiera un ser humano, con caracteres comunes"
            "toma en cuenta que tu respuesta es para un profesor o director, maneja un vocabulario adecuado, semiformal"
        )

        client = genai.Client()
        chat   = client.chats.create(
            model   = "gemini-2.5-flash",
            config  = types.GenerateContentConfig(
                system_instruction = system_instruction,
                temperature        = 0.7
            )
        )

        try:
            geminiService.createThought(user.id, "user", user_message)
            response = chat.send_message(user_message)
            geminiService.createThought(user.id, "model", response.text)
            return response.text

        except Exception as e:
            print(e)
            response = client.models.generate_content(
                model       ="gemini-2.5-flash", 
                config      = types.GenerateContentConfig(
                    temperature         = 0.3,
                    system_instruction  = (
                        "Imagina que has tenido un inconveniente al intentar cumplir la consulta que te piden"
                        "hazlo saber al usuario de que has tenido un inconveniente al tratar de responder la consulta"
                        "anterior y sugiere cambiar al modelo Niutom Compendium o Niutom Pro para más efectividad"
                        f"no debes responder a la siguiente pregunta {user_message}, solo indica cambiar de modelo"
                        "a Niutom Pro con más efectividad o Niutom Compendium con una base de conocimientos"
                        "cargados del repertorio de temas de la escuela"
                    )
                ),
                contents = user_message
            )
            return response.text