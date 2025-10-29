import os
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

class TavilySearch:

    def __init__(self):
        self.initTavilyClient()


    def initTavilyClient(self):
        self.tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"),
                                          search_depth="advanced",
                                          include_raw_content=True
                                          )

    
    @classmethod
    async def queryChatSimple(cls, user_message, user, session):
        tavily = cls()
        response     = tavily.tavily_client.search(user_message)
        processed_response = (f"{response.get("results", {})[0].get("url", "")}"
                              f"{response.get("results", {})[0].get("title", "")}"
                              f"{response.get("results", {})[0].get("content", "")}")

        return processed_response