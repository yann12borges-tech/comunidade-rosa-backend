from pydantic import BaseModel
from datetime import datetime

class BenfeitorCreate(BaseModel):
    nome: str
    telefone: str
    email: str

class Benfeitor(BaseModel):
    nome: str
    telefone: str
    email: str
    created_at: datetime
    notified: bool = False

class ContatoCreate(BaseModel):
    name: str
    email: str
    message: str
