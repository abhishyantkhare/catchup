from flask import Flask
from flask import request
from flask import jsonify
from flask import make_response
from flask import render_template
from flask_cors import CORS, cross_origin
import flask
import os
import datetime
from bson.json_util import dumps
from pymongo import MongoClient
import json
import requests
import util

client = MongoClient()
db = client.catchupdb
users = db.users
app = Flask(__name__)
cors = CORS(app)




@app.route('/')
def index():
    resp = make_response(render_template('index.html'))
    return resp

@app.route('/sign_in', methods=['POST'])
def sign_in():
    data = request.data
    dataDict = json.loads(data)
    userEmail = dataDict['email']
    userLocation = dataDict['location']
    if users.find({'email': userEmail}).count() == 0:
        users.insert_one({
                        'email': userEmail,
                        'location': {
                            'type': 'Point',
                            'coordinates': userLocation
                        }
                        })
    session_token = util.generate_token()
    users.update_one({'email': userEmail}, {'$set': {'session_token': session_token}})

    return jsonify({'session_token': session_token})

@app.route('/sign_out', methods=['POST'])
@cross_origin()
def sign_out():
    return ''




if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
