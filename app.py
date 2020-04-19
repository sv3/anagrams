#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, request, render_template, abort
from flask_socketio import SocketIO, send, emit
import git
import json
from update_server import update
from check_signature import is_valid_signature
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
pool = [13,5,6,7,24,6,7,6,12,2,2,8,8,11,15,4,2,12,10,10,6,2,4,2,2,2]
pool_flipped = ''
played_words = {}
messages = []


@app.route('/')
def anagrams():
    poolletters = toblocks(pool_flipped)
    # blockwords = [ toblocks(word) for word in played_words.values() ]
    return render_template('index.html', poolletters=poolletters) #, words=played_words.items())


@app.route('/info')
def info():
    return app.send_static_file('info.html')


@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon.ico')


# endpoint that pulls from github and restarts the server
app.add_url_rule('/update_server', 'update_server', update, methods=['POST'])


@socketio.on('newid')
def makenewid():
    lettnum = string.ascii_letters + string.digits
    newid = ''.join( random.choice(lettnum) for i in range(10) )
    played_words[newid] = []
    print('sending back newly generated id: ' + newid)
    emit('newid', newid)


@socketio.on('submit')
def handle_message(userid, word):
    print('received message: ' + str(word))
    global pool
    global pool_flipped
    global played_words

    messages = []
    word = word.upper()
    result = False

    # is it a valid word?
    if len(word) == 0:
        letter = pickletter(pool)
        letterindex = alphabet.find(letter)
        pool[letterindex] -= 1
        pool_flipped = pool_flipped + letter
        emit('wordmess', 'Added a letter to the pool')
    elif len(word) < min_word_length:
        emit('wordmess', f'That word is too short. Minimum length is {min_word_length}')
    elif word not in dictionary:
        emit('wordmess', f'{word} is not even a word ⚆_⚆')
    else:
        # recursively try to make the word from a combination of existing words and letters
        result, pool_flipped_new, played_words_new = getword(word, pool_flipped, played_words, 0)
        if result == False:
            emit('wordmess', f'You can\'t make {word} out of the available letters')

    if result == True:
        messages.append(f'{userid} claimed {word}')
        print(f'{userid} claimed {word}')
        played_words = played_words_new.copy()
        if userid in played_words:
            played_words[userid].append(word)
        else:
            played_words[userid] = [word]
        pool_flipped = pool_flipped_new

    blockwords = ' '.join([ toblocks(word) for word in played_words ])
    poolstring = '​'.join(toblocks(pool_flipped))
    socketio.emit('newword', [word, poolstring, str(played_words), messages, userid])


if __name__ == '__main__':
    if app.env == 'development':
        socketio.run(app, host='0.0.0.0', port=80)
    else:
        socketio.run(app)
