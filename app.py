from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return 'Hi woorld'

@app.route('/fbwebhook')
def webhook():
    return 'Parsing webhooks!'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
