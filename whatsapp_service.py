import os
import logging

logger = logging.getLogger(__name__)

async def send_whatsapp_notification(nome: str, telefone: str, email: str):
    logger.info("WhatsApp notification skipped")
    return {'success': False, 'message': 'WhatsApp not configured'}
