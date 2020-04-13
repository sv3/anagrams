from flask import Flask, request, render_template, redirect, url_for
from flask_socketio import SocketIO
from pirate_scrabble import toblocks, pickletter, recursive
import string


app = Flask(__name__)
app.config['SECRET KEY'] = 'secret!'
socketio = SocketIO(app)


with open('twl06.txt') as twl06:
    dictionary = [word[:-1].upper() for word in twl06.readlines()[2:]]

min_word_length = 3
alphabet = string.ascii_uppercase
pool = [13,5,6,7,24,6,7,6,12,2,2,8,8,11,15,4,2,12,10,10,6,2,4,2,2,2]
# pool_flipped = [0 for i in range(26)]
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
        messages.append(f'That word is too short. Minimum length is {min_word_length}')
    elif word not in dictionary:
        messages.append(f'{word} is not even a word ⚆_⚆')
    else:
        result, pool_flipped_new, played_words_new = recursive(word, pool_flipped, played_words, 0)
        if result == False:
            messages.append(f'You can\'t make {word} out of the available letters')

    if result == True:
        messages.append(f'You claimed {word}')
        played_words = played_words_new.copy()
        played_words.append(word)
        pool_flipped = pool_flipped_new

    blockwords = ' '.join([ toblocks(word) for word in played_words ])
    poolstring = '​'.join(toblocks(pool_flipped))
    socketio.emit('newword', [word, poolstring, blockwords])


if __name__ == '__main__':
    socketio.run(app, use_reloader=True, debug=True, host='0.0.0.0')
