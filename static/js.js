document.addEventListener('DOMContentLoaded', (event) => {

    let socket = io();

    socket.on('connect', function() {
        console.log('connected socket');
        if (localStorage.getItem('userid') === null) {
            console.log('requesting new id');
            socket.emit('newid');
        };
    });

    socket.on('newid', function(id) {
        console.log('got new id: ' + id);
        localStorage.setItem('userid', id);
    });

    socket.on('newword', function(word) {
        console.log(word);
        let pool = document.getElementById('pool');
        let wordlist = document.getElementById('wordlist');
        let message = document.getElementById('newwordmessage');
        pool.textContent = word[1];
        wordlist.innerHTML = '';
        for (const playerid in word[2]) {
            let namediv = document.createElement("div");
            namediv.append(document.createTextNode(playerid));
            let wordsdiv = document.createElement("div");
            wordsdiv.className = 'words';
            wordsdiv.append(document.createTextNode(word[2][playerid]));
            wordlist.append(namediv, wordsdiv);
        };
        message.textContent = word[3];
    });

    socket.on('wordmess', function(mess) {
        console.log('word message: ' + mess);
        let message = document.getElementById('newwordmessage');
        message.textContent = mess;
    });

    let form = document.getElementById('wordform');

    form.addEventListener('submit', function(event) {
        let message = form[0].value;
        socket.emit('submit', localStorage.getItem('userid'), message);
        console.log('submitted');
        form[0].value = '';
        event.preventDefault();
        return false;
    });
});
