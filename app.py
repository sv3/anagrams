#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, request, render_template, abort
from flask_socketio import SocketIO
import git
import json
from check_signature import is_valid_signature
from pirate_scrabble import toblocks, pickletter, recursive
import string

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
played_words = []
messages = []


@app.route('/', methods=['POST', 'GET'])
def anagrams():
    if request.method == 'GET':
        poolletters = toblocks(pool_flipped)
        print(messages)
        blockwords = [ toblocks(word) for word in played_words ]
        return render_template('index.html', messages=messages, poolletters=poolletters, words=blockwords)
    else:
        return 'what the heck'


@app.route('/info')
def info():
    return app.send_static_file('info.html')


@app.route('/update_server', methods=['POST'])
def update():
    abort_code = 418
    # Do initial validations on required headers
    required_headers = ['X-Github-Event', 'X-Github-Delivery', 'X-Hub-Signature', 'User-Agent']
    if not all(reqd_header in request.headers for reqd_header in required_headers):
        abort(abort_code)
    if not request.is_json:
        abort(abort_code)
    ua = request.headers.get('User-Agent')
    if not ua.startswith('GitHub-Hookshot/'):
        abort(abort_code)

    event = request.headers.get('X-GitHub-Event')
    if event != "push":
        return json.dumps({'msg': "Wrong event type"})

    x_hub_signature = request.headers.get('X-Hub-Signature')
    # webhook content type should be application/json for request.data to have the payload
    # request.data is empty in case of x-www-form-urlencoded
    if not is_valid_signature(x_hub_signature, request.data, w_secret):
        print('Deploy signature failed: {sig}'.format(sig=x_hub_signature))
        abort(abort_code)

    payload = request.get_json()
    if payload is None:
        print('Deploy payload is empty: {payload}'.format(
            payload=payload))
        abort(abort_code)

    if payload['ref'] != 'refs/heads/master':
        return json.dumps({'msg': 'Not master; ignoring'})

    repo = git.Repo('.')
    origin = repo.remotes.origin

    pull_info = origin.pull()

    if len(pull_info) == 0:
        return json.dumps({'msg': "Didn't pull any information from remote!"})
    if pull_info[0].flags > 128:
        return json.dumps({'msg': "Didn't pull any information from remote!"})

    commit_hash = pull_info[0].commit.hexsha
    build_commit = 'build_commit = "{commit_hash}"'.format(commit_hash=commit_hash)
    print(str(build_commit))
    return 'Updated Anagrams server to commit {commit}'.format(commit=commit_hash)


@socketio.on('submit')
def handle_message(word):
    print('received message: ' + str(word))
    global pool
    global pool_flipped
    global played_words
    global messages
    tilestatus = ''

    messages = []
    word = word.upper()
    result = False

    # is it a valid word?
    if len(word) == 0:
        letter = pickletter(pool)
        letterindex = alphabet.find(letter)
        pool[letterindex] -= 1
        pool_flipped = pool_flipped + letter
    elif len(word) < min_word_length:
        messages.append('That word is too short. Minimum length is {min_word_length}'.format(min_word_length=min_word_length))
        pass
    elif word not in dictionary:
        messages.append('{word} is not even a word ⚆_⚆'.format(word=word))
        pass
    else:
        result, pool_flipped_new, played_words_new = recursive(word, pool_flipped, played_words, 0)
        if result == False:
            messages.append('You can\'t make {word} out of the available letters'.format(word=word))
            pass

    if result == True:
        messages.append('You claimed {word}'.format(word=word))
        played_words = played_words_new.copy()
        played_words.append(word)
        pool_flipped = pool_flipped_new

    blockwords = ' '.join([ toblocks(word) for word in played_words ])
    poolstring = '​'.join(toblocks(pool_flipped))
    socketio.emit('newword', [word, poolstring, blockwords])


if __name__ == '__main__':
    socketio.run(app)
