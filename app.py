from flask import Flask
from flask import request


app = Flask(__name__)

@app.route('/')
def index():
    return 'Hi woorld'

@app.route('/fbwebhook', methods=["GET","POST"])
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
    print(str(request.get_json()))
    return 'POST'


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
