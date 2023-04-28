from flask import Flask, render_template, redirect, url_for, request, session

import socketserver
from pymongo import MongoClient

app = Flask(__name__)

mongo_client = MongoClient("mongo")
db_siteData = mongo_client["site_data"]
db_siteData_users = db_siteData["users"]
db_siteData_courses = db_siteData["courses"]

socketserver.TCPServer.allow_reuse_address = True


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != 'admin' or request.form['password'] != 'admin':
            error = 'Invalid Credentials. Please try again.'
        else:
            session['username'] = request.form['username']
            return redirect(url_for('home'))
    return render_template('login.html', error=error)


@app.route('/home')
def home():
    return "Welcome to the home page!"


@app.route('/', methods=['GET', 'POST'])
def index():
    if 'username' in session:
        username = session['username']
        return redirect(url_for('home'))
    else:
        return redirect(url_for('login'))


@app.route('/create-join')
def create_join():
    return render_template('create_join.html')


@app.route('/create-course', methods=['POST'])
def create_course():
    entry = {"name": request.form['name'], "instructor": session['username']}

    # insert new entry into course collection
    db_siteData_courses.insert_one(entry)

    # create new database
    new_db = mongo_client[request.form['name']]


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)

# users_collection.insert_one({'username': , 'password': })
