
Arquivo 4: email_service.py
Abra email_service.py
Edit (lápis)
Apague tudo
Cole isto:
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

logger = logging.getLogger(__name__)

async def send_email_notification(nome: str, telefone: str, email: str):
    try:
        smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.environ.get('SMTP_PORT', 587))
        smtp_username = os.environ.get('SMTP_USERNAME')
        smtp_password = os.environ.get('SMTP_PASSWORD')
        email_from = os.environ.get('EMAIL_FROM')
        email_to = os.environ.get('EMAIL_TO', '').split(',')
        
        if not all([smtp_username, smtp_password, email_from, email_to]):
            logger.warning("Email configuration incomplete")
            return {'success': False, 'error': 'Email configuration incomplete'}
        
        message = MIMEMultipart()
        message['From'] = email_from
        message['To'] = ', '.join(email_to)
        message['Subject'] = 'Novo Benfeitor Cadastrado - Comunidade Rosa Mistica'
        
        body = f"""
        <html>
        <body>
            <h2>Novo Benfeitor Cadastrado!</h2>
            <p>Um novo benfeitor se cadastrou no site:</p>
            <ul>
                <li><strong>Nome:</strong> {nome}</li>
                <li><strong>Telefone:</strong> {telefone}</li>
                <li><strong>Email:</strong> {email}</li>
            </ul>
            <p>Entre em contato para agradecer e confirmar a doacao.</p>
        </body>
        </html>
        """
        
        message.attach(MIMEText(body, 'html'))
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(message)
        
        logger.info(f"Email sent to {email_to}")
        return {'success': True, 'recipients': email_to}
        
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return {'success': False, 'error': str(e)}
Commit changes
Arquivo 5: server.py (ÚLTIMO!)
Abra server.py
Edit
Apague tudo
Cole isto:
from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List
import uuid
from datetime import datetime, timezone

from models import BenfeitorCreate, Benfeitor
from whatsapp_service import send_whatsapp_notification
from email_service import send_email_notification

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")

class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

@api_router.get("/")
async def root():
    return {"message": "Hello World"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.post("/benfeitor")
async def create_benfeitor(benfeitor_data: BenfeitorCreate):
    try:
        benfeitor_dict = benfeitor_data.dict()
        benfeitor_dict['created_at'] = datetime.now(timezone.utc)
        benfeitor_dict['notified'] = False
        
        result = await db.benfeitores.insert_one(benfeitor_dict)
        benfeitor_dict['_id'] = result.inserted_id
        
        email_result = await send_email_notification(
            nome=benfeitor_data.nome,
            telefone=benfeitor_data.telefone,
            email=benfeitor_data.email
        )
        
        whatsapp_result = await send_whatsapp_notification(
            nome=benfeitor_data.nome,
            telefone=benfeitor_data.telefone,
            email=benfeitor_data.email
        )
        
        notifications_sent = email_result['success'] or whatsapp_result['success']
        if notifications_sent:
            await db.benfeitores.update_one(
                {'_id': result.inserted_id},
                {'$set': {'notified': True}}
            )
        
        return {
            'success': True,
            'message': 'Benfeitor cadastrado com sucesso!',
            'id': str(result.inserted_id),
            'email_sent': email_result['success'],
            'whatsapp_sent': whatsapp_result['success'],
            'notification_method': 'email' if email_result['success'] else ('whatsapp' if whatsapp_result['success'] else 'none')
        }
    except Exception as e:
        logging.error(f"Error creating benfeitor: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/benfeitores")
async def get_benfeitores():
    try:
        benfeitores = await db.benfeitores.find().sort('created_at', -1).to_list(100)
        return {
            'success': True,
            'count': len(benfeitores),
            'benfeitores': [Benfeitor(**{**b, '_id': b['_id']}).dict() for b in benfeitores]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    return status_checks

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
