import os
import httpx
from dotenv import load_dotenv

load_dotenv()
HTTP_CLIENT = httpx.AsyncClient()

class HttpRequest:

    @staticmethod
    async def sendToWhatsApp(data):
        baseURL = f"{os.getenv("API_URL")}/{os.getenv("API_VERSION")}/{os.getenv("BUSINESS_PHONE")}/messages"
        headers = {
            "Authorization": f"Bearer {os.getenv("API_TOKEN")}",
            "Content-Type": "application/json"
        }
        try:
            response = await HTTP_CLIENT.post(baseURL, headers = headers, json = data)
            return response
        
        except httpx.HTTPStatusError as e:
            print(f"Error del cliente: {e}")

        except Exception as e:
            print(f"Ha ocurrido un error: {e}")

    
    @staticmethod
    async def sendToFile(media_id):
        baseURL = f"{os.getenv("API_URL")}/{os.getenv("API_VERSION")}/{media_id}"
        headers = {
            "Authorization": f"Bearer {os.getenv("API_TOKEN")}",
            "Content-Type": "application/json"
        }
        try:
            response = await HTTP_CLIENT.get(baseURL, headers = headers)
            return response
        
        except httpx.HTTPStatusError as e:
            print(f"Error del cliente: {e}")

        except Exception as e:
            print(f"Ha ocurrido un error: {e}")


    @staticmethod
    async def getBytesFile(download_url):
        headers = {
            "Authorization": f"Bearer {os.getenv("API_TOKEN")}",
        }

        response = await HTTP_CLIENT.get(download_url, headers = headers)
        return response.content