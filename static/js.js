function renderwords(wordlists) {
    userid = localStorage.getItem('userid')
    let wordlistdiv = document.getElementById('wordlist')
    wordlistdiv.innerHTML = ''          // clear word lists

    for (const playerid in wordlists) {
        if (playerid === userid) {continue} // deal with the current user later
        if (wordlists[playerid] === '') {continue}
        htmlstring = `
        <div class='namelabel'>${playerid}</div>
        <div class='words'>${wordlists[playerid]}</div>`
        wordlistdiv.innerHTML += htmlstring
    }

    // append current user's words at end of list
    htmlstring = `
    <div class='namelabel'>Your words</div>
    <div class='words'>${wordlists[userid]}</div>`
    wordlistdiv.innerHTML += htmlstring
}


document.addEventListener('DOMContentLoaded', (event) => {

    let socket = io()

    socket.on('connect', function() {
        console.log('connected socket')
        // if a user id is not stored, request one from the server
        if (localStorage.getItem('userid') === null) {
            console.log('requesting new id')
            socket.emit('newid')
        } else {
            console.log('adduser')
            socket.emit('adduser', localStorage.getItem('userid'))
        }
    })


    socket.on('newid', function(id) {
        // got a message containing a new id for this session
        console.log('got new id: ' + id)
        localStorage.setItem('userid', id)
    })


    socket.on('update', function(wordresponse) {
        console.log('update')
        if (wordresponse == null) {return}
        console.log(wordresponse)

        let pool = document.getElementById('pool')
        let message = document.getElementById('globalmessage')

        pool.textContent = wordresponse[1]  // render letter pool
        
        renderwords(wordresponse[2])      // dictionary of word lists by player id

        // display global message
        if (wordresponse[3] !== ''){
            message.textContent = wordresponse[3]
        }
    })


    socket.on('wordmess', function(mess) {
        console.log('word message: ' + mess)
        let message = document.getElementById('localmessage')
        message.textContent = mess
        setTimeout(function() {
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
