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
    userEmail = dataDict['email']
    userLocation = dataDict['location']
    session_token = util.generate_token()
    userObj = User.create_user(userEmail, userLocation)
    userObj.session_token = session_token
    userObj.save()
    return jsonify({'session_token': session_token})

@app.route('/get_catchups', methods=['GET'])
def get_catchups():
    user_email = request.args.get('user_email')
    session_token = request.args.get('session_token')
    if not User.objects(email=user_email):
        return jsonify(util.get_error('No such user'))
    user_obj = User.objects.get(email=user_email)
    if session_token != user_obj.session_token:
        return jsonify(util.get_error('Invalid session token'))
    return jsonify({"catchups" : user_obj.catchups})
    
@app.route('/sign_out', methods=['POST'])
@cross_origin()
def sign_out():
    return ''




if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
