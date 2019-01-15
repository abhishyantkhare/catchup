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
from stored_event import StoredEvent
from apscheduler.schedulers.background import BackgroundScheduler


connect('catchupdb')
app = Flask(__name__)
cors = CORS(app)

# Start the scheduler
sched = BackgroundScheduler()
sched.start()



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
    catchup_obj.save()
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
    catchup_obj.accept_user(user_email, sched)

    
    return jsonify({'success': 'accepted!'})

@app.route('/deny_catchup', methods=['POST'])
def deny_catchup():
    data = request.data
    dataDict = json.loads(data)
    user_email = dataDict['user_email']
    session_token = dataDict['session_token']
    user_valid = util.validate_user(user_email, session_token)
    if not user_valid[0]:
        return jsonify(user_valid[1])
    user_obj=user_valid[1]
    catchup_id = dataDict['catchup_id']
    catchup_obj = Catchup.objects.get(id=catchup_id)
    catchup_obj.deny_user(user_email)

    return jsonify({'success': 'denied!'})

@app.route('/add_stored_event', methods=['POST'])
def add_stored_event():
    data = request.data
    dataDict = json.loads(data)
    event_name = dataDict['event_name']
    preferred_times = dataDict['preferred_times']
    yelp_event = dataDict['yelp_event']
    event_duration = float(dataDict['event_duration'])
    StoredEvent.create_stored_event(event_name, preferred_times, yelp_event, event_duration)

    return jsonify({'success': 'added_event'})

@app.route('/update_catchup', methods=['POST'])
def update_event():
    data = request.data
    dataDict = json.loads(data)
    user_email = dataDict['user_email']
    session_token = dataDict['session_token']
    user_valid = util.validate_user(user_email, session_token)
    if not user_valid[0]:
        return jsonify(user_valid[1]) 
    catchup = dataDict['catchup']
    catchup_id = catchup['_id']['$oid']
    catchup_obj = Catchup.objects.get(id=catchup_id)
    if user_email != catchup_obj.catchup_owner:
        return jsonify(util.get_error('Invalid permissions'))
    catchup_obj.catchup_title=catchup['catchup_title']
    catchup_obj.compare_accepted_users(catchup['accepted_users'])
    catchup_obj.accepted_users = catchup['accepted_users']
    catchup_obj.new_invite_users(catchup['invited_users'])
    catchup_obj.compare_invited_users(catchup['invited_users'])
    catchup_obj.invited_users = catchup['invited_users']
    catchup_obj.frequency = catchup['frequency']
    if 'current_event' in  catchup:
        current_event = catchup['current_event']
        catchup_obj.current_event.event_name = current_event['event_name']
        catchup_obj.current_event.event_start_time = current_event['event_start_time']
        catchup_obj.current_event.event_end_time = current_event['event_end_time']
        catchup_obj.current_event.event_location = current_event['event_location']
        catchup_obj.current_event.event_duration = current_event['event_duration']
    catchup_obj.save()
    print(catchup_obj)
    return jsonify({'success': 'updated catchup!'})

@app.route('/delete_catchup', methods=['POST'])
def delete_catchup():
    data = request.data
    dataDict = json.loads(data)
    user_email = dataDict['user_email']
    session_token = dataDict['session_token']
    user_valid = util.validate_user(user_email, session_token)
    if not user_valid[0]:
        return jsonify(user_valid[1]) 
    catchup = dataDict['catchup'] 
    catchup_obj = Catchup.objects.get(id=catchup['_id']['$oid'])
    if user_email != catchup_obj.catchup_owner:
        return jsonify(util.get_error('Invalid permissions'))
    owner_obj = User.objects.get(email=catchup_obj.catchup_owner)
    owner_obj.remove_catchup(catchup_obj.id)
    for user in catchup_obj.accepted_users:
        user_obj = User.objects.get(email=user)
        user_obj.remove_catchup(catchup_obj.id)
    for user in catchup_obj.invited_users:
        user_obj = User.objects.get(email=user)
        user_obj.remove_catchup(catchup_obj.id)
    return jsonify({'success': 'deleted catchup'})

@app.route('/leave_catchup', methods=['POST'])
def leave_catchup():
    data = request.data
    dataDict = json.loads(data)
    user_email = dataDict['user_email']
    session_token = dataDict['session_token']
    user_valid = util.validate_user(user_email, session_token)
    if not user_valid[0]:
        return jsonify(user_valid[1]) 
    catchup = dataDict['catchup'] 
    catchup_obj = Catchup.objects.get(id=catchup['_id']['$oid']) 
    user_obj = User.objects.get(email=user_email)
    user_obj.remove_catchup(catchup_obj.id)
    if user_email in catchup_obj.accepted_users:
        catchup_obj.accepted_users.remove(user_email)
        catchup_obj.save()
    return jsonify({'success': 'left catchup'})


    







if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
