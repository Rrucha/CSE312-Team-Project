import { io } from "https://cdn.socket.io/4.3.2/socket.io.esm.min.js";

const socket = io("http://localhost:8080/")

socket.on("STU_new_question", (post_course, json) => {
    // TODO
})

socket.on("STU_stop_question", (post_course) => {

})