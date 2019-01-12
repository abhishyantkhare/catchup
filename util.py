import secrets
from uuid import uuid4
from user import User
from dotenv import load_dotenv
import os
import requests
import json
from apiclient import discovery
import httplib2
from oauth2client import client
import dateutil.parser
import datetime

load_dotenv()


catchup_link = os.getenv("CATCHUP_URL")
sendgrid_api_key = os.getenv("SENDGRID_KEY")
sendgrid_url = os.getenv("SENDGRID_URL")
CALENDAR_API_FREEBUSY = 'https://www.googleapis.com/calendar/v3/freeBusy'
CALENDAR_API_INFO = 'https://www.googleapis.com/calendar/v3/calendars/primary'

email_message = """Hi!

                You've been invited to a catchup. To accept or deny your invitation, go to """ + catchup_link + """.
              
                Thanks,
                The Catchup Team"""

email_subject = "You've Been Invited To A Catchup!"
sender = os.getenv("CATCHUP_EMAIL")
client_secret_path = os.getenv("CLIENT_SECRET_PATH")

SCOPES = ['https://www.googleapis.com/auth/calendar.events']



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

def google_auth_user(auth_code):
  credentials = client.credentials_from_clientsecrets_and_code(
    client_secret_path,
    SCOPES[0],
    auth_code)
  return credentials

def get_user_timezone(user_obj):
  headers = {
    "authorization": "Bearer " + user_obj.access_token,
    "content-type": "application/json"
  }

  
def get_user_free_time(user_obj):
  utc_now = datetime.datetime.utcnow()
  now = utc_now.isoformat() + 'Z'  # 'Z' indicates UTC time
  utc_nxt = utc_now + datetime.timedelta(days=7)
  nxt = utc_nxt.isoformat() + 'Z'
  print(user_obj.access_token)

  data = {
    "timeMin": now,
    "timeMax": nxt,
    "items": [
      {
        "id": user_obj.email
      }
    ]
  }

  headers = {
    "authorization": "Bearer " + user_obj.access_token,
    "content-type": "application/json"
  }

  r = requests.post(CALENDAR_API_FREEBUSY, data=json.dumps(data), headers=headers)
  rsp_data = r.json()
  print(rsp_data)
  busy_times_dicts = rsp_data['calendars'][user_obj.email]['busy']
  busy_times = [(dateutil.parser.parse(busy_dict['start']), dateutil.parser.parse(busy_dict['end'])) for busy_dict in busy_times_dicts]


  return busy_times


def merge_busy_times(busy_times_list):
  busy_times_list.sort(key=lambda item: item[0])
  print(busy_times_list)
  merged = []
  merged.append(busy_times_list[0])
  busy_times_list = busy_times_list[1:]
  for busy_time in busy_times_list:
    if busy_time[0] > merged[-1][1]:
      merged.append(busy_time)
    else:
      merged[-1][1] = max(busy_time[1], merged[-1][1])
  return merged