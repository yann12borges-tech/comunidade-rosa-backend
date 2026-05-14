📋 PASSO 1 — Atualizar 3 arquivos no GitHub (backend)
Acessa: 🔗 https://github.com/yann12borges-tech/comunidade-rosa-backend

Arquivo 1: models.py → editar e substituir TUDO por:
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
Arquivo 2: email_service.py → editar e substituir TUDO por:
import os
import asyncio
import logging
import resend

logger = logging.getLogger(__name__)


async def send_email_notification(nome: str, telefone: str, email: str):
    try:
        resend_api_key = os.environ.get('RESEND_API_KEY')
        email_from = os.environ.get('EMAIL_FROM', 'onboarding@resend.dev')
        email_to_raw = os.environ.get('EMAIL_TO', '')

        if not resend_api_key or not email_to_raw:
            logger.warning("Email config incomplete")
            return {'success': False, 'error': 'Config incomplete'}

        email_to = [e.strip() for e in email_to_raw.split(',') if e.strip()]

        resend.api_key = resend_api_key

        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #1e40af;">Novo Benfeitor Cadastrado</h2>
            <p style="color: #374151;">Um novo benfeitor acaba de se cadastrar no site da Comunidade Missionaria Nossa Senhora da Rosa Mistica:</p>
            <table style="border-collapse: collapse; width: 100%; margin-top: 20px;">
                <tr>
                    <td style="padding: 10px; border: 1px solid #e5e7eb; background-color: #f9fafb; font-weight: bold; width: 30%;">Nome</td>
                    <td style="padding: 10px; border: 1px solid #e5e7eb;">{nome}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #e5e7eb; background-color: #f9fafb; font-weight: bold;">Telefone</td>
                    <td style="padding: 10px; border: 1px solid #e5e7eb;">{telefone}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #e5e7eb; background-color: #f9fafb; font-weight: bold;">Email</td>
                    <td style="padding: 10px; border: 1px solid #e5e7eb;">{email}</td>
                </tr>
            </table>
            <p style="color: #6b7280; margin-top: 30px; font-size: 14px;">Entre em contato com o benfeitor para agradecer a contribuicao. Que Deus abencoe!</p>
        </div>
        """

        params = {
            "from": email_from,
            "to": email_to,
            "subject": "Novo Benfeitor Cadastrado - Rosa Mistica",
            "html": html_body
        }

        result = await asyncio.to_thread(resend.Emails.send, params)

        logger.info(f"Email sent via Resend: {result.get('id')}")
        return {'success': True, 'recipients': email_to, 'email_id': result.get('id')}

    except Exception as e:
        logger.error(f"Email failed: {str(e)}")
        return {'success': False, 'error': str(e)}


async def send_contact_email(name: str, email: str, message: str):
    try:
        resend_api_key = os.environ.get('RESEND_API_KEY')
        email_from = os.environ.get('EMAIL_FROM', 'onboarding@resend.dev')
        email_to_raw = os.environ.get('EMAIL_TO', '')

        if not resend_api_key or not email_to_raw:
            logger.warning("Email config incomplete")
            return {'success': False, 'error': 'Config incomplete'}

        email_to = [e.strip() for e in email_to_raw.split(',') if e.strip()]

        resend.api_key = resend_api_key

        message_html = message.replace('\n', '<br>')

        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #be123c;">Nova Mensagem de Contato</h2>
            <p style="color: #374151;">Voce recebeu uma nova mensagem pelo formulario "Fale Conosco" do site da Comunidade Missionaria Nossa Senhora da Rosa Mistica:</p>
            <table style="border-collapse: collapse; width: 100%; margin-top: 20px;">
                <tr>
                    <td style="padding: 10px; border: 1px solid #e5e7eb; background-color: #f9fafb; font-weight: bold; width: 30%;">Nome</td>
                    <td style="padding: 10px; border: 1px solid #e5e7eb;">{name}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #e5e7eb; background-color: #f9fafb; font-weight: bold;">Email</td>
                    <td style="padding: 10px; border: 1px solid #e5e7eb;"><a href="mailto:{email}" style="color: #be123c;">{email}</a></td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #e5e7eb; background-color: #f9fafb; font-weight: bold; vertical-align: top;">Mensagem</td>
                    <td style="padding: 10px; border: 1px solid #e5e7eb; white-space: pre-wrap;">{message_html}</td>
                </tr>
            </table>
            <p style="color: #6b7280; margin-top: 30px; font-size: 14px;">Para responder, basta enviar um email diretamente para <strong>{email}</strong>.</p>
        </div>
        """

        params = {
            "from": email_from,
            "to": email_to,
            "reply_to": email,
            "subject": f"Fale Conosco - Mensagem de {name}",
            "html": html_body
        }

        result = await asyncio.to_thread(resend.Emails.send, params)

        logger.info(f"Contact email sent via Resend: {result.get('id')}")
        return {'success': True, 'recipients': email_to, 'email_id': result.get('id')}

    except Exception as e:
        logger.error(f"Contact email failed: {str(e)}")
        return {'success': False, 'error': str(e)}
Arquivo 3: server.py → editar e substituir TUDO por:
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime, timezone
import logging
from dotenv import load_dotenv

from models import BenfeitorCreate, ContatoCreate
from email_service import send_email_notification, send_contact_email

load_dotenv()

mongo_url = os.environ.get('MONGO_URL')
db_name = os.environ.get('DB_NAME', 'comunidade_rosa')

client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.get("/api/")
async def root():
    return {"message": "Rosa Mistica Backend API"}

@app.post("/api/benfeitor")
async def create_benfeitor(benfeitor_data: BenfeitorCreate):
    try:
        benfeitor_dict = benfeitor_data.dict()
        benfeitor_dict['created_at'] = datetime.now(timezone.utc)
        benfeitor_dict['notified'] = False

        result = await db.benfeitores.insert_one(benfeitor_dict)

        email_result = await send_email_notification(
            nome=benfeitor_data.nome,
            telefone=benfeitor_data.telefone,
            email=benfeitor_data.email
        )

        if email_result['success']:
            await db.benfeitores.update_one(
                {'_id': result.inserted_id},
                {'$set': {'notified': True}}
            )

        return {
            'success': True,
            'message': 'Benfeitor cadastrado com sucesso!',
            'email_sent': email_result['success']
        }

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/benfeitores")
async def get_benfeitores():
    try:
        benfeitores = await db.benfeitores.find({}, {"_id": 0}).sort('created_at', -1).to_list(100)
        return {
            'success': True,
            'count': len(benfeitores),
            'benfeitores': benfeitores
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/contato")
async def create_contato(contato_data: ContatoCreate):
    try:
        contato_dict = contato_data.dict()
        contato_dict['created_at'] = datetime.now(timezone.utc)
        contato_dict['notified'] = False

        result = await db.contatos.insert_one(contato_dict)

        email_result = await send_contact_email(
            name=contato_data.name,
            email=contato_data.email,
            message=contato_data.message
        )

        if email_result['success']:
            await db.contatos.update_one(
                {'_id': result.inserted_id},
                {'$set': {'notified': True}}
            )

        return {
            'success': True,
            'message': 'Mensagem enviada com sucesso!',
            'email_sent': email_result['success']
        }

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/contatos")
async def get_contatos():
    try:
        contatos = await db.contatos.find({}, {"_id": 0}).sort('created_at', -1).to_list(100)
        return {
            'success': True,
            'count': len(contatos),
            'contatos': contatos
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("shutdown")
async def shutdown():
    client.close()
