import pika
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json

# RabbitMQ configuration
rabbitmq_host = 'localhost'
rabbitmq_queue = 'email_queue'

# Gmail SMTP configuration
smtp_server = "smtp.gmail.com"
smtp_port = 587

connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host))
channel = connection.channel()
channel.queue_declare(queue=rabbitmq_queue)

def send_email(sender_email, password, receiver_email, text):
    message = MIMEMultipart("alternative")
    message["Subject"] = "Test Email"
    message["From"] = sender_email
    message["To"] = receiver_email

    part1 = MIMEText(text, "plain")
    message.attach(part1)

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())

def callback(ch, method, properties, body):
    data = json.loads(body.decode('utf-8'))
    sender_email = data['sender_email']
    password = data['password']
    receiver_email = data['receiver_email']
    text = data['text']

    send_email(sender_email, password, receiver_email, text)
    print(f"Email sent to {receiver_email}")

channel.basic_consume(queue=rabbitmq_queue, on_message_callback=callback, auto_ack=True)

print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
