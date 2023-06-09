import uuid
from ast import Pass
import json
from urllib.parse import uses_query
import html
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
site_db = mongo_client["TOPHAT_SITEDATA"]
users_collection = site_db["users"]
courses_collection = site_db["courses"]


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


def enrolled_students(code):
    users = []
    for user in users_collection.find():
        if code in user['enrolled']:
            users.append(user)
        return users


def created_courses(user):
    created = [i for i in courses_collection.find({'instructor': user})]
    # print('created_courses', created)
    return created


socketserver.TCPServer.allow_reuse_address = True


@app.route('/', methods=['GET', 'POST'])
def index():
    return redirect('/login')


@app.route("/login", methods=["POST", "GET"])  # login system is cookie based
def login():
    error = None

    if request.cookies.get("user"):
        return redirect("/homepage")

    if request.method == "POST":
        username = request.form['user']
        username = html.escape(username)
        password = request.form['password']
        password = html.escape(password)

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
        code = html.escape(code)
        code_match = [i for i in courses_collection.find({'code': code})]
        print(code_match)
        if code_match:
            error = "code already exists"
        else:
            title = request.form["title"]
            title = html.escape(title)
            describ = request.form["description"]
            describ = html.escape(describ)
            courses_collection.insert_one({
                'title': title,
                'description': describ,
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
    course_doc = courses_collection.find_one({'code': code})
    # except:
    #     code_match = False

    if course_doc:  # if course code exist
        print(1111111111111, course_doc, code, user)

        # add the course to the user's enrolled courses
        user_info = users_collection.find_one({'username': user})
        enrolled_codes = user_info.get('enrolled', [])  # Get the 'enrolled' field or an empty list if it doesn't exist

        if code not in enrolled_codes and user != course_doc['instructor']:
            enrolled_codes.append(code)
            users_collection.update_one({'username': user}, {'$set': {'enrolled': enrolled_codes}})
            # user_info =  users_collection.find_one({'username': user})
            # print("User info: ", user_info)

            # Add the use to the course's enrolled students.
            course_db = mongo_client[code]
            stu_coll = course_db['students']
            stu_coll.insert_one({
                "username": user,
                "scores": []
            })

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

        q_coll = mongo_client[code]['questions']
        is_question_active = len([i for i in q_coll.find({'active': 'true'})]) > 0

        if course in enrolled_courses(user) or course in created_courses(user):
            response = make_response(render_template("content.html",
                                                     user=user,
                                                     hide_sidebar=True,
                                                     course_nav=True,
                                                     error=None,
                                                     course=course,
                                                     is_instructor=is_instructor,
                                                     is_question_active=is_question_active))
            response.set_cookie("course-code", code)  # TODO: remove?
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


def get_average(scores):
    total = 0
    for i in scores:
        total += i

    return total / len(scores)


@app.route('/gradebook/<code>')
def gradebook(code):
    print("User is now in gradebook")
    user = request.cookies.get("user")
    if not user:
        return redirect("/login")

    # Search for a course that matches the code. If found, and the user is in the course, serve the course page.
    code_match = [i for i in courses_collection.find({'code': code})]
    if code_match:
        course = code_match[0]

        stu_dict = {}
        for s in [i for i in mongo_client[course['code']]['students'].find({})]:
            stu_dict.update({s['username']: str(round(round(get_average(s['scores']), 2) * 100)) + "%"})

        print(stu_dict)

        stu_scores = []
        s = mongo_client[course['code']]['students'].find_one({"username": user})
        if s is not None:
            stu_scores = s['scores']

        is_instructor = course['instructor'] == request.cookies.get("user")

        if course in enrolled_courses(user) or course in created_courses(user):
            return render_template('gradebook.html', code=code,
                                   user=user,
                                   course=course,
                                   is_instructor=is_instructor,
                                   stu_dict=stu_dict,
                                   scores=stu_scores)

    return render_template("homepage.html")


@app.route('/courseslist', methods=["GET"])
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
        print("user found and will render homepage.html")
    return render_template(
        "homepage.html", user=user, courses=[i for i in courses_collection.find()]
    )


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


# @app_ws.on('FROMINS_stop_question')
# def stop_question(course_code):
#     # Fired by instructors when they press the "Stop Question" button
#     # Receive it, then send it to all students.
#
#
#
#     emit('TOSTU_stop_question', to=course_code)


@app_ws.on('answer_question')
def answer_question(course, user, answer):
    # Fired by students when they press the "Submit" button on an active question.
    # Save their answer to the course's "answers" collection.
    print(course, user, answer)
    mongo_client[course]['current-answers'].insert_one({
        "username": user,
        "answer": answer
    })


@app.route('/current-question/<code>')
def get_current_question(code):
    # print(code)

    course_db = mongo_client[code]

    answer = ""
    answer_doc = course_db['current-answers'].find_one({'username': request.cookies.get("user")})
    if answer_doc is not None:
        answer = answer_doc['answer']

    is_instructor = "false"
    course = courses_collection.find_one({'code': code})
    if course is not None and course['instructor'] == request.cookies.get("user"):
        is_instructor = "true"

    if answer_doc is not None:
        answer = answer_doc['answer']

    q_dict = {}
    active_question = course_db['questions'].find_one({'active': 'true'})

    if active_question:
        q_dict = {
            "answer": answer,
            "is_instructor": is_instructor,
            "question": active_question['question'],
            "answers": active_question['answers']
        }

    return json.dumps(q_dict), 200, {'ContentType': 'application/json'}


# Instructors should have access to a question form which sends an HTTP multipart request
@app.route('/post-question', methods=['POST'])
def post_question():
    answer = request.form['cq_rad']

    course_dict = {
        "active": "true",
        "question": html.escape(request.form['question']),
        "answers": [
            html.escape(request.form['a1']),
            html.escape(request.form['a2']),
            html.escape(request.form['a3']),
            html.escape(request.form['a4'])
        ],
        "correct": answer  # character 0, 1, 2, or 3
    }

    json_str = json.dumps(course_dict)

    # Add the question to the "questions" collection, and reset the "answers" collection.
    course_code = request.form['course-code']
    course_db = mongo_client[course_code]

    questions_coll = course_db['questions']
    questions_coll.insert_one(course_dict)

    course_db['current-answers'].drop()

    # Send the question to all students, and then reload the page for the instructor.
    app_ws.emit('new_question', json_str, to=course_code)
    return redirect("/course/" + course_code)


@app.route('/stop-question', methods=['POST'])
def stop_question():
    # Deactivates the question, grades all students, and redirects the instructor back to the course homepage.
    # TODO: set the current question's "active" element to false.
    # TODO: iterate through current answers collection, updating all students' grades.

    course_code = request.form['course-code']
    course_db = mongo_client[course_code]
    q_coll = course_db['questions']

    question = q_coll.find_one({'active': 'true'})
    q_coll.update_one({'active': 'true'}, {"$set": {'active': 'false'}})

    if question is None:
        return None  # This should never happen but who knows

    app_ws.emit('stop_question', to=course_code)

    # iterate through all students
    students = [i for i in course_db['students'].find({})]
    correct = question['correct']

    for s in students:
        print(s['username'])
        # if they have a recorded answer (current-answers), and the answer is correct, append a 1.
        answer = course_db['current-answers'].find_one({"username": s['username']})
        stu_scores = s['scores']
        if answer is not None and answer['answer'] == correct:
            print(s['username'], s['scores'], answer['answer'], correct)
            stu_scores.append(1)
        else:
            stu_scores.append(0)
        course_db['students'].update_one({'username': s['username']}, {"$set": {'scores': stu_scores}})

    return redirect("/course/" + course_code)


if __name__ == "__main__":
    # Before startup, delete all questions that were active before the "crash" (server shutdown)
    courses = [i for i in courses_collection.find({})]
    for c in courses:
        c_db = mongo_client[c['code']]['questions']
        c_db.delete_many({'active': 'true'})

    app_ws.run(app, host='0.0.0.0', port=8000)
