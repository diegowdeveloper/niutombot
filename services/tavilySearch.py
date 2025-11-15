import os
from dotenv import load_dotenv
from tavily import TavilyClient
from .llmModel import LLMModel

load_dotenv()

class TavilySearch(LLMModel):

    def __init__(self, session):
        super().__init__(session)
        self.initTavilyClient()


    def initTavilyClient(self):
        self.tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

    
    @classmethod
    async def queryChat(cls, user_message, user, session):

        tavily   = cls(session)
        response = tavily.tavily_client.search(
            user_message + " busca SIEMPRE fuentes verídicas, expresa el resultado en español en NO MÁS de 450 palabras",
            search_depth        = "advanced",
            include_raw_content = True,
            max_results         = 3,
            include_answer      = "advanced" 
        )

        processed_response = "Aquí tienes algunas fuentes:"

        for result in response.get("results"):
            processed_response += f"\n\n *{result["url"]}*\n{result["title"]}\n{result["content"][:250] + "(continúa leyendo en el enlace)..."}"

        return processed_response