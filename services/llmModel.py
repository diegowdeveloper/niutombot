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
from abc import ABC

class LLMModel(ABC):

    def __init__(self, session):
        self.session = session
    
    @classmethod
    async def queryChat(cls, user_message, user, session) -> str: ...


    def getAllThroughtsByIDProfesor(self, profesor_id) -> list[Pensamiento]: ...


    def getChatHistory(self, results) -> None: ...


    def createThought(self, profesor_id, role, message) -> None:
        new_pensamiento = Pensamiento(role = role, content = message, profesor_id = profesor_id)
        self.session.add(new_pensamiento)
        self.session.commit()
        self.session.refresh(new_pensamiento)
