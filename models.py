from pydantic import BaseModel
from typing import Optional
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
