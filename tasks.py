from celery.schedules import crontab
from workers import celery
from run import app
from datetime import datetime

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Template
from models import User

with app.app_context():
    users = User.query.all()


SMPTP_SERVER_HOST="0.0.0.0"
SMPTP_SERVER_PORT=1025
SENDER_ADDRESS="reminder@flashcards.com"
SENDER_PASSWORD=""


@celery.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(crontab(hour=19), reminder.s(), name="reminder")
    sender.add_periodic_task(crontab(day_of_month=1), report.s(), name="report")


@celery.task
def report():
    for user in users:
        file = open("monthly_report.html")
        template = Template(file.read())
        message = template.render(user=user)
            
        msg = MIMEMultipart()
        msg['From'] = SENDER_ADDRESS
        msg['To'] = user.email
        msg['Subject'] = "Flashcards - Monthly Report"

        msg.attach(MIMEText(message,'html'))

        
        s = smtplib.SMTP(host=SMPTP_SERVER_HOST, port=SMPTP_SERVER_PORT)
        s.login(SENDER_ADDRESS, SENDER_PASSWORD)
        s.send_message(msg)
        
        s.quit()

    return True    


@celery.task
def reminder():
    for user in users:
        now = datetime.today()
        delta = str(user.last_rev - now).split(':')
        if int(delta[0]) >= 19:
            file = open("daily_reminder.html")
            template = Template(file.read())
            message = template.render(user=user)

            msg = MIMEMultipart()
            msg['From'] = SENDER_ADDRESS
            msg['To'] = user['email']
            msg['Subject'] = "Flashcards - Daily Reminder"

            msg.attach(MIMEText(message,'html'))

            s = smtplib.SMTP(host=SMPTP_SERVER_HOST, port=SMPTP_SERVER_PORT)
            s.login(SENDER_ADDRESS, SENDER_PASSWORD)
            s.send_message(msg)
            s.quit()

    return True


if __name__=="__main__":
    reminder.apply_async()
    report.apply_async()

