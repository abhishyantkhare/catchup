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
import pytz

load_dotenv()


catchup_link = os.getenv("CATCHUP_URL")
sendgrid_api_key = os.getenv("SENDGRID_KEY")
sendgrid_url = os.getenv("SENDGRID_URL")
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
CALENDAR_API_FREEBUSY = 'https://www.googleapis.com/calendar/v3/freeBusy'
CALENDAR_API_INFO = 'https://www.googleapis.com/calendar/v3/calendars/primary'
EVENT_API = 'https://www.googleapis.com/calendar/v3/calendars/primary/events?sendUpdates=all'
REFRESH_URL = 'https://www.googleapis.com/oauth2/v4/token'



email_subject = "You've Been Invited To A Catchup!"
sender = os.getenv("CATCHUP_EMAIL")
client_secret_path = os.getenv("CLIENT_SECRET_PATH")

SCOPES = ['https://www.googleapis.com/auth/calendar.events']

weekday_map = {
  'Sun': 6,
  'Mon': 0,
  'Tue': 1,
  'Wed': 2,
  'Thu': 3,
  'Fri': 4,
  'Sat': 5
}

frequency_map = {
  'Weekly': 1,
  'Biweekly': 2,
  'Monthly': 4
}

with open('email_template.html') as email_file:
  email_message = email_file.read().replace('\n', '')




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
        "type": "text/html",
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

def refresh_access_token(user_obj):
  data = {
    "client_id": client_id,
    "client_secret": client_secret,
    "refresh_token": user_obj.refresh_token,
    "grant_type": "refresh_token"
  }
  headers = {
    'content-type': 'application/json'
  }
  r = requests.post(REFRESH_URL, data=json.dumps(data), headers=headers)

  rsp_json = r.json()
  access_token = rsp_json['access_token']
  user_obj.access_token = access_token
  user_obj.save()

def get_user_timezone(user_obj):
  headers = {
    "authorization": "Bearer " + user_obj.access_token,
    "content-type": "application/json"
  }

  
def get_user_busy_time(user_obj):
  utc_now = datetime.datetime.utcnow()
  now = utc_now.isoformat() + 'Z'  # 'Z' indicates UTC time
  utc_nxt = utc_now + datetime.timedelta(days=7)
  nxt = utc_nxt.isoformat() + 'Z'

  refresh_access_token(user_obj)

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

def string_to_datetime(string_time, time_zone):
  weekday_str_split = string_time.split(' ')
  weekday_str = weekday_str_split[0]
  weekday_num = weekday_map[weekday_str]
  today = datetime.datetime.utcnow() 
  date = today + datetime.timedelta(days=((weekday_num-today.weekday()+7)%7))
  date = date.astimezone(pytz.timezone(time_zone))
  start_time = weekday_str_split[1]
  start_time_am = weekday_str_split[2] == 'AM'
  end_time = weekday_str_split[4]
  end_time_am = weekday_str_split[5] == 'AM'
  start_time_hr, start_time_min = get_time_hr_min(start_time, start_time_am)
  end_time_hr, end_time_min = get_time_hr_min(end_time, end_time_am)
  start_date = date.replace(hour=start_time_hr, minute=start_time_min)
  end_date = date.replace(hour=end_time_hr, minute=end_time_hr)
  return start_date, end_date


def get_time_hr_min(time_str, am):
  time_str_split = time_str.split(':')
  hr = int(time_str_split[0])
  if hr == 12:
    hr = 0
  if not am:
    hr = hr + 12
  minute = int(time_str_split[1])
  return hr, minute

def date_in_intervals(intervals, date):
  for interval in intervals:
    start = interval[0]
    end = interval[1]
    if date >= start and date <= end:
      return True
  return False


def add_event(user_obj, event, attendees):
  data = {
    "start": {
      "dateTime": event.event_start_time
    },
    "end": {
      "dateTime": event.event_end_time
    },
    "attendees": attendees,
    "summary": event.event_name
  }
  print(data)
  headers = {
    'content-type': 'application/json',
    'authorization': 'Bearer ' + user_obj.access_token
  }
  r = requests.post(EVENT_API, data=json.dumps(data), headers=headers)

def get_user_timezone(user_obj):
  headers = {
    'content-type': 'application/json',
    'authorization': 'Bearer ' + user_obj.access_token
  }
  r = requests.get(CALENDAR_API_INFO, headers=headers)

  return r.json()['timeZone']

def run_catchup_event_generate(catchup_obj, sched):
  catchup_obj.generate_new_event(sched)

def schedule_catchup_event_generate(catchup_obj, sched):
  #Change according to frequency
  job = sched.add_job(run_catchup_event_generate, run_date=datetime.datetime.now() + datetime.timedelta(weeks=frequency_map[catchup_obj.frequency]), args=[catchup_obj, sched])

  print(job)

