from fastapi import FastAPI, Query, HTTPException
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os
import pika
import json
import logging
from datetime import datetime
import smtplib

# Load environment variables
load_dotenv()

# RabbitMQ configuration
rabbitmq_host = 'localhost'
rabbitmq_queue = 'email_queue'

# Establish connection and channel
connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host))
channel = connection.channel()
channel.queue_declare(queue=rabbitmq_queue)

# Instantiate FastAPI
app = FastAPI()

# Function to send email using SMTP
def send_email(sender_email, password, receiver_email, text):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587  # For TLS

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

    return True

# Endpoint to handle email sending and logging
@app.get("/send-task/")
async def send_task(sendmail: str = Query(None), talktome: bool = Query(False)):
    try:
        if sendmail:
            # Retrieve sender credentials from environment variables
            sender_email = os.getenv('SENDER_EMAIL')
            password = os.getenv('PASSWORD')

            # Enqueue message to RabbitMQ
            message_body = {
                'sender_email': sender_email,
                'password': password,
                'receiver_email': sendmail,
                'text': "This is a test email."
            }
            channel.basic_publish(exchange='',
                                routing_key=rabbitmq_queue,
                                body=json.dumps(message_body))

            response_msg = "Email task queued successfully"
        else:
            response_msg = "No email task specified"

        if talktome:
            # Log current time to a file (e.g., ~/logs/messaging_system.log)
            logs_dir = os.path.expanduser("~/logs")
            if not os.path.exists(logs_dir):
                os.makedirs(logs_dir)  # Create directory if it doesn't exist

            log_file = os.path.join(logs_dir, "messaging_system.log")
            logging.basicConfig(filename=log_file, level=logging.INFO)
            logging.info(f"Logged time: {datetime.now()}")

        return {"message": response_msg}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process task: {str(e)}")

# Run FastAPI server with uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
