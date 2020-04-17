document.addEventListener('DOMContentLoaded', (event) => {

    var socket = io();

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
        var pool = document.getElementById('pool');
        var words = document.getElementById('words');
        var message = document.getElementById('newwordmessage');
        pool.textContent = word[1];
        words.textContent = word[2];
        message.textContent = word[3];
    });

    var form = document.getElementById('wordform');

    form.addEventListener('submit', function(event) {
        //localStorage.name = form[0].value;
        var message = form[0].value;
        socket.emit('submit', message);
        console.log('submitted');
        form[0].value = '';
        event.preventDefault();
        return false;
    });
});
