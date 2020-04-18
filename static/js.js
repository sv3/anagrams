document.addEventListener('DOMContentLoaded', (event) => {

    let socket = io();

    socket.on('connect', function() {
        console.log('connected socket');
        if (localStorage.getItem('userid') === null) {
            console.log('requesting new id');
            socket.emit('newid');
        };
        socket.emit('word', {data: 'I\'m connected!'});
    });

    socket.on('newid', function(id) {
        console.log('got new id: ' + id);
        localStorage.setItem('userid', id);
    });

    socket.on('newword', function(word) {
        console.log(word);
        let pool = document.getElementById('pool');
        let words = document.getElementById('words');
        let message = document.getElementById('newwordmessage');
        pool.textContent = word[1];
        words.textContent = word[2];
        if (word[3] != '') {
            message.textContent = word[3];
        };
    });

    socket.on('wordmess', function(mess) {
        console.log('word message: ' + mess);
        let message = document.getElementById('newwordmessage');
        message.textContent = mess;
    });

    let form = document.getElementById('wordform');

    form.addEventListener('submit', function(event) {
        //localStorage.name = form[0].value;
        let message = form[0].value;
        socket.emit('submit', message);
        console.log('submitted');
        form[0].value = '';
        event.preventDefault();
        return false;
    });
});
