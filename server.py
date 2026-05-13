
Arquivo 4: whatsapp_service.py
"Add file" → "Create new file"
Nome: whatsapp_service.py
Cole:
import os
import logging

logger = logging.getLogger(__name__)

async def send_whatsapp_notification(nome: str, telefone: str, email: str):
    """
    Send WhatsApp notification (currently disabled - returns success=False)
    """
    logger.info("WhatsApp notification skipped (not configured)")
    return {'success': False, 'message': 'WhatsApp not configured'}
"Commit new file"
Arquivo 5: server.py (ÚLTIMO!)
"Add file" → "Create new file"
Nome: server.py
Cole:
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

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
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
    """
    Create a new benfeitor (benefactor) and send email notification
    """
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
    """
    Get all benfeitores (for admin purposes)
    """
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
