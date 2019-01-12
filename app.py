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
from mongoengine import connect
from user import User
from catchup import Catchup
from apiclient import discovery
import httplib2
from oauth2client import client

connect('catchupdb')
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
    user_location = dataDict['location']
    session_token = util.generate_token()
    auth_code = dataDict['auth_code']
    credentials = util.google_auth_user(auth_code)
    user_email = credentials.id_token['email']
    user_obj = User.create_user(user_email, user_location, auth_code, credentials.refresh_token, credentials.access_token)
    user_obj.session_token = session_token
    user_obj.save()
    return jsonify({'session_token': user_obj.session_token, 'user_email': user_email})

@app.route('/get_catchups', methods=['GET'])
def get_catchups():
    user_email = request.args.get('user_email')
    session_token = request.args.get('session_token')
    user_valid = util.validate_user(user_email, session_token)
    if not user_valid[0]:
        return jsonify(user_valid[1])
    user_obj = user_valid[1]
    catchups = [Catchup.objects.get(id=catchup_id).to_json() for catchup_id in user_obj.catchups]
    return jsonify({"catchups" : catchups})
    
@app.route('/sign_out', methods=['POST'])
@cross_origin()
def sign_out():
    data = request.data
    dataDict = json.loads(data)
    user_email = dataDict['user_email']
    session_token = dataDict['session_token']
    user_valid = util.validate_user(user_email, session_token)
    if not user_valid[0]:
        return jsonify(user_valid[1])
    user_obj = user_valid[1]
    user_obj.session_token = ''
    user_obj.save()
    return jsonify({'signed_out': 'success'})

@app.route('/create_catchup', methods=['POST'])
def create_catchup():
    data = request.data
    dataDict = json.loads(data)
    owner = dataDict['catchup_owner']
    session_token = dataDict['session_token']
    user_valid = util.validate_user(owner, session_token)
    if not user_valid[0]:
        return jsonify(user_valid[1])
    invited_list = dataDict['invited_list']
    title = dataDict['title']
    catchup_obj = Catchup.create_catchup(owner, invited_list, title)
    owner_obj = User.objects.get(email=owner)
    owner_obj.add_catchup(catchup_obj.id)
    for email in invited_list:
        user_obj = User.create_user(email, [-1,-1], '', '', '')
        user_obj.add_catchup(catchup_obj.id)
    return jsonify({'create_catchup': 'success'})

@app.route('/accept_catchup', methods=['POST'])
def accept_catchup():
    data = request.data
    dataDict = json.loads(data)
    user_email = dataDict['user_email']
    session_token = dataDict['session_token']
    user_valid = util.validate_user(user_email, session_token)
    if not user_valid[0]:
        return jsonify(user_valid[1])
    user_obj = user_valid[1]
    catchup_id = dataDict['catchup_id']
    catchup_obj = Catchup.objects.get(id=catchup_id)
    catchup_obj.accept_user(user_email)
    
    return jsonify({'success': 'accepted!'})

    







if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
