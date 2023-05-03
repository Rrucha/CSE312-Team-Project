from flask import Flask, render_template, redirect, url_for, request, session, make_response
from flask_socketio import SocketIO, emit

import socketserver
from pymongo import MongoClient

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
        enrolled_codes = users_collection.find({'user': user})[0]['enrolled']
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

        user = request.form['user']
        password = request.form['password']
        login = False
        # for row in users:
        #     if user == row['user'] and password == row['password']:
        #         login = True
        #         break
        try:
            users_collection.find({'user': user})[0]['enrolled']
        except:
            users_collection.insert_one({
                'user': user,
                'password': password,
                'enrolled': [],
                'created': []})
        login = True  # temp allow all user to login
        if request.form['user'] == '' or password == '':
            res = redirect(url_for('homepage'))
            res.set_cookie("user", user)
        elif login:
            res = redirect(url_for('homepage'))
            res.set_cookie("user", user)
        else:
            res = redirect(url_for('login'))
            res.set_cookie("user", user)
        # return redirect(url_for('home'))

        # result = valid_login(user, request.form["password"])
        if True:
            return res
        else:
            error = "Entered User or Password were incorrect!"
    return render_template("login.html", error=error)


@app.route("/create_course", methods=["POST", "GET"])  # create a new auction by the seller
def create_course():
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

    if code_match:
        print(1111111111111, code_match, code, user)
        enrolled_codes = users_collection.find({'user': user})[0]['enrolled']
        if code not in enrolled_codes:
            enrolled_codes.append(code)
            users_collection.update_one({'user': user}, {'$set': {'enrolled': enrolled_codes}})
        return redirect(f"/course/{code}")
    else:
        error = "code does not exists"

    return render_template("join_course.html", user=user, error=error)


@app.route("/course/<code>", methods=["POST", "GET"])  # create a new auction by the seller
def course(code):
    error = None
    user = request.cookies.get("user")
    if not user:
        return redirect("/login")
    # code = request.form["code"]
    code_match = [i for i in courses_collection.find({'code':code})]
    if code_match:
        course = code_match[0]
        if course in enrolled_courses(user) or course in created_courses(user):
            return render_template("content.html", user=user, hide_sidebar=True, course_nav=True, error=error, course=course)

        return render_template("course.html", user=user, error=error, course=course)

    # else:
    #     inserted_course = courses_collection.insert_one({
    #         'title':request.form["title"],
    #         'description':request.form["description"], 
    #         'code':code, 
    #         'instructor':user})
    #     # if inserted_course.acknowledged:
    #     #     return 

    # return redirect(f"/course/{code}")
    return render_template(
        "homepage.html", user=user, error=error
    )

@app.route('/courseslist')
def courseslist():
    error = ""
    user = request.cookies.get("user")
    if not user:
        return redirect("/login")
    return render_template("courses.html", user=user, enrolled=enrolled_courses(user),
                           created_courses=created_courses(user))


@app.route('/homepage')
def homepage():
    error = None
    user = request.cookies.get("user")
    if not user:
        return redirect("/login")
    return render_template(
        "homepage.html", user=user, courses=[i for i in courses_collection.find()]
    )


@app.route("/register", methods=["POST", "GET"])  # register system to login
def register():
    error = None
    if request.cookies.get("user"):
        return redirect("/homepage")
    if request.method == "POST":
        user = request.form["user"]
        if "@" in user and "." in user:
            if found:
                error = "User already registered"
            else:
                created_user
                connection.commit()
                connection.close()
                return redirect("/login")
        else:
            error = "User not valid"
    return render_template("register.html", error=error)


@app.route("/logout", methods=["POST", "GET"])  # logout by deleting the cookie
def logout():
    error = None
    res = make_response(render_template("login.html", error=error))
    res.set_cookie("user", "", expires=0)
    return res


@app.route('/', methods=['GET', 'POST'])
def index():
    return redirect('/login')


@app_ws.on('INS_post_question')
def post_question(post_course, json):
    # emit question to all users. Use post_course to filter out students not in the course
    emit('STU_new_question', post_course, json, broadcast=True)


@app_ws.on('INS_stop_question')
def stop_question(post_course):
    emit('STU_stop_question', post_course, broadcast=True)


# Instructors should have access to a question form which sends an HTTP multipart request
@app.route('/post-question')
def HTTP_post_question():
    course = request.form["course"]
    question = request.form["question"]
    # TODO


if __name__ == "__main__":
    app_ws.run(app, host='0.0.0.0', port=8000, debug=True)
