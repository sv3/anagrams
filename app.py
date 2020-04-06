
# A very simple Flask Hello World app for you to get started with...

from flask import Flask
from flask import request, render_template
from pirate_scrabble import pooltoletters, letterstopool, pickletter, recursive
import string


with open('twl06.txt') as twl06:
    dictionary = [word[:-1].upper() for word in twl06.readlines()[2:]]

min_word_length = 3
alphabet = string.ascii_uppercase
pool = [13,5,6,7,24,6,7,6,12,2,2,8,8,11,15,4,2,12,10,10,6,2,4,2,2,2]
pool_flipped = [0 for i in range(26)]
played_words = []

app = Flask(__name__)

@app.route('/', methods=['POST', 'GET'])
def hello_world():
    global pool
    global pool_flipped
    global played_words
    messages = []
    tilestatus = ''

    if request.method == 'POST':
        word = request.form['word'].upper()

        result = False

        # is it a valid word?
        if len(word) == 0:
            pass
        elif len(word) < min_word_length:
            messages.append(f'That word is too short. Minimum length is {min_word_length}')
        elif word not in dictionary:
            messages.append(f'{word} is not even a word ⚆_⚆')
        else:
            result, pool_flipped, played_words = recursive(word, played_words, pool_flipped)
            if result == False:
                messages.append(f'You can\'t make {word} out of the available letters')

        if result:
            messages.append(f'You claimed {word}')
            played_words.append(word)
        else:
            letter = pickletter(pool)
            messages.append(f'flipped over {letter}')
            letterindex = alphabet.find(letter)
            pool[letterindex] -= 1
            pool_flipped[letterindex] += 1

    poolletters = pooltoletters(pool_flipped)
    print(messages)
    return render_template('index.html', messages=messages, poolletters=poolletters, words=played_words)
