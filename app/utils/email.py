import smtplib
from email.mime.text import MIMEText
from app.config import settings




def send_reset_email(recipient_email : str, token : str):
    
    reset_link = (
        f"http://localhost:5173/reset-password"
        f"?token={token}"
    )
    
    
    
    body = f"""
    Hello,
    
    You requested a password reset for your KisanPath account.
    
    Click the link below:
    
    {reset_link}
    
    This link expire in 5 minutes.
    
    If you did not request this, ignore this email.
    
    Regards,
    KisanPath Team
    """
    
    
    msg = MIMEText(body)
    
    msg["Subject"] = "KisanPath Password Reset"
    msg["From"] = settings.EMAIL_USER
    msg["To"] = recipient_email

    with smtplib.SMTP(settings.EMAIL_HOST,settings.EMAIL_PORT) as server:

        server.starttls()

        server.login(
            settings.EMAIL_USER,
            settings.EMAIL_PASSWORD
        )

        server.send_message(msg)