import tempfile
from google import genai
from google.genai import types
from google.genai.types import UserContent, ModelContent, Part
from dotenv import load_dotenv
from ..models import Pensamiento
from sqlmodel import select

load_dotenv()

class GeminiService:

    def __init__(self, session):
        self.session = session


    def createPensamiento(self, profesor_id, role, message) -> None:
        new_pensamiento = Pensamiento(role = role, content = message, profesor_id = profesor_id)
        self.session.add(new_pensamiento)
        self.session.commit()
        self.session.refresh(new_pensamiento)


    def getAllPensamientosByIDProfesor(self, profesor_id) -> list[Pensamiento]:
        return self.session.exec(select(Pensamiento).where(Pensamiento.profesor_id == profesor_id)).all()


    def getChatHistory(self, results) -> list[UserContent, ModelContent]:
        chat_history = []
        for row in results:
            if row.role == "user":
                chat_history.append(UserContent(parts=[Part(text=row.content)]))
            elif row.role == "model":
                chat_history.append(ModelContent(parts=[Part(text=row.content)]))
        return chat_history


    @staticmethod
    async def processAudioMessage(audio_bytes: bytes):
        temp_file_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as temp_file:
                temp_file.write(audio_bytes)
                temp_file_path = temp_file.name
                return temp_file_path
        except Exception as e:
            print(f"Ha ocurrido un error: {e}")

    
    @classmethod
    async def queryChatSimple(cls, user_message, user, session):
        geminiService = cls(session)

        chat_history = []
        results = geminiService.getAllPensamientosByIDProfesor(user.id)

        if not results:
            chat_history = [
                UserContent(parts=[Part(text="Hola Niutom, cuál es tu función")]),
                ModelContent(parts=[Part(text=f"¡Hola {user.name}! Mi función es asistirte en las tareas diarias de tu labor.")])
            ]
        else:
            chat_history = geminiService.getChatHistory(results)

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
            ),
            history = chat_history
        )

        try:
            geminiService.createPensamiento(user.id, "user", user_message)
            response = chat.send_message(user_message)
            geminiService.createPensamiento(user.id, "model", response.text)
            return response.text

        except Exception as e:
            print(e)
            response = client.models.generate_content(
                model       ="gemini-2.5-flash", 
                config      = types.GenerateContentConfig(
                    temperature         = 0.3,
                    max_output_tokens   = 500,
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
            geminiService.createPensamiento(user.id, "user", user_message)
            response = chat.send_message(user_message)
            geminiService.createPensamiento(user.id, "model", response.text)
            return response.text

        except Exception as e:
            print(e)
            response = client.models.generate_content(
                model       ="gemini-2.5-flash", 
                config      = types.GenerateContentConfig(
                    temperature         = 0.3,
                    max_output_tokens   = 500,
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


    @classmethod
    async def queryChatAudio(cls, temp_file_path, user, session):
        geminiService = cls(session)

        chat_history = []
        results = geminiService.getAllPensamientosByIDProfesor(user.id)

        if not results:
            chat_history = [
                UserContent(parts=[Part(text="Hola Niutom, cuál es tu función")]),
                ModelContent(parts=[Part(text=f"¡Hola {user.name}! Mi función es asistirte en las tareas diarias de tu labor.")])
            ]
        else:
            chat_history = geminiService.getChatHistory(results)

        system_instruction = (
            "Eres Niutom y estás en 'modo básico', eres un asistente virtual en español"
            "No hace falta que especifiques tu nombre a los docentes" 
            "que permite sugerir actividades escolares, métodos de evaluación, asistencia en"
            "conceptos y temas, resúmenes sobre algún tema en particular y permite asistir a la"
            "planificación escolar de los profesores para con sus cursos, y recordatorios que dejan los docentes"
            "estás listo para hablar con un profesor de la Unidad Educativa Instituto San Antonio,"
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
            "Si un profesor se equivoca con tu nombre no está permitido que lo corrijas"
        )

        client     = genai.Client()
        audio_file = client.files.upload(file=temp_file_path)
        chat   = client.chats.create(
            model   = "gemini-2.5-flash",
            config  = types.GenerateContentConfig(
                system_instruction = system_instruction,
                temperature        = 0.3,
                max_output_tokens  = 1000
            ),
            history = chat_history
        )

        try:
            response_transcribe = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=["Transcribe este audio, no coloques caracteres especiales como *#- solo texto plano, se permiten signos de pregunta, comas y puntos", audio_file]
            )
            geminiService.createPensamiento(user.id, "user", response_transcribe.text)
            response = chat.send_message(response_transcribe.text)
            geminiService.createPensamiento(user.id, "model", response.text)
            return response.text

        except Exception as e:
            print(e)
            response = client.models.generate_content(
                model       ="gemini-2.5-flash", 
                config      = types.GenerateContentConfig(
                    temperature         = 0.3,
                    max_output_tokens   = 500,
                    system_instruction  = (
                        "Imagina que has tenido un inconveniente al intentar cumplir la consulta que te piden"
                        "hazlo saber al usuario de que has tenido un inconveniente al tratar de responder la consulta"
                        "anterior y sugiere cambiar al modelo Niutom Compendium o Niutom Pro para más efectividad"
                    )
                ),
                contents = "Ha ocurrido un error al procesar el audio"
            )
            return response.text