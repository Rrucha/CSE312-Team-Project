from flask import Flask, render_template, redirect, url_for, request

import socketserver
from pymongo import MongoClient



mongo_client = MongoClient("mongo")
db = mongo_client["cse312"]
users_collection = db["users"]

socketserver.TCPServer.allow_reuse_address = True
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != 'admin' or request.form['password'] != 'admin':
            error = 'Invalid Credentials. Please try again.'
        else:
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

#users_collection.insert_one({'username': , 'password': })