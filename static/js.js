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
        myscore = scores[userid]
    }
    htmlstring = `
    <div class='namelabel'>
        You 
        <div id='myname'>(${userid})</div>
    </div>
    <div class='words' id='mywords'>
        ${mywords}
        <div class='score'>${myscore}</div>
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
    let roomname = document.head.getAttribute('data-room')
    console.log(roomname)

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
        socket.emit('update', roomname)
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


    // submit word to claim
    let form = document.getElementById('wordform')
    form.addEventListener('submit', function(event) {
        let message = form[0].value
        socket.emit('submit', roomname, localStorage.getItem('userid'), message)
        form[0].value = ''
        event.preventDefault()
        return false
    })

    let wordlist = document.getElementById('wordlist')
    wordlist.addEventListener('click', function(e) {
        if (e.target.id == 'myname') {
            let oldname = e.target.textContent.slice(1,-1)
            formhtml = `(
            <form id="nameform" method="post">
                <span id="hide"></span><input type="text" name="nameinput" id="nameinput" autofocus autocapitalize=off autocomplete=off spellcheck=false>
            </form>)`
            e.target.innerHTML = formhtml
            //console.log(e.target.childNodes[0])
            let nameinput = document.getElementById('nameinput')
            nameinput.value = oldname
            nameinput.focus()
            nameinput.select()
            
            let hide = document.getElementById('hide');
            resize();
            nameinput.addEventListener("input", resize);

            function resize() {
              hide.textContent = nameinput.value;
              nameinput.style.width = hide.offsetWidth + "px";
            }
            
            e.target.addEventListener('submit', function(event) {
                let newname = event.target[0].value
                socket.emit('addname', localStorage.getItem('userid'), newname)
                e.target.innerHTML = "(" + newname + ")"
                event.preventDefault()
                return false
            })
        }
        return false
    } , false)
})
