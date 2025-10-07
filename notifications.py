from twilio.rest import Client
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Twilio Configuration
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE = os.getenv("TWILIO_PHONE")
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

async def send_sms(phone: str, message: str):
    """Send SMS notification"""
    try:
        message = twilio_client.messages.create(
            body=message,
            from_=TWILIO_PHONE,
            to=phone
        )
        return True
    except Exception as e:
        print(f"SMS Error: {e}")
        return False

async def send_email(to_email: str, subject: str, body: str):
    """Send email notification"""
    try:
        msg = MIMEMultipart()
        msg['From'] = "noreply@homeservepro.com"
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASSWORD"))
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Email Error: {e}")
        return False

async def send_whatsapp_message(phone: str, message: str):
    """Send WhatsApp message via Twilio"""
    try:
        message = twilio_client.messages.create(
            body=message,
            from_=f"whatsapp:{TWILIO_PHONE}",
            to=f"whatsapp:{phone}"
        )
        return True
    except Exception as e:
        print(f"WhatsApp Error: {e}")
        return False
