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

from .geminiService import GeminiService

load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")

class LangChainGemini:

    store: Dict[str, BaseChatMessageHistory] = {}

    def __init__(self, session, user_id):
        self.session = session
        self.config  = {"configurable": {"session_id": user_id}}


    def getAllPensamientosByIDProfesor(self, profesor_id) -> list[Pensamiento]:
        return self.session.exec(select(Pensamiento).where(Pensamiento.profesor_id == profesor_id)).all()

    
    def getChatHistory(self, results) -> list[HumanMessage, AIMessage]:
        messages = []
        for row in results:
            if row.role == "user":
                messages.append(HumanMessage(content=str(row.content)))
            elif row.role == "model":
                messages.append(AIMessage(cotent=str(row.content)))
        return messages

    
    @classmethod
    def getSessionHistory(cls, session_id: str) -> BaseChatMessageHistory:
        if session_id not in cls.store:
            cls.store[session_id] = InMemoryChatMessageHistory()
        return cls.store[session_id]


    @classmethod
    async def queryChatSimple(cls, user_message, user, session):
        
        langchainService = cls(session, user.id)
        model_llm        = ChatGoogleGenerativeAI(model       = "gemini-2.5-flash",
                                             temperature = 0.5,
                                             max_tokens  = None,
                                             max_retries = 2)
        
        with_message_history    = RunnableWithMessageHistory(model_llm, langchainService.getSessionHistory)
        results                 = langchainService.getAllPensamientosByIDProfesor(user.id)

        if with_message_history:
            response = with_message_history.invoke(
                                        [SystemMessage(content = "Eres un asistente virtual para ayudar a los docentes en sus labores y te llamas Niutom"), HumanMessage(content=user_message)],
                                        config                 = langchainService.config
                                        )

            if not response.content:
                response_text = await GeminiService.queryChatSimple(user_message, user, session)
                return response_text

            return response.content
            
        else:

            messages    = []

            if not results:
                messages = [
                    SystemMessage(content="Eres un asistente virtual llamado Niutom y estás en modo Pro para ayudar en las labores diarias de un docente"),
                    HumanMessage(content=user_message),
                ]
            else:
                messages = langchainService.getChatHistory(results)
                messages.append(SystemMessage(content="Eres un asistente virtual llamado Niutom y estás en modo Pro para ayudar en las labores diarias de un docente"))
                messages.append(HumanMessage(content=user_message))


            trim_tokens = trim_messages(
                messages,
                max_tokens    = 1000,
                strategy      = "last",
                token_counter = ChatGoogleGenerativeAI(model = "gemini-2.5-flash")
            )

            return model_llm.invoke(trim_tokens).content