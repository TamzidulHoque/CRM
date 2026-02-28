import smtplib
from email.message import EmailMessage
from config import (
    EMAIL_SENDER,
    MAILTRAP_HOST,
    MAILTRAP_PORT,
    MAILTRAP_USERNAME,
    MAILTRAP_PASSWORD,
)


def send_registration_email(to_email, clinic_name):
    msg = EmailMessage()
    msg["Subject"] = "Clinic Registration Invitation"
    msg["From"] = EMAIL_SENDER
    msg["To"] = to_email
    msg.set_content(f"""
Hello {clinic_name},

We would like to invite you to register in our healthcare platform.
Please reply if interested.

Best regards.
""")

    # connect with a timeout to avoid hanging indefinitely
    with smtplib.SMTP(MAILTRAP_HOST, MAILTRAP_PORT, timeout=20) as smtp:
        smtp.starttls()
        smtp.login(MAILTRAP_USERNAME, MAILTRAP_PASSWORD)
        # EmailMessage works with send_message which handles headers & payload
        smtp.send_message(msg)

    print(f"Email captured in Mailtrap inbox for {to_email}")



send_registration_email("tamzidulhoquetahmid@gmail.com", "Tahmid")