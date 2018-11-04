from flask import Flask
from flask import request
from flask import jsonify
from flask import make_response
from flask import render_template

import requests


app = Flask(__name__)





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
    print(req_json)
    return ('got data')


@app.route('/fbwebhook', methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        return get_webhook()
    elif request.method == "POST":
        return post_webhook()
    return 'Unexpected response'


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
                    "url": "https://catchupbot.com",
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
