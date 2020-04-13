document.addEventListener('DOMContentLoaded', (event) => {

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


var socket = io();
socket.on('connect', function() {
    console.log('connectedsocket');
    socket.emit('word', {data: 'I\'m connected!'});
});

socket.on('newword', function(word) {
    console.log(word);
    var pool = document.getElementById('pool');
    var words = document.getElementById('words');
    pool.textContent = word[1];
    words.textContent = word[2];
});


// Get user name stored on this device
//if (localStorage.name) {
//form[0].value = localStorage.name
//};


