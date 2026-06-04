import smtplib
from email.mime.text import MIMEText
from app.config import settings


def send_email(recipient_email: str, subject: str, body: str):

    msg = MIMEText(body)

    msg["Subject"] = subject
    msg["From"] = settings.EMAIL_USER
    msg["To"] = recipient_email

    with smtplib.SMTP(
        settings.EMAIL_HOST,
        settings.EMAIL_PORT
    ) as server:

        server.starttls()

        server.login(
            settings.EMAIL_USER,
            settings.EMAIL_PASSWORD
        )

        server.send_message(msg)


def send_welcome_email(
    recipient_email: str,
    full_name: str,
    role: str
):

    role = role.upper()

    if role == "USER":

        subject = "Welcome to KisanPath"

        body = f"""
Hello {full_name},

Welcome to KisanPath!

Your account has been created successfully.

You can now:
• Browse products
• Purchase crops
• Connect with farmers and vendors

Thank you for joining KisanPath.

Regards,
KisanPath Team
"""

    elif role == "FARMER":

        subject = "Welcome Farmer to KisanPath"

        body = f"""
Hello {full_name},

Welcome to KisanPath!

Your Farmer account has been created successfully.

You can now:
• List your crops
• View market prices
• Connect with buyers
• Manage your farm profile

Thank you for joining KisanPath.

Regards,
KisanPath Team
"""

    elif role == "VENDOR":

        subject = "Welcome Vendor to KisanPath"

        body = f"""
Hello {full_name},

Welcome to KisanPath!

Your Vendor account has been created successfully.

You can now:
• Add agricultural products
• Manage inventory
• Connect with farmers
• Sell products through KisanPath

Thank you for joining KisanPath.

Regards,
KisanPath Team
"""

    else:

        subject = "Welcome to KisanPath"

        body = f"""
Hello {full_name},

Your account has been registered successfully.

Regards,
KisanPath Team
"""

    send_email(
        recipient_email=recipient_email,
        subject=subject,
        body=body
    )