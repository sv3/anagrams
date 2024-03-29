#!/usr/bin/env python
# -*- coding: utf-8 -*-
import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, redirect
from flask_socketio import SocketIO, send, emit, join_room
from update_server import gitpullserver
from anagrams import Anagrams, dictionaries
import string, random
import re
import json

from apscheduler.schedulers.background import BackgroundScheduler

with open('../secret.txt') as f:
    w_secret = f.read()[:-1]

app = Flask(__name__)
app.config['SECRET KEY'] = w_secret
socketio = SocketIO(app, logger=True)


alphabet = string.ascii_uppercase
block_alphabet = '🄰🄱🄲🄳🄴🄵🄶🄷🄸🄹🄺🄻🄼🄽🄾🄿🅀🅁🅂🅃🅄🅅🅆🅇🅈🅉'

rooms = {}

rooms['lobby'] = Anagrams('en', min_word_len=3, score_handicap=2)
rooms['test'] = Anagrams('en', min_word_len=3, score_handicap=2)
rooms['test'].pool_flipped = 'TEST'
rooms['cz'] = Anagrams('cz', min_word_len=3, score_handicap=2)

users = {}

tpool = eventlet.GreenPool()

def toblocks(letterstring):
    letterlist = [block_alphabet[alphabet.find(l)] for l in letterstring]
    return ''.join(letterlist)


### HTTP routes ----------------------------------------------------------------

@app.route('/')
def tolobby():
    return redirect('/room/lobby')


@app.route('/info')
def info():
    return app.send_static_file('info.html')


@app.route('/room/<roomname>')
def room(roomname):
    if roomname in rooms:
        return render_template('index.html', room=roomname, poolletters='')
    else:
        return redirect('/room/' + roomname + '/reset')


@app.route('/room/<roomname>/reset')
def reset(roomname):
    global rooms

    rooms[roomname] = Anagrams('en', 3, 2)
    print('reset room', roomname, rooms[roomname])
    return redirect('/room/' + roomname)


@app.route('/debug')
def debug():
    # if app.env != 'development':
    #     return redirect('/')
    # elif app.env == 'development':
    roomdict = { roomname:room.get_state() for roomname, room in rooms.items() }
    vardict = { 'users':users, 'rooms':roomdict }
    return(json.dumps(vardict))


@app.route('/room/<roomname>/plays')
def findplays(roomname):
    room = rooms[roomname]
    possible_plays = findplays2(roomname)
    html = ''
    for word in possible_plays:
        html += '<div class="playlist">' + word + '</div>'
    head = '<head><link rel="stylesheet" type="text/css" href="/static/normalize.css" /> <link rel="stylesheet" type="text/css" href="/static/css.css" /></head>'
    html = '<html>'+head+'<body><div>' + html + '</div></html></body>'
    return html


### websocket routes -----------------------------------------------------------

@socketio.on('adduser')
def adduser(userid, username):
    print(userid, username)

    # didn't receive an ID - generate one
    if not userid:
        userid = ''.join( random.choice(string.ascii_lowercase) for i in range(7) )
        while True:
            newname = random.choice(dictionaries['en'])
            if 4 < len(newname) < 15:
                break
        users[userid] = newname
        print('sending back newly generated id: ' + userid)
        emit('userid', (userid, newname))
        return

    # didn't receive a name - add player to the game
    if not username:
        if userid not in users:
            users[userid] = userid
        emit('userid', (userid, users[userid]))
    else:
        users[userid] = username


def update(roomname):
    room = rooms[roomname]
    score_handicap = room.score_handicap
    blockwords = {}
    pool_flipped, played_words = room.pool_flipped, room.played_words
    if room.lang == 'cz':
        for user in played_words.keys():
            blockwords[user] = ' '.join([word for word in played_words[user]])
        poolstring = '​'.join(pool_flipped)
    else:
        for user in played_words.keys():
            blockwords[user] = ' '.join([toblocks(word) for word in played_words[user]])
        poolstring = '​'.join(toblocks(pool_flipped))

    scores = {userid:room.calc_score(words) for userid, words in played_words.items()}
    names = {userid:users[userid] for userid in played_words}
    # tpool.spawn_n(update_possible_plays, roomname)
    socketio.start_background_task(update_possible_plays, roomname)
    emit('update', [poolstring, blockwords, scores, names, ''], room=roomname)


def findplays2(roomname):
    room = rooms[roomname]
    played_words = room.played_words
    letters = room.pool_flipped
    flat_word_list = []
    for player_words in played_words.values():
        for word in player_words:
            flat_word_list.append(word)

    available_letters = ''.join(flat_word_list) + letters
    available_set = set(available_letters) 

    words_from_avail_letters = []
    possible_plays = []
    for word in room.dictionary:
        if room.check_fully_contained(word, available_letters) == available_letters:
            pass
        else:
            words_from_avail_letters.append(word)
            socketio.sleep(0)

    for word in words_from_avail_letters:
        result = False
        if len(word) < room.min_word_len:
            continue
        else:
            result, _, _ = room.getword(word, room.played_words, 0)
            if result:
                socketio.sleep(0)
                possible_plays.append(word)

    return possible_plays


def update_possible_plays(roomname):
    room = rooms[roomname]
    room.possible_plays = findplays2(roomname)
    room.num_possible_plays = len(room.possible_plays)
    add_until_playable2(roomname)
    num_plays = room.num_possible_plays
    poolstring = '​'.join(toblocks(room.pool_flipped))
    socketio.emit('update', [poolstring, None, None, None, num_plays], room=roomname)


def add_until_playable2(roomname):
    room = rooms[roomname]
    while room.num_possible_plays == 0:
        room.flipletter()
        room.possible_plays = self.findplays()
        room.num_possible_plays = len(self.possible_plays)
    return

@socketio.on('update')
def updateclient(roomname):
    print('updating client for room:',roomname)
    # flask-socketio function to join a room
    join_room(roomname)
    update(roomname)


@socketio.on('submit')
def submit(roomname, userid, word):
    global rooms
    dictionary = rooms[roomname].dictionary
    room = rooms[roomname]

    pool, pool_flipped, played_words = room.pool, room.pool_flipped, room.played_words

    message = ''
    word = word.upper()
    # ignore whitespace
    word = re.sub(r'\s+', '', word)
    print(userid, 'submitted', word)
    result = False

    # Is the word length 0? Is it shorter than the minimum length? Is it a real word?
    if len(word) == 0:
        letter = room.flipletter()
        message = 'A new letter has been flipped'
    elif len(word) < rooms[roomname].min_word_len:
        emit('wordmess', f'That word is too short. Minimum length is {min_word_length}')
    elif word not in dictionary:
        emit('wordmess', f'{word} is not even a word ⚆_⚆')
    else:
        # recursively try to make the word from a combination of existing words and letters
        result, room.pool_flipped, room.played_words = room.getword(word, played_words, 0)
        if not result:
            emit('wordmess', f'You can\'t make {word} out of the available letters')
        elif result:
            message = f'{userid} claimed {word}'
            print(message)
            if userid in played_words:
                room.played_words[userid].append(word)
            else:
                room.played_words[userid] = [word]

    update(roomname)


def auto_add_letter():
    for room in rooms:
        print(room)
        submit(room, '', '')

# sched = BackgroundScheduler()
# sched.add_job(func=auto_add_letter, trigger='interval', seconds=5)
# sched.start()

# endpoint that pulls from github and restarts the server
@app.route('/update_server', methods=['POST'])
def updateserver():
    return gitpullserver(w_secret)


if __name__ == '__main__':
    if app.env == 'development':
        socketio.run(app, host='0.0.0.0', port=80)
    else:
        socketio.run(app)
