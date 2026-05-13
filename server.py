from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime, timezone
import logging
from dotenv import load_dotenv

from models import BenfeitorCreate
from email_service import send_email_notification

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

@app.on_event("shutdown")
async def shutdown():
    client.close()
