import os
import logging
import smtplib
import email
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate


def send_mail(to, subject, text, sender="noreply@halifax.ca", files: list = [], cc: list = [], bcc: list = [], server="localhost"):
    message = MIMEMultipart()

    message['From'] = sender
    message['To'] = COMMASPACE.join(to)
    message['Date'] = formatdate(localtime=True)
    message['Subject'] = subject
    message['Cc'] = COMMASPACE.join(cc) if cc else None

    message.attach(MIMEText(text))

    for file in files:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(open(file, 'rb').read())

        email.encoders.encode_base64(part)

        part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(file))

        message.attach(part)

    addresses = [x for x in to]

    for x in cc:
        addresses.append(x)

    for x in bcc:
        addresses.append(x)

    smtp = smtplib.SMTP(server)
    smtp.sendmail(sender, addresses, message.as_string())
    smtp.close()


def send_html(to, subject, html, cc: list = None, bcc: list = None, sender="noreply@halifax.ca", server="mailer1.halifax.ca"):
    message = MIMEMultipart()

    message['From'] = sender
    message['To'] = COMMASPACE.join(to)
    message['Date'] = formatdate(localtime=True)
    message['Subject'] = subject
    message['Cc'] = COMMASPACE.join(cc)

    message.attach(MIMEText(html, "html"))
    addresses = []

    for x in to:
        addresses.append(x)

    for x in cc:
        addresses.append(x)

    for x in bcc:
        addresses.append(x)

    smtp = smtplib.SMTP(server)
    smtp.sendmail(sender, addresses, message.as_string())
    smtp.close()


def send_error(title, text):
    server = "mailer1.halifax.ca"
    sender = "noreply@halifax.ca"
    recipients = [
        "potterm@halifax.ca",
        "gallaga@halifax.ca"
    ]

    send_mail(recipients, title, text, sender, server=server)


def send_everbridge_error(title, text):
    server = "mailer1.halifax.ca"
    sender = "noreply@halifax.ca"

    recipients = ["potterm@halifax.ca", "milesp@halifax.ca", "gallaga@halifax.ca", "taylorki@halifax.ca"]
    send_mail(recipients, title, text, sender, [], [], [], server)


def set_up_log(log_file, log_to_console: bool = False):
    formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s: %(message)s', datefmt='%m-%d-%Y %H:%M:%S')

    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


if __name__ == "__main__":
    logFile = r"E:\HRM\Scripts\Python3\parks dashboard\server_setup\scripts\logs\logs_02062023.log"
    logger = set_up_log(logFile)

    send_error("ERROR - Project to WGS84 Backup Creation Failed", "MSGISAPPQ204 / Project_to_WGS84.py")
