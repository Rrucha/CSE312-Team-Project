import socketserver
import os
import json
import secrets
import hashlib
import base64
import random
from pymongo import MongoClient
from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def hello():
    return render_template('login.html')

@app.route("/login")
def login():
    score = 100
    return render_template('login.html', score = score)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)

def func():
    return None