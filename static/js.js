function renderwords(wordlists, scores) {
    userid = localStorage.getItem('userid')
    let wordlistdiv = document.getElementById('wordlist')
    wordlistdiv.innerHTML = ''              // clear word lists

    for (const playerid in wordlists) {
        if (playerid === userid) {continue} // deal with the current user later
        if (wordlists[playerid] === '') {continue} // ignore player with no words
        score = scores[playerid]
        htmlstring = `
        <div class='namelabel'>${playerid}</div>
        <div class='words'>
            ${wordlists[playerid]}
            <div class='score'>${score}</div>
        </div>`
        wordlistdiv.innerHTML += htmlstring
    }

    // append current user's words at end of list
    let mywords = ''
    let myscore = 0
    if (userid in wordlists) {
        mywords = wordlists[userid]
        score = scores[userid]
    }
    htmlstring = `
    <div class='namelabel'>You</div>
    <div class='words'>
        ${mywords}
        <div class='score'>${score}</div>
    </div>`
    wordlistdiv.innerHTML += htmlstring
}

function update(wordresponse) {
    console.log('update')
    if (wordresponse == null) {return}
    console.log(wordresponse)

    let pool = document.getElementById('pool')
    let message = document.getElementById('globalmessage')

    pool.textContent = wordresponse[0]  // render letter pool

    renderwords(wordresponse[1], wordresponse[2])        // dictionary of word lists by player id

    // display global message
    if (wordresponse[3] !== ''){
        message.textContent = wordresponse[3]
    }
}

document.addEventListener('DOMContentLoaded', (event) => {

    let socket = io()

    socket.on('connect', function() {
        console.log('connected socket')
        // if a user id is not stored, request one from the server
        if (localStorage.getItem('userid') === null) {
            console.log('requesting new id')
            socket.emit('adduser', '')
        // if a user id is stored, report it to the server to join game
        } else {
            socket.emit('adduser', localStorage.getItem('userid'))
        }
        socket.emit('update')
    })


    socket.on('userid', function(id) {
        // got a message containing a new id for this session
        console.log('got new id: ' + id)
        localStorage.setItem('userid', id)
    })

    socket.on('update', update)
    
    let disappeartimer

    socket.on('wordmess', function(mess) {
        console.log('word message: ' + mess)
        let message = document.getElementById('localmessage')
        message.textContent = mess
        clearTimeout(disappeartimer)
        disappeartimer = setTimeout(function() {
            message.textContent = ''
        }, 6000)
    })


    let form = document.getElementById('wordform')

    form.addEventListener('submit', function(event) {
        let message = form[0].value
        socket.emit('submit', localStorage.getItem('userid'), message)
        form[0].value = ''
        event.preventDefault()
        return false
    })
})
