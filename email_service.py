import smtplib
from email.message import EmailMessage

from config import EMAIL_SENDER, EMAIL_PASSWORD


def send_registration_email(to_email, clinic_name):
    msg = EmailMessage()
    msg["Subject"] = "Clinic Registration Invitation"
    msg["From"] = EMAIL_SENDER
    msg["To"] = "786saadman@gmail.com"
    msg.set_content(
        f"""
Hello {clinic_name},

We would like to invite you to register in our healthcare platform.
Please reply if interested.

Best regards.
"""
    )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
        smtp.send_message(msg)
    print(f"Email sent to {to_email}")


if __name__ == "__main__":
    send_registration_email("786saadman@gmail.com", "Saad")
