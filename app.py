#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, render_template, redirect
from flask_socketio import SocketIO, send, emit, join_room
from update_server import gitpullserver
from anagrams import pickletter, getword, calc_score, resetgame
import string, random
import re

with open('../secret.txt') as f:
    w_secret = f.read()[:-1]

app = Flask(__name__)
app.config['SECRET KEY'] = w_secret
socketio = SocketIO(app)

with open('dictionaries/blex.txt', encoding='utf-8') as dictfile:
    dict_cz = [word[:-1].upper() for word in dictfile.readlines()[2:]]

with open('dictionaries/twl06.txt', encoding='utf-8') as dictfile:
    dict_en = [word[:-1].upper() for word in dictfile.readlines()[2:]]

### Room parameters
alphabet = string.ascii_uppercase
min_word_length = 3
score_handicap = 2  # subtract this from the score for each word
block_alphabet = '🄰🄱🄲🄳🄴🄵🄶🄷🄸🄹🄺🄻🄼🄽🄾🄿🅀🅁🅂🅃🅄🅅🅆🅇🅈🅉'
# block_alphabet = 'AÁBCČDĎEÉĚFGHIÍJKLMNŇOÓPQRŘSŠTŤUÚŮVWXYÝZŽ'

rooms = {}
rooms['test'] = resetgame()
rooms['test']['pool_filpped'] = 'TEST'
users = []

def toblocks(letterstring):
    letterlist = [block_alphabet[alphabet.find(l)] for l in letterstring]
    return ''.join(letterlist)


@app.route('/')
def tolobby():
    return redirect('/room/lobby')


@app.route('/info')
def info():
    return app.send_static_file('info.html')


@app.route('/room/<room>')
def room(room):
    if room in rooms:
        if room == 'cz':
            poolletters = rooms[room]['pool_flipped']
        else:
            poolletters = toblocks(rooms[room]['pool_flipped'])
        return render_template('index.html', room=room, poolletters=poolletters)
    else:
        return redirect('/room/' + room + '/reset')


@app.route('/room/<room>/reset')
def reset(room):
    global rooms
    if room == 'cz':
        rooms[room] = resetgame(language='cz')
    else:
        rooms[room] = resetgame()
        print('reset room', room, rooms[room])
    return redirect('/room/' + room)


# endpoint that pulls from github and restarts the server
@app.route('/update_server', methods=['POST'])
def updateserver():
    return gitpullserver(w_secret)


@socketio.on('adduser')
def adduser(userid):
    if not userid:
        lettnum = string.ascii_letters + string.digits
        userid = ''.join( random.choice(lettnum) for i in range(10) )
        print('sending back newly generated id: ' + userid)
        emit('userid', userid)

    if userid not in users:
        # users[userid] = []
        users.append(userid)


def update(room, pool_flipped, played_words):
    if room == 'cz':
        blockwords = {}
        for user in played_words.keys():
            blockwords[user] = ' '.join([word for word in played_words[user]])
        poolstring = '​'.join(pool_flipped)
    else:
        blockwords = {}
        for user in played_words.keys():
            blockwords[user] = ' '.join([toblocks(word) for word in played_words[user]])
        poolstring = '​'.join(toblocks(pool_flipped))
    scores = {user:calc_score(words, score_handicap) for user, words in played_words.items()}
    socketio.emit('update', [poolstring, blockwords, scores, ''], room=room)


@socketio.on('update')
def updateclient(roomname):
    print('updating client for room:',roomname)
    join_room(roomname)
    room = rooms[roomname]
    update(roomname, room['pool_flipped'], room['played_words'])


@socketio.on('submit')
def handle_message(roomname, userid, word):
    global rooms
    if roomname == 'cz':
        lang = 'cz'
        dictionary = dict_cz
    else:
        lang = 'en'
        dictionary = dict_en
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


if __name__ == '__main__':
    if app.env == 'development':
        socketio.run(app, host='0.0.0.0', port=80)
    else:
        socketio.run(app)
