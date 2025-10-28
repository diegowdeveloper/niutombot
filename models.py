from pydantic import BaseModel
from sqlmodel import SQLModel, Field, Relationship

class ProfesorBase(SQLModel):
    name: str        = Field(default = None)
    wa_id: str       = Field(default = None)
    mode: str | None = Field(default = None)
    new_user: bool   = Field(default = True)


class Profesor(ProfesorBase, table = True):
    id: int | None                  = Field(default = None, primary_key = True)
    pensamientos: list["Pensamiento"] = Relationship(back_populates = "profesor")


class PensamientoBase(SQLModel):
    role: str    = Field(default = "user")
    content: str = Field(default = None)


class Pensamiento(PensamientoBase, table = True):
    id: int | None      = Field(default = None, primary_key = True)
    profesor_id: int    = Field(foreign_key = "profesor.id")
    profesor: Profesor  = Relationship(back_populates = "pensamientos")