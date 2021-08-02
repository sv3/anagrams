#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, render_template, redirect
from flask_socketio import SocketIO, send, emit, join_room
from update_server import gitpullserver
from anagrams import pickletter, getword, calc_score, resetgame
import string, random
import re
import json

from apscheduler.schedulers.background import BackgroundScheduler

with open('../secret.txt') as f:
    w_secret = f.read()[:-1]

app = Flask(__name__)
app.config['SECRET KEY'] = w_secret
socketio = SocketIO(app)

dictionaries = {}

with open('dictionaries/blex.txt', encoding='utf-8') as dictfile:
    dictionaries['cz'] = [word[:-1].upper() for word in dictfile.readlines()[2:]]

with open('dictionaries/twl06.txt', encoding='utf-8') as dictfile:
    dictionaries['en'] = [word[:-1].upper() for word in dictfile.readlines()[2:]]

alphabet = string.ascii_uppercase
block_alphabet = '🄰🄱🄲🄳🄴🄵🄶🄷🄸🄹🄺🄻🄼🄽🄾🄿🅀🅁🅂🅃🅄🅅🅆🅇🅈🅉'

rooms = {}
rooms_meta = {}
meta_default = {
        'lang':'en',
        'min_word_length':3,
        'score_handicap':2 # subtract this from the score for each word
        }

rooms_meta['test'] = meta_default.copy()
rooms['test'] = resetgame(rooms_meta['test'])
rooms['test']['pool_flipped'] = 'TEST'
rooms_meta['cz'] = meta_default.copy()
rooms_meta['cz']['lang'] = 'cz'

users = {}


def toblocks(letterstring):
    letterlist = [block_alphabet[alphabet.find(l)] for l in letterstring]
    return ''.join(letterlist)


@app.route('/')
def tolobby():
    return redirect('/room/lobby')


@app.route('/info')
def info():
    return app.send_static_file('info.html')


@app.route('/room/<roomname>')
def room(roomname):
    if roomname in rooms and roomname in rooms_meta:
        return render_template('index.html', room=roomname, poolletters='')
    else:
        return redirect('/room/' + roomname + '/reset')


@app.route('/room/<roomname>/reset')
def reset(roomname):
    global rooms
    global rooms_meta

    # for new rooms, set default parameters
    rooms_meta.setdefault(roomname, meta_default)

    meta = rooms_meta[roomname]
    rooms[roomname] = resetgame(meta)
    print('reset room', roomname, rooms[roomname])
    return redirect('/room/' + roomname)


@app.route('/debug')
def debug():
    # if app.env != 'development':
    #     return redirect('/')
    # elif app.env == 'development':
    debugvars = ('rooms', 'rooms_meta', 'users')
    vardict = { key:globals()[key] for key in debugvars }
    return(json.dumps(vardict))


@socketio.on('adduser')
def adduser(userid, username):
    print(userid, username)
    if not userid:
        userid = ''.join( random.choice(string.ascii_lowercase) for i in range(7) )
        users[userid] = userid
        print('sending back newly generated id: ' + userid)
        emit('userid', userid)

    # just an id received: save it in users
    if not username:
        if userid not in users:
            users[userid] = userid
    else:
        users[userid] = username


def update(roomname, pool_flipped, played_words):
    score_handicap = rooms_meta[roomname]['score_handicap']
    blockwords = {}
    if rooms_meta[roomname]['lang'] == 'cz':
        for user in played_words.keys():
            blockwords[user] = ' '.join([word for word in played_words[user]])
        poolstring = '​'.join(pool_flipped)
    else:
        for user in played_words.keys():
            blockwords[user] = ' '.join([toblocks(word) for word in played_words[user]])
        poolstring = '​'.join(toblocks(pool_flipped))

    scores = {userid:calc_score(words, score_handicap) for userid, words in played_words.items()}
    names = {userid:users[userid] for userid in played_words}
    socketio.emit('update', [poolstring, blockwords, scores, names, ''], room=roomname)


@socketio.on('update')
def updateclient(roomname):
    print('updating client for room:',roomname)
    join_room(roomname)
    room = rooms[roomname]
    update(roomname, room['pool_flipped'], room['played_words'])


@socketio.on('submit')
def submit(roomname, userid, word):
    global rooms
    room_meta = rooms_meta[roomname]
    lang = room_meta['lang']
    min_word_length = room_meta['min_word_length']
    dictionary = dictionaries[lang]
    room = rooms[roomname]

    pool, pool_flipped, played_words = room['pool'], room['pool_flipped'], room['played_words']

    message = ''
    word = word.upper()
    word = re.sub(r'\s+', '', word)
    print(userid, 'submitted', word)
    result = False

    # Is the word length 0? Is it shorter than the minimum length? Is it a real word?
    if len(word) == 0:
        letter, pool, pool_flipped = pickletter(pool, pool_flipped, language=lang)
        message = 'A new letter has been flipped'
    elif len(word) < min_word_length:
        emit('wordmess', f'That word is too short. Minimum length is {min_word_length}')
    elif word not in dictionary:
        emit('wordmess', f'{word} is not even a word ⚆_⚆')
    else:
        # recursively try to make the word from a combination of existing words and letters
        result, pool_flipped_new, played_words_new = getword(word, pool_flipped, played_words, 0)
        if not result:
            emit('wordmess', f'You can\'t make {word} out of the available letters')

    if result:
        message = f'{userid} claimed {word}'
        print(message)
        played_words = played_words_new.copy()
        if userid in played_words:
            played_words[userid].append(word)
        else:
            played_words[userid] = [word]
        pool_flipped = pool_flipped_new

    
    rooms[roomname] = {'pool':pool, 'pool_flipped':pool_flipped, 'played_words':played_words}
    update(roomname, pool_flipped, played_words)

def auto_add_letter():
    for room in rooms:
        print(room)
        submit(room, '', '')

sched = BackgroundScheduler()
sched.add_job(func=auto_add_letter, trigger='interval', seconds=5)
sched.start()

# endpoint that pulls from github and restarts the server
@app.route('/update_server', methods=['POST'])
def updateserver():
    return gitpullserver(w_secret)


if __name__ == '__main__':
    if app.env == 'development':
        socketio.run(app, host='0.0.0.0', port=80)
    else:
        socketio.run(app)
