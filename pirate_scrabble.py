import random
import string

with open('twl06.txt') as twl06:
    dictionary = [word[:-1].upper() for word in twl06.readlines()[2:]]

min_word_length = 3
alphabet = string.ascii_uppercase
pool = [13,5,6,7,24,6,7,6,12,2,2,8,8,11,15,4,2,12,10,10,6,2,4,2,2,2]
block_alphabet = '🄰🄱🄲🄳🄴🄵🄶🄷🄸🄹🄺🄻🄼🄽🄾🄿🅀🅁🅂🅃🅄🅅🅆🅇🅈🅉'
pool_flipped = ''
played_words = []


def countstostring(letterpool):
    letterlist = [ alphabet[i]*num for i, num in enumerate(letterpool) ]
    return ''.join(letterlist)


def stringtoblocks(string):
    letterlist = [ block_alphabet[alphabet.find(l)] for l in string ]
    return ''.join(letterlist)


def stringtocounts(letters):
    letterpool = [0 for i in range(26)]
    for l in letters.upper():
        letterindex = alphabet.find(l)
        letterpool[letterindex] += 1
    return letterpool


def pickletter(letterpool):
    poolstring = ''.join([ alphabet[i]*num for i, num in enumerate(letterpool) ])
    letter = random.choice(poolstring)
    return letter


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


def recursive(target, letterpool, played_words, depth):
    target = target.upper()
    indent = depth*2
    print(' '*indent + 'target',target,'  letterpool',letterpool,'  played_words',played_words)

    if played_words != []:
        for donor in played_words:
            # Check if any of the played words are fully contained in the target word
            remaining = check_fully_contained(donor, target)
            if remaining == False:
                # try the next word in played_words
                continue
            elif remaining == '':
                # found a word to steal
                if depth == 0:
                    continue
                played_words_new.remove(donor)
                print(' '*indent + 'stealing ' + donor + ' to make ' + target)
                return True, letterpool, played_words_new
            else:
                # found a word to steal for some of the letters needed - we need to go deeper
                played_words_new = played_words.copy()
                played_words_new.remove(donor)
                print(' '*indent + 'trying to steal', donor, 'to make', target, '.  remaining:', remaining)
                result, newpool, played_words_new = recursive(remaining, letterpool, played_words_new, depth+1)
                if result == True:
                    return True, newpool, played_words_new
                else:
                    played_word_new = played_words.copy()
        print(' '* indent + 'failed to find a word to steal for the letters:', target)

    poollist = [ l for l in reversed(letterpool) ]
    target_remaining = ''

    for letter in target:
        if letter in poollist:
            poollist.remove(letter)
        else:
            target_remaining = target_remaining + letter

    if target_remaining == '':
        print(' '*indent + 'taking these letters from the pool:', target)
        return True, ''.join(poollist), played_words
    else:
        print(' '*indent + 'failed to find these letters from', target, 'in the pool:', target_remaining, '- backtracking')
        return False, letterpool, played_words

def infinite():
    while True:
        print('tiles in pool: ', end='')
        print(pool_flipped)
        print('words played: ' + '  '.join(played_words) )

        word = input('enter word: ').upper()
        # clear_output()

        result = False

        # is it a valid word?
        if len(word) == 0:
            pass
        elif len(word) < min_word_length:
            print('That word is too short. Minimum length is', min_word_length)
        elif word not in dictionary:
            print(word, 'is not even a word ⚆_⚆')
        else:
            result, pool_flipped, played_words = recursive(word, pool_flipped, played_words, 0)

        if result:
            print('You claimed ' + word)
            played_words.append(word)
        else:
            letter = pickletter(pool)
            print('flipped over', letter)
            letterindex = alphabet.find(letter)
            pool[letterindex] -= 1
            pool_flipped = pool_flipped + letter
