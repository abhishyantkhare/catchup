import secrets
from uuid import uuid4
from user import User
from dotenv import load_dotenv
import os
import requests
import json


load_dotenv()


catchup_link = os.getenv("CATCHUP_URL")
sendgrid_api_key = os.getenv("SENDGRID_KEY")
sendgrid_url = os.getenv("SENDGRID_URL")

email_message = """Hi!

                You've been invited to a catchup. To accept or deny your invitation, go to """ + catchup_link + """.
              
                Thanks,
                The Catchup Team"""

email_subject = "You've Been Invited To A Catchup!"
sender = os.getenv("CATCHUP_EMAIL")


def generate_token():
  return secrets.token_urlsafe(16)


def get_error(msg):
  return {"error": msg}


def validate_user(user_email, session_token):
  if not User.objects(email=user_email):
      return False, get_error("No Such User")
  user_obj = User.objects.get(email=user_email)
  if user_obj.session_token != session_token or user_obj.session_token == '':
      return False, get_error("Invalid Session Token")
  return True, user_obj


def generate_uuid():
  return uuid4()


def send_emails(email_list):
  for email in email_list:
    send_email(email)


def send_email(recipient):
  data = json.dumps(create_email(recipient))
  headers = {
    'authorization': 'Bearer ' + sendgrid_api_key,
    'content-type': 'application/json'
  }
  r = requests.post(sendgrid_url, data=data, headers=headers)
  print(r.text)


def create_email(recipient):
  email_obj = {
    "personalizations": 
    [
      {
        "to": [{"email": recipient}],
        "subject": email_subject
      }
    ], 
    "from": 
    {
      "email": sender, 
      "name": "Catchup Team"
    },
    "subject": email_subject,
    "content":
    [
      {
        "type": "text/plain",
        "value": email_message
      }
    ]
  }
  return email_obj

