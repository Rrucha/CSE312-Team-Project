import { io } from "socket.io-client";

const socket = io("ws://localhost:8080")

socket.on("STU_new_question", (post_course, json) => {
    // TODO
})

socket.on("STU_stop_question", (post_course) => {

})

