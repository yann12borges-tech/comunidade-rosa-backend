import os
import logging

logger = logging.getLogger(__name__)

async def send_whatsapp_notification(nome: str, telefone: str, email: str):
    """
    Send WhatsApp notification (currently disabled - returns success=False)
    """
    logger.info("WhatsApp notification skipped (not configured)")
    return {'success': False, 'message': 'WhatsApp not configured'}
