#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, render_template, redirect
from flask_socketio import SocketIO, send, emit
from update_server import update
from pirate_scrabble import toblocks, pickletter, getword
import string, random

with open('../secret.txt') as f:
    w_secret = f.read()[:-1]

app = Flask(__name__)
app.config['SECRET KEY'] = w_secret
socketio = SocketIO(app)

with open('twl06.txt') as twl06:
    dictionary = [word[:-1].upper() for word in twl06.readlines()[2:]]

min_word_length = 3
alphabet = string.ascii_uppercase


def resetgame():
    pool = [13,5,6,7,24,6,7,6,12,2,2,8,8,11,15,4,2,12,10,10,6,2,4,2,2,2]
    pool_flipped = ''
    played_words = {}
    return pool, pool_flipped, played_words

pool, pool_flipped, played_words = resetgame()


@app.route('/')
def anagrams():
    poolletters = toblocks(pool_flipped)
    return render_template('index.html', poolletters=poolletters)


@app.route('/info')
def info():
    return app.send_static_file('info.html')


@app.route('/reset')
def reset():
    global pool, pool_flipped, played_words
    pool, pool_flipped, played_words = resetgame()
    return redirect('/')


# endpoint that pulls from github and restarts the server
@app.route('/update_server', methods=['POST'])
def updateserver():
    return update(w_secret)


@socketio.on('adduser')
def adduser(userid):
    if not userid:
        lettnum = string.ascii_letters + string.digits
        userid = ''.join( random.choice(lettnum) for i in range(10) )
        print('sending back newly generated id: ' + userid)
        emit('userid', userid)

    if userid not in played_words:
        played_words[userid] = []

    blockwords = {}
    for user in played_words.keys():
        blockwords[user] = ' '.join( [toblocks(word) for word in played_words[user]] )
    poolstring = '​'.join(toblocks(pool_flipped))
    socketio.emit('update', ['', poolstring, blockwords, ''])


def update(pool_flipped, played_words):
    blockwords = {}
    for user in played_words.keys():
        blockwords[user] = ' '.join([toblocks(word) for word in played_words[user]])
    poolstring = '​'.join(toblocks(pool_flipped))
    socketio.emit('update', ['', poolstring, blockwords, ''])


@socketio.on('update')
def updateclient():
    update(pool_flipped, played_words)
    

@socketio.on('submit')
def handle_message(userid, word):
    global pool
    global pool_flipped
    global played_words

    message = ''
    word = word.upper()
    result = False

    # Is the word length 0? Is it shorter than the minimum length? Is it a real word?
    if len(word) == 0:
        letter = pickletter(pool)
        letterindex = alphabet.find(letter)
        pool[letterindex] -= 1
        pool_flipped = pool_flipped + letter
        message = 'Drew a new letter'
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

    update(pool_flipped, played_words)


if __name__ == '__main__':
    if app.env == 'development':
        socketio.run(app, host='0.0.0.0', port=80)
    else:
        socketio.run(app)
