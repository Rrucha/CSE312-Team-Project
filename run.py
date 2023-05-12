import uuid
from ast import Pass
import json
from urllib.parse import uses_query

from flask import Flask, render_template, redirect, url_for, request, session, make_response, Response, \
    send_from_directory
from flask_socketio import SocketIO, emit, join_room
import socketserver
from pymongo import MongoClient
import bcrypt
import secrets

app = Flask(__name__)
app_ws = SocketIO(app)

MONGO_HOST = "mongo"
MONGO_PORT = 27017
mongo_client = MongoClient(MONGO_HOST, MONGO_PORT)
db = mongo_client["TOPHAT_SITEDATA"]
users_collection = db["users"]
courses_collection = db["courses"]


def enrolled_courses(user):
    try:
        # enrolled_codes = users_collection.find({'username': user})[0]['enrolled']
        # enrolled = []
        # for i in enrolled_codes:
        # try:
        #     enrolled += courses_collection.find({'code': i})
        # except:
        #     pass
        enrolled_codes = users_collection.find_one({'username': user}).get('enrolled',
                                                                           [])  # Get the 'enrolled' field or an empty list if it doesn't exist
        enrolled = []
        for i in enrolled_codes:
            try:
                enrolled += courses_collection.find({'code': i})
            except:
                pass
    except:
        enrolled = []
    return enrolled


def created_courses(user):
    created = [i for i in courses_collection.find({'instructor': user})]
    # print('created_courses', created)
    return created


socketserver.TCPServer.allow_reuse_address = True


@app.route("/login", methods=["POST", "GET"])  # login system is cookie based
def login():
    error = None

    if request.cookies.get("user"):
        return redirect("/homepage")

    if request.method == "POST":
        # user = request.form["user"]
        # user_type = request.form["user_type"]

        # user = request.form['user']
        # password = request.form['password']
        # login = False
        # for row in users:
        #     if user == row['user'] and password == row['password']:
        #         login = True
        #         break
        # try:
        #     users_collection.find({'user': user})[0]['enrolled']
        # except:
        #     users_collection.insert_one({
        #         'user': user,
        #         'password': password,
        #         'enrolled': [],
        #         'created': []})
        # login = True  # temp allow all user to login
        # if request.form['user'] == '' or password == '':
        #     res = redirect(url_for('homepage'))
        #     res.set_cookie("user", user)
        # elif login:
        #     res = redirect(url_for('homepage'))
        #     res.set_cookie("user", user)
        # else:
        #     res = redirect(url_for('login'))
        #     res.set_cookie("user", user)

        username = request.form['user']
        password = request.form['password']

        print("user", username)
        print("pass", password)

        document = users_collection.find_one({"username": username})
        if document is not None:
            saved_hash = document["password"]
            hashes_match = bcrypt.checkpw(password.encode(), saved_hash)
            if hashes_match:
                # TODO: generate authentication token
                auth_token = secrets.token_hex(16)  # Generate a 128-bit random token (32 characters)

                # TODO: save auth-token, set username, auth-token cookies
                save_auth_token = {"$set": {'auth_token': auth_token}}
                users_collection.update_one({"username": username}, save_auth_token)

                response = make_response(redirect("/homepage"))
                response.set_cookie('user', username)
                response.set_cookie('auth_token', auth_token, max_age=3600)

                return response
            else:
                msg = ' The username/password is incorrect. '
                return render_template("login.html", msg=msg)
        else:
            msg = ' Username not found! Register an account first. '
            return render_template("login.html", msg=msg)

    return render_template("login.html", error=error)


@app.route("/websockets.js")
def websockets_js():
    return send_from_directory('static', 'js/websockets.js')


@app.route("/functions.js")
def functions_js():
    return send_from_directory('static', 'js/functions.js')


@app.route("/create_course", methods=["POST", "GET"])  # create a new auction by the seller
def create_course():
    print("create_course")
    error = None
    user = request.cookies.get("user")
    if not user:
        return redirect("/login")
    if request.method == "POST":
        code = request.form["code"]
        code_match = [i for i in courses_collection.find({'code': code})]
        print(code_match)
        if code_match:
            error = "code already exists"
        else:
            inserted_course = courses_collection.insert_one({
                'title': request.form["title"],
                'description': request.form["description"],
                'code': code,
                'instructor': user})
            # if inserted_course.acknowledged:
            #     return 

            return redirect(f"/course/{code}")
    return render_template("create_course.html", user=user, error=error)


@app.route("/join_course", methods=["POST", "GET"])  # create a new auction by the seller
def join_course():
    error = None
    user = request.cookies.get("user")
    if not user:
        return redirect("/login")
    try:
        code = request.args.get('code')
    except:
        code = None
    if request.method == "POST" and not code:
        code = request.form["code"]
    code_match = [i for i in courses_collection.find({'code': code})]
    # except:
    #     code_match = False

    if code_match:  # if course code exist
        print(1111111111111, code_match, code, user)

        # enrolled_codes = users_collection.find({'username': user})[0]['enrolled']
        user_info = users_collection.find_one({'username': user})
        # print("User info: ", user_info)
        enrolled_codes = user_info.get('enrolled', [])  # Get the 'enrolled' field or an empty list if it doesn't exist

        if code not in enrolled_codes:
            enrolled_codes.append(code)
            users_collection.update_one({'username': user}, {'$set': {'enrolled': enrolled_codes}})
            # user_info =  users_collection.find_one({'username': user})
            # print("User info: ", user_info)
        return redirect(f"/course/{code}")
    else:
        error = "code does not exists"

    return render_template("join_course.html", user=user, error=error)


@app.route("/course/<code>", methods=["GET"])
def enter_course(code):
    # Ask user to log in first if not already logged in
    user = request.cookies.get("user")
    if not user:
        return redirect("/login")

    # Search for a course that matches the code. If found, and the user is in the course, serve the course page.
    code_match = [i for i in courses_collection.find({'code': code})]
    if code_match:
        course = code_match[0]
        is_instructor = course['instructor'] == request.cookies.get("user")
        if course in enrolled_courses(user) or course in created_courses(user):
            response = make_response(render_template("content.html",
                                                     user=user,
                                                     hide_sidebar=True,
                                                     course_nav=True,
                                                     error=None,
                                                     course=course,
                                                     is_instructor=is_instructor))
            response.set_cookie("course-code", code)
            return response
        return render_template("course.html", user=user, error=None, course=course)

    # else:
    #     inserted_course = courses_collection.insert_one({
    #         'title':request.form["title"],
    #         'description':request.form["description"], 
    #         'code':code, 
    #         'instructor':user})
    #     # if inserted_course.acknowledged:
    #     #     return 

    # return redirect(f"/course/{code}")
    return render_template("homepage.html")


@app.route('/courseslist')
def courseslist():
    error = ""
    user = request.cookies.get("user")
    if not user:
        return redirect("/login")
    return render_template("courses.html", user=user, enrolled=enrolled_courses(user),
                           created_courses=created_courses(user))


@app.route('/homepage', methods=["GET"])
def homepage():
    error = None
    user = request.cookies.get("user")
    if not user:
        print("no user found")
        return redirect("/login")
    else:
        print("user found and will render hompage.html")
    return render_template(
        "homepage.html", user=user, courses=[i for i in courses_collection.find()]
    )


@app.route("/register", methods=["POST", "GET"])  # register system to login
def register():
    print("text")

    error = None
    if request.cookies.get("user"):
        return redirect("/homepage")
    if request.method == "POST":
        username = request.form['user']
        password = request.form['password']
        print("user", username)
        print("pass", password)

        if users_collection.find_one({"username": username}):
            error = 'Username already taken.'
            return render_template("register.html", error=error)

        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode(), salt)
        users_collection.insert_one({"username": username, "password": hashed_password})

        msg = 'You have successfully registered !'

        return render_template("login.html", msg=msg)
    else:
        return render_template("register.html", error=error)


@app.route("/logout", methods=["POST", "GET"])  # logout by deleting the cookie
def logout():
    print("logout")
    error = None
    res = make_response(render_template("login.html", error=error))
    res.set_cookie("user", "", expires=0)
    return res


@app.route('/', methods=['GET', 'POST'])
def index():
    return redirect('/login')


@app_ws.on('join_room')
def ws_join_room(course_code):
    # Fired by clients after they receive a connection response.
    # Place the sender into the desired room.
    join_room(course_code)


# @app_ws.on('post_question')
# def post_question(course_code, question_data):
#     # Fired by instructors when they press "Post Question"
#     # emit new question to all students in the course room.
#     # question_data is a dict holding all the necessary info for the question.
#     emit('new_question', question_data, to=course_code)


@app_ws.on('stop_question')
def stop_question(course_code, question_id):
    # Fired by instructors when they press the "Stop Question" button
    # Receive it, then send it to all students. Students
    emit('stop_question', question_id, to=course_code)


@app.route('/answer-question', methods=['POST'])
def answer_question():
    return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}


# Instructors should have access to a question form which sends an HTTP multipart request
@app.route('/post-question', methods=['POST'])
def HTTP_post_question():
    course_dict = {
        "course": request.form['course'],
        "question": request.form['question'],
        "answers": [
            request.form['a1'],
            request.form['a2'],
            request.form['a3'],
            request.form['a4']
        ],
        "correct": request.form['correct-answer']  # character a, b, c, or d
    }

    # TODO
    json_str = json.dumps(course_dict)
    # Add the question to the database.
    app_ws.emit('new_question', json_str, to=request.cookies.get("course-code"))
    return redirect("/course/" + request.cookies.get("course-code"))


if __name__ == "__main__":
    app_ws.run(app, host='0.0.0.0', port=8000)
