import os
from dotenv import load_dotenv
from typing import Dict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, trim_messages
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.chat_history import (
    BaseChatMessageHistory,
    InMemoryChatMessageHistory
)
from langchain_core.runnables import RunnableWithMessageHistory

from models import Pensamiento
from sqlmodel import select
from .llmModel import LLMModel

from .geminiService import GeminiService
from .azureNiutomCompendium import AzureNiutomCompendium
from azure.search.documents.models import VectorizedQuery, VectorizableTextQuery

load_dotenv()
# os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")

class LangChainGemini(LLMModel):

    store: Dict[str, BaseChatMessageHistory] = {}

    def __init__(self, session, user):
        super().__init__(session)
        self.model          = "gemini-2.5-flash"
        self.temperature    = .4
        self.chat_history   = [
            HumanMessage(content=str("Hola Niutom, cuál es tu función")),
            AIMessage(content=str(f"¡Hola {user.name}! Mi función es asistirte en las tareas diarias de tu labor."))
        ]
        self.config         = {"configurable": {"session_id": user.id}}
        self.comunicacion   = "Expresa el resultado en NO MÁS de 450 palabras, usa emojis pero no en exceso para expresarte, toma en cuenta que hablas con docentes de primaria y bachillerato, por eso, maneja siempre un dialecto acorde a la altura de un docente, pero sin entrar en exceso a la formalidad, quiero que el docente sienta que habla con un agente cercano. No puedes usar símbolos especiales en exceso como *, si vas a marcar en negrilla solo usa un solo par de asteriscos (como por ejemplo *este es un ejemplo*), no se te permite usar exceso de asteriscos como: **este es un ejemplo**, mantén siempre una comunicación de respeto, sin caer en formalismos."


    def getAllThroughtsByIDProfesor(self, profesor_id) -> list[Pensamiento]:
        return self.session.exec(select(Pensamiento).where(Pensamiento.profesor_id == profesor_id)).all()

    
    def getChatHistory(self, results) -> list[HumanMessage, AIMessage]:
        for row in results:
            if row.role == "user":
                self.chat_history.append(HumanMessage(content=str(row.content)))
            elif row.role == "model":
                self.chat_history.append(AIMessage(content=str(row.content)))

        if len(self.chat_history) > 4:
            self.chat_history = self.chat_history[-4:]

    
    @classmethod
    def getSessionHistory(cls, session_id: str) -> BaseChatMessageHistory:
        if session_id not in cls.store:
            cls.store[session_id] = InMemoryChatMessageHistory()
        return cls.store[session_id]


    @classmethod
    async def queryChat(cls, user_message, user, session):
        langchainService = cls(session, user)
        model_llm        = ChatGoogleGenerativeAI(google_api_key    = os.getenv("GEMINI_API_KEY"),
                                                  model             = langchainService.model,
                                                  temperature       = langchainService.temperature,
                                                  max_tokens        = 3000,
                                                  max_retries       = 2)
        with_message_history = RunnableWithMessageHistory(model_llm, langchainService.getSessionHistory)
        results              = langchainService.getAllThroughtsByIDProfesor(user.id)
        context              = langchainService.comunicacion

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

            context += "Complementa el resultado con el siguiente contexto: " + azureSearchClient.obtainContextData(search_results)

        if with_message_history:
            try:
                response = with_message_history.invoke(
                    [SystemMessage(content = f"Eres un asistente virtual para ayudar a los docentes en sus labores y te llamas Niutom. {context} {langchainService.comunicacion}"), HumanMessage(content=user_message)],
                    config                 = langchainService.config
                )

                print(len(response.content))
                if not response.content:
                    response_text = await GeminiService.queryChat(user_message, user, session)
                    return response_text

                return response.content
            except Exception as e:
                return f"Ha ocurrido un error al intentar conectar con el modelo: {e}"
            
        else:

            if results:
                langchainService.getChatHistory(results)
                langchainService.chat_history.append(SystemMessage(content="Eres un asistente virtual llamado Niutom y estás en modo Pro para ayudar en las labores diarias de un docente"))
                langchainService.chat_history.append(HumanMessage(content=user_message))

            trim_tokens = trim_messages(
                langchainService.chat_history,
                max_tokens    = 5000,
                strategy      = "last",
                token_counter = ChatGoogleGenerativeAI(google_api_key = os.getenv("GEMINI_API_KEY"), model = "gemini-2.5-flash")
            )

            return model_llm.invoke(trim_tokens).content