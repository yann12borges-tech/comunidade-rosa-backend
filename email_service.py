fastapi==0.110.1
uvicorn==0.25.0
motor==3.6.0
pymongo==4.9.0
pydantic==2.12.5
python-dotenv==1.2.2
resend>=2.0.0
Arquivo 2: email_service.py → editar e substituir TODO o conteúdo por:
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
            logger.warning("Email config incomplete (RESEND_API_KEY or EMAIL_TO missing)")
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
