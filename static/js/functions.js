function answerQuestion() {
    console.log("Question answered")

    choices = document.getElementsByName("q_choice")
    for (var i = 0; i < choices.length; i++) {
        choices[i].disabled = true
    }
    console.log("Choices: " + document.getElementsByName("q_choice").length)

    var request = new XMLHttpRequest();
    request.onreadystatechange = function() {
        if (this.readyState === 4 && this.status === 200) { }
    };
    request.open("POST", "/answer-question");
    request.send();
}