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
            logger.warning("Email config incomplete")
            return {'success': False, 'error': 'Config incomplete'}
        
        message = MIMEMultipart()
        message['From'] = email_from
        message['To'] = ', '.join(email_to)
        message['Subject'] = 'Novo Benfeitor Cadastrado'
        
        body = "Novo benfeitor: " + nome + " - Telefone: " + telefone + " - Email: " + email
        
        message.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(message)
        
        logger.info("Email sent")
        return {'success': True, 'recipients': email_to}
        
    except Exception as e:
        logger.error("Email failed: " + str(e))
        return {'success': False, 'error': str(e)}
