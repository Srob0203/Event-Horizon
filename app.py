from bson.objectid import ObjectId
from flask import Flask, render_template, request, session, url_for, redirect
from datetime import datetime
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo import MongoClient
import json
from os import environ as env
from urllib.parse import quote_plus, urlencode
from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from functools import wraps

app = Flask(__name__)
app.secret_key = env.get("APP_SECRET_KEY")
ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

uri = "mongodb+srv://MinhPhu:LjG3SbftvdS9aCBW@cluster0.w0tqvvf.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(uri, server_api=ServerApi('1'))
# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

db = client.flask_db
todos = db.todos
events = db.events
courses = db.courses
def requires_auth(f):
    """
    Use on routes that require a valid session, otherwise it aborts with a 403
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('user') is None:
            return redirect(url_for('auth.login'))

        return f(*args, **kwargs)

    return decorated

oauth = OAuth(app)

oauth.register("auth0", client_id=env.get("AUTH0_CLIENT_ID"), client_secret=env.get("AUTH0_CLIENT_SECRET"), client_kwargs={
    "scope": "openid profile email",}, server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration')

@app.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
            redirect_uri=url_for("callback", _external=True)
            )

@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    session["user"] = token
    return redirect("/todo")
@app.route("/logout")
def logout():
    session.clear()
    return redirect(
            "https://" + env.get("AUTH0_DOMAIN")
            + "/v2/logout?"
            + urlencode(
                {
                    "returnTo": url_for("home", _external=True),
                    "client_id": env.get("AUTH0_CLIENT_ID"),
                    },
                quote_via=quote_plus,
                )
            )
@app.route("/")
def home():
    return render_template('design.html')

@app.route('/todo', methods=['GET', 'POST'])
@requires_auth
def todo():
    if request.method=='POST':
        course_code = request.form['course_code']
        course_name = request.form['course_name']
        course_section = request.form['course_section']
        crn = request.form['crn']
        building = request.form['building']
        room = request.form['room']
        class_name = request.form['class_name']
        todos.insert_one({'course_code': course_code, 
    'course_name': course_name,
    'course_section': course_section,
    'crn': crn,
    'room': room,
    'building': building,
    'class_name':class_name
    })
        return redirect(url_for('todo'))

    all_todos=todos.find().sort({'course_code':1})
    return render_template('course.html',todos=all_todos)

@app.post('/todo/<id>/delete/')
def delete(id):
    courses.delete_one({"_id": ObjectId(id)})
    return redirect(url_for('todo'))