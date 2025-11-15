import os
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv
from azure.search.documents.models import VectorizedQuery, VectorizableTextQuery
from .llmModel import LLMModel

load_dotenv()

class AzureNiutomCompendium(LLMModel):

    def __init__(self, session):
        super().__init__(session)
        self.setOpenAICLient()
        self.setSearchClient()

    
    def setOpenAICLient(self):
        self.openai_client = AzureOpenAI(
            api_key         = os.getenv("AZURE_OPENAI_API_KEY"),
            azure_endpoint  = os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_version     = os.getenv("OPENAI_API_VERSION")
        )


    def setSearchClient(self):
        self.search_client = SearchClient(
            endpoint    = os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT"),
            index_name  = os.getenv("AZURE_SEARCH_INDEX_NAME"),
            credential  = AzureKeyCredential(os.getenv("AZURE_SEARCH_ADMN_KEY"))
        )


    async def getEmbedding(self, text):
        return self.openai_client.embeddings.create(
            model = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYED_MODEL_NAME"),
            input = text,
        ).data[0].embedding
    

    def obtainContextData(self, search_results):
        context = ""
        for result in search_results:
            context += result["chunk"] + "\n\n"
        return context
    

    def OpenAIResponseModel(self, system_message, user_message):
        response = self.openai_client.chat.completions.create(
            model       = os.getenv("AZURE_OPENAI_CHAT_COMPLETION_DEPLOYED_MODEL_NAME"),
            temperature = .7,
            messages    = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ]
        )
        return response
    

    @classmethod
    async def queryChat(cls, message, user, session):
        azureNiutomCompendium = cls(session)
        search_results        = azureNiutomCompendium.search_client.search(
            None,
            top=3,
            vector_queries=[
                VectorizableTextQuery(text=message, k_nearest_neighbors=3, fields="text_vector")
            ]
        )

        context = azureNiutomCompendium.obtainContextData(search_results)
        system_message = f"""
        Eres Niutom y estás en modo Compendium, con base a los hechos listados en el siguiente texto responde al usuario:
        Contexto:
        {context}
        """

        response = azureNiutomCompendium.OpenAIResponseModel(system_message=system_message, user_message=message)
        return response.choices[0].message.content