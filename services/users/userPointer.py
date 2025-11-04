from typing import Optional, List, Dict, Any
from db import SessionDep
from sqlmodel import select
from models import Profesor

# Puntero que se integra con la tabla profesor
class UserPointer:

    def sessionAction(self, session, model):
        session.add(model)
        session.commit()
        session.refresh(model)


    def getChatMode(self, session, sender_data):
        mode = session.exec(select(Profesor.mode).where(Profesor.wa_id == sender_data["wa_id"])).first()
        return mode
    

    def create_user(self, session, name, wa_id):
        try: 
            new_user = Profesor(name=name, wa_id=wa_id)
            self.sessionAction(session, new_user)
        except Exception as e:
            print(e)


    def updateUser(self, session, user, option_id):
        user.mode = option_id
        self.sessionAction(session, user)
    

    def searchUser(self, session, sender_data) -> bool:
        try:
            user = session.exec(select(Profesor).where(Profesor.wa_id == sender_data["wa_id"])).first()

            if user:
                return True
            
            return False
        
        except Exception as e:
            print(f"Ha ocurrido un error al buscar al usuario: \n\n {e}")

    
    def getUserByWaID(self, session, sender_data):
        result = select(Profesor).where(Profesor.wa_id == sender_data["wa_id"])
        return session.exec(result).first()