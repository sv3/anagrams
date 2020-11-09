import random
import string
from copy import deepcopy


with open('blex.txt', encoding='utf-8') as dictfile:
    dict_cz = [word[:-1].upper() for word in dictfile.readlines()[2:]]

with open('twl06.txt', encoding='utf-8') as dictfile:
    dict_en = [word[:-1].upper() for word in dictfile.readlines()[2:]]

alphabet = string.ascii_uppercase
# alphabet = 'AÁBCČDĎEÉĚFGHIÍJKLMNŇOÓPQRŘSŠTŤUÚŮVWXYÝZŽ'
min_word_length = 3
score_handicap = 2


def resetgame():
    # use letter distribution from wikipedia article "Anagrams"
    starting_pool = [13,5,6,7,24,6,7,6,12,2,2,8,8,11,15,4,2,12,10,10,6,2,4,2,2,2]
    #                  A,Á,B,C,Č,D,Ď,E,É,Ě,F,G,H,I,Í,J,K,L,M,N,Ň,O,Ó,P,Q,R,Ř,S,Š,T,Ť,U,Ú,Ů,V,W,X,Y,Ý,Z,Ž
    # starting_pool = [5,2,2,3,1,3,1,5,2,2,1,1,3,4,3,2,3,3,3,5,1,6,1,3,1,3,2,4,2,4,1,3,1,1,4,1,1,2,2,2,1]
    pool = starting_pool
    pool_flipped = ''
    played_words = {}
    return {'pool':pool, 'pool_flipped':pool_flipped, 'played_words':played_words}


def calc_score(words, handicap):
    score = 0
    for word in words:
        lenw = len(word)
        if lenw >= handicap:
            score += lenw - handicap
    return score


def pickletter(letterpool, letterpool_flipped):
    poolstring = ''.join([alphabet[i]*num for i, num in enumerate(letterpool)])
    letter = random.choice(poolstring)
    letterindex = alphabet.find(letter)
    letterpool[letterindex] -= 1
    letterpool_flipped = letterpool_flipped + letter
    return letter, letterpool, letterpool_flipped


def check_fully_contained(donor, target):
    '''Check if donor is fully contained in target. Return any remaining letters from target'''
    for l in donor:
        index = target.find(l)

        # letter not in target word - abort
        if index < 0:
            return False
        else:
            # remove the letter
            target = target[:index] + target[index+1:]

    # return remaining letters from target word
    return target


def getword(target, letterpool, played_words, depth):
    target = target.upper()
    indent = ' ' * depth * 2
    print(indent + f'target: {target}  letterpool: {letterpool}  played_words: {played_words})')
    played_words_new = deepcopy(played_words)

    for player, player_words in played_words.items():
        for donor in player_words:
            # Check if any of the played words are fully contained in the target word
            remaining_letters = check_fully_contained(donor, target)
            if not remaining_letters:
                # try the next word in player_words
                continue
            elif donor in target:
                print('You need to rearrange the letters in a word to steal it')
                continue
            elif remaining_letters == '':
                # found a word to steal
                if depth == 0:
                    # can't steal a just a single word - must combine with other letters
                    continue
                played_words_new[player].remove(donor)
                print(indent + 'stealing ' + donor)
                return True, letterpool, played_words_new
            else:
                # found a word to steal for some of the letters needed - we need to go deeper
                played_words_new[player].remove(donor)
                print(indent + f'trying to steal: {donor} to make {target}.  remaining: {remaining_letters}')
                result, newpool, played_words_new = getword(remaining_letters, letterpool, played_words_new, depth+1)
                if result:
                    return True, newpool, played_words_new

    print(indent + 'failed to find a word to steal for the letters:', target)

    poollist = list(letterpool)
    target_remaining = ''

    for letter in target:
        if letter in poollist:
            poollist.remove(letter)
        else:
            target_remaining = target_remaining + letter

    if target_remaining == '':
        print(indent + 'taking these letters from the pool:', target)
        return True, ''.join(poollist), played_words
    else:
        print(indent + f'failed to find these letters from {target} in the pool: {target_remaining} - backtracking')
        return False, letterpool, played_words



if __name__ == '__main__':
    # play in the terminal with an imaginary and passive opponent
    pool, pool_flipped, played_words = resetgame()
    playerid = 'itsme'
    played_words[playerid] = []
    played_words['otherguy'] = ['CAT', 'HAT', 'FAT']
    dictionary = dict_en

    while True:

        print()
        print('tiles in pool: ', end='')
        print(pool_flipped)
        for player, words in played_words.items():
            print(f'{player}:  {" ".join(words)}')
            print(f'score: {calc_score(words, score_handicap)}')

        word = input('enter word: ').upper()
        # clear_output()

        result = False

        # is it a valid word?
        if len(word) == 0:
            letter, pool, pool_flipped = pickletter(pool, pool_flipped)
            print('flipped over', letter)
        elif len(word) < min_word_length:
            print('That word is too short. Minimum length is', min_word_length)
        elif word not in dictionary:
            print(word, 'is not even a word ⚆_⚆')
        else:
            result, pool_flipped, played_words = getword(word, pool_flipped, played_words, 0)

        if result:
            print('You claimed ' + word)
            played_words[playerid].append(word)
