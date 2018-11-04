from flask import Flask
from flask import request
from flask import jsonify
from flask import make_response
from flask import render_template
from flask_cors import CORS, cross_origin
import flask
import os
import datetime
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
from bson.json_util import dumps
from pymongo import MongoClient

import requests

client = MongoClient()
db = client.catchupdb
chats = db.chats
app = Flask(__name__)
cors = CORS(app)

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/plus.me']
API_SERVICE_NAME = 'calendar'
API_VERSION = 'v3'

app.secret_key = '\xf5,\xd3uH=\xb4\rS\xa7\x16\xbf\x14\xb5A0\xca\n{\x1e\xf1J1~'
CLIENT_SECRETS_FILE = "client_secret.json"
SEND_API_URL = "https://graph.facebook.com/v2.6/me/messages?access_token=EAAE9HFOuWMkBABlZC3IArcPyCjZBSdNDuecUzNmqCXuvWdHHX17G8NzjGRpnRvgsBpEAnpmEhWtPCZArvkI0C45DQYnxZAReOhP1dL2LNZClBWeRUdoZAnnNUFcYqnZBsGnnoTFMhhW4UNYq8ah9BfYOvzO2giWmzZAavLG4ZBHWHagZDZD"


@app.route('/')
def index():
    resp = make_response(render_template('index.html'))
    resp.headers['X-FRAME-OPTIONS'] = "ALLOW-FROM https://www.messenger.com/"
    resp.headers['X-FRAME-OPTIONS'] = "ALLOW-FROM https://www.facebook.com/"
    return resp


@app.route('/testing', methods=['GET', 'POST'])
def testing():
    req_json = request.get_json()
    flask.session['chat_id'] = req_json['tid']
    print(req_json)
    return ('got data')

@app.route('/getchat')
def getchat():
    chat_id = request.args.get('id')
    creds = chats.find_one(filter = {'chat_id': chat_id})
    if creds == None:
        resp = {"credentials": "NONE"}
        return jsonify(resp)
    return jsonify(dumps(creds))

@app.route('/storechat', methods=['GET', 'POST'])
def storechat():
    req_json = request.get_json()
    tid = req_json['chat_id']
    credential = {'chat_id': tid, 'credentials': []}
    chats.insert_one(credential)
    return 'Stored!'

def updatechat(tid, email):
    chat_data = chats.find_one(filter = {'chat_id': tid})
    credential = chat_data['credentials']
    credential.append(email)
    print(credential)
    chats.update_one({
        'chat_id': tid,
    }, {
        '$set':
        {
            'credentials': credential
        }
    })
    return "UPDATED"


@app.route('/pickevent')
def pickevent():
    resp = make_response(render_template('pick_event.html'))
    resp.headers['X-FRAME-OPTIONS'] = "ALLOW-FROM https://www.messenger.com/"
    resp.headers['X-FRAME-OPTIONS'] = "ALLOW-FROM https://www.facebook.com/"
    return resp 
    


@app.route('/test')
def test_api_request():
    if 'credentials' not in flask.session:
        return flask.redirect('authorize')

    # Load credentials from the session.
    credentials = google.oauth2.credentials.Credentials(
        **flask.session['credentials'])

    service = googleapiclient.discovery.build(
        API_SERVICE_NAME, API_VERSION, credentials=credentials)

    user_info_service = googleapiclient.discovery.build(
        'plus', 'v1', credentials=credentials)

    user_info = user_info_service.people().get(userId='me').execute()
    user_email = user_info['emails'][0]['value']
    flask.session['user_email'] = user_email
    chat_id = request.args.get('chatid')
    if chat_id is not None:
        tid = request.get_json()['chatid']
        updatechat(tid, user_email)

    utc_now = datetime.datetime.utcnow()
    now = utc_now.isoformat() + 'Z'  # 'Z' indicates UTC time
    utc_nxt = utc_now + datetime.timedelta(days=7)
    nxt = utc_nxt.isoformat() + 'Z'

    freebusy_result = service.freebusy().query(body={
        'timeMax': nxt,
        'timeMin': now,
        'items': [
            {'id': user_email}
        ]
    }).execute()

    freebusy = freebusy_result.get('calendars', [])
    print(freebusy)

    # Save credentials back to session in case access token was refreshed.
    # ACTION ITEM: In a production app, you likely want to save these
    #              credentials in a persistent database instead.
    flask.session['credentials'] = credentials_to_dict(credentials)

    resp = make_response(render_template('share_auth.html'))
    resp.headers['X-FRAME-OPTIONS'] = "ALLOW-FROM https://www.messenger.com/"
    resp.headers['X-FRAME-OPTIONS'] = "ALLOW-FROM https://www.facebook.com/"


    return resp


@app.route('/authorize')
def authorize():
    # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES)

    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

    authorization_url, state = flow.authorization_url(
        access_type='offline', include_granted_scopes='true')

    # Store the state so the callback can verify the auth server response.
    flask.session['state'] = state
    resp = make_response(flask.redirect(authorization_url))
    resp.headers['X-FRAME-OPTIONS'] = "ALLOW-FROM https://www.messenger.com/"
    resp.headers['X-FRAME-OPTIONS'] = "ALLOW-FROM https://www.facebook.com/"

    return resp


@app.route('/oauth2callback')
def oauth2callback():
    # Specify the state when creating the flow in the callback so that it can
    # verified in the authorization server response.
    state = flask.session['state']

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    authorization_response = flask.request.url
    flow.fetch_token(authorization_response=authorization_response)

    # Store credentials in the session.
    # ACTION ITEM: In a production app, you likely want to save these
    credentials = flow.credentials

    flask.session['credentials'] = credentials_to_dict(credentials)

    return flask.redirect(flask.url_for('test_api_request'))


def credentials_to_dict(credentials):
    return {'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes}


@app.route('/fbwebhook', methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        return get_webhook()
    elif request.method == "POST":
        return post_webhook()
    return 'Unexpected response'

def get_free_slots(credentials, group_emails, time):
    for email in group_emails:
        pass


def get_webhook():
    VERIFY_TOKEN = "serg_squad"

    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    if mode == 'subscribe' and token == VERIFY_TOKEN:
        return challenge
    else:
        return 'Fail!', 403


def post_webhook():
    req_json = request.get_json()
    user_id = req_json['entry'][0]['messaging'][0]['sender']['id']

    send_msg = {
        "messaging_type": "RESPONSE",
        "recipient": {
            "id": user_id
        },
        "message": {
            "attachment":
                {
                    "type": "template",
                    "payload": {
                        "template_type": "button",
                        "text": "OK, let's start socializing again!",
                        "buttons": [{
                            "type": "web_url",
                            "url": "https://catchupbot.com/test",
                            "title": "Set preferences",
                            "webview_height_ratio": "compact",
                            "messenger_extensions": True
                        }]
                    }
                }
        }
    }

    r = requests.post(SEND_API_URL, json=send_msg)

    print(r.status_code)

    return "Received!"


def send_message(id, message):
    send_msg = {
        "messaging_type": "RESPONSE",
        "recipient": {
            "id": id
        },
        "message": message
    }
    r = requests.post(SEND_API_URL, json=send_msg)

    print(r.status_code)


if __name__ == "__main__":
    # TODO REMOVE ON REAL APPLICATION
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

    app.run(host="https://www.catchupbot.com", port=80)
