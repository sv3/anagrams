
# A very simple Flask Hello World app for you to get started with...

from flask import Flask
import pirate_scrabble as ps
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

@app.route('/')
def hello_world():
    poolletters = pooltoletters(pool_flipped)
    playedwordsstring = '  '.join(played_words)
    return f'tiles in pool: {poolletters}<br/>words played: {playedwordsstring}'


@app.route('/word/<string:target>')
def enter_word(target):
    global pool
    global pool_flipped
    global played_words

    word = target.upper()
    page = ''

    poolletters = pooltoletters(pool_flipped)
    playedwordsstring = '  '.join(played_words)

    result = False

    # is it a valid word?
    if len(word) == 0:
        pass
    elif len(word) < min_word_length:
        print('That word is too short. Minimum length is', min_word_length)
        page = page + f'That word is too short. Minimum length is {min_word_length}<br/>'
    elif word not in dictionary:
        print(word, 'is not even a word ⚆_⚆')
        page = page + f'{word} is not even a word ⚆_⚆<br/>'
    else:
        result, pool_flipped, played_words = recursive(word, played_words, pool_flipped)

    if result:
        print('You claimed ' + word)
        page = page + f'You claimed {word}<br/>'
        played_words.append(word)
    else:
        letter = pickletter(pool)
        print('flipped over', letter)
        page = page + f'flipped over {letter}<br/>'
        letterindex = alphabet.find(letter)
        pool[letterindex] -= 1
        pool_flipped[letterindex] += 1

    page = page + f'tiles in pool: {poolletters}<br/>words played: {playedwordsstring}<br/>' 
    return page
