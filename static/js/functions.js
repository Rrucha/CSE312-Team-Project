import { io } from "https://cdn.socket.io/4.3.2/socket.io.esm.min.js";

const socket = io("http://localhost:8080/")

const course_id = document.getElementById("course-code").innerHTML

socket.on("new_question", (json) => {
    // Check if this connection is the instructor. If so, ignore.
    // TODO
})

socket.on("STU_stop_question", (post_course) => {

})

socket.on("connect", () => {
    // After receiving a response, ask to join the WS room for the course.
    socket.emit("join_room", course_id)
})