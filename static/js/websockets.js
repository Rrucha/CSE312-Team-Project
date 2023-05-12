import { io } from "https://cdn.socket.io/4.3.2/socket.io.esm.min.js";

const socket = io("http://localhost:8080/")

const course_id = document.getElementById("course-code").innerHTML

socket.on("new_question", (json) => {
    // Check if this connection is the instructor. If so, ignore.
    // TODO: maybe use cookies? Set the course-code and is-instructor cookies so we can get them here in JS.
    // TODO
    console.log("question received!")
    const question = JSON.parse(json);
    document.getElementById("question_form").disabled = false
    document.getElementById("question_form").style.visibility = 'visible'
    document.getElementById("q_question").innerHTML = question['question']
    document.getElementById("q_a1").innerHTML = question['answers'][0]
    document.getElementById("q_a2").innerHTML = question['answers'][1]
    document.getElementById("q_a3").innerHTML = question['answers'][2]
    document.getElementById("q_a4").innerHTML = question['answers'][3]
    // console.log("Question: " + question['question'] + "Answer: " + question['correct'] + "Answers: " + question['answers'][0] + question['answers'][1])
    // document.getElementById("slide-content").innerHTML = "Question: " + question['question'] + "Answer: " + question['correct'] + "Answers: " + question['answers'][0] + question['answers'][1]
})

socket.on("STU_stop_question", (post_course) => {

})

socket.on("connect", () => {
    // After receiving a response, ask to join the WS room for the course.
    socket.emit("join_room", course_id)
})