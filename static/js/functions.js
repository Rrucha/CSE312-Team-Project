import { io } from "https://cdn.socket.io/4.3.2/socket.io.esm.min.js";

export const socket = io("http://localhost:8080/")

const course_id = document.getElementById("course-code").innerHTML

socket.on("new_question", (json) => {
    console.log("question received!")
    const question = JSON.parse(json);
    document.getElementById("q_question").innerHTML = question['question']
    document.getElementById("q_a1").innerHTML = question['answers'][0]
    document.getElementById("q_a2").innerHTML = question['answers'][1]
    document.getElementById("q_a3").innerHTML = question['answers'][2]
    document.getElementById("q_a4").innerHTML = question['answers'][3]
    document.getElementById("question_form").style.visibility = 'visible'

    var choices = document.getElementsByName("q_choice");
    for (var i = 0; i < choices.length; i++) {
        choices[i].disabled = false;
        choices[i].checked = false;
    }

    // console.log("Question: " + question['question'] + "Answer: " + question['correct'] + "Answers: " + question['answers'][0] + question['answers'][1])
    // document.getElementById("slide-content").innerHTML = "Question: " + question['question'] + "Answer: " + question['correct'] + "Answers: " + question['answers'][0] + question['answers'][1]
})

socket.on("stop_question", () => {
    // TODO: modify the HTML to disable the question, regardless of whether or not it was answered.
    document.getElementById("question_form").style.visibility = 'hidden'

    console.log("question stopped!")
})

socket.on("connect", () => {
    // After receiving a response (completing the handshake), ask to join the WS room for the course.
    socket.emit("join_room", course_id);
})

function answerQuestion() {
    console.log("Question answered");

    // Disable the question after submission. Get the selected answer.
    var choices = document.getElementsByName("q_choice");
    var answer = "";
    for (var i = 0; i < choices.length; i++) {
        choices[i].disabled = true;
        if (choices[i].checked) {
            answer = choices[i].value;
        }
    }
    // console.log("Choices: " + document.getElementsByName("q_choice").length);


    socket.emit("answer_question", course_id, getCookie("user"), answer);
}

document.getElementById("q_button").addEventListener("click", answerQuestion);

//function stopQuestion() {
//    console.log("Stopping question.");
//
//    socket.emit("stop_question", course_id);
//}

// document.getElementById("stop_question").addEventListener("click", stopQuestion);

var radio_btns = document.getElementsByName("cq_rad");
for (var i = 0; i < radio_btns.length; i++) {
    radio_btns[i].addEventListener("change", function() {
        document.getElementById("save-question").disabled = false;
    });
}

function getQuestion() {
    // console.log(getCookie("user"));

    var request = new XMLHttpRequest();
    request.onreadystatechange = function() {
        if (this.readyState === 4 && this.status === 200) {
            console.log(this.responseText)

            if (this.responseText != "{}") {
                const responseJSON = JSON.parse(this.responseText)

                document.getElementById("q_question").innerHTML = responseJSON['question']
                document.getElementById("q_a1").innerHTML = responseJSON['answers'][0]
                document.getElementById("q_a2").innerHTML = responseJSON['answers'][1]
                document.getElementById("q_a3").innerHTML = responseJSON['answers'][2]
                document.getElementById("q_a4").innerHTML = responseJSON['answers'][3]

                // If already answered, disable all fields.
                if (responseJSON['answer'] != "") {
                    var choices = document.getElementsByName("q_choice");
                    for (var i = 0; i < choices.length; i++) {
                        choices[i].disabled = true;
                        if (responseJSON['answer'] == choices[i].value) {
                            choices[i].checked = true;
                        }
                    }
                }

                document.getElementById("question_form").style.visibility = 'visible'
            }
        }
    };
    request.open("GET", "/current-question/" + course_id);
    request.send();
}

document.getElementById("javascript").addEventListener("load", getQuestion);

function getCookie(cookie) {
    console.log(document.cookie);
    var cookie_split = document.cookie.split(/; ?/)
    for (var i = 0; i < cookie_split.length; i++) {
        var kv = cookie_split[i].split('=');
        if (kv[0] == cookie) {
            return kv[1];
        }
    }

    return null;
}