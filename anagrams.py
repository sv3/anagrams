import random
import string
from copy import deepcopy
import logging, sys


dictionaries = {}

with open('dictionaries/blex.txt', encoding='utf-8') as dictfile:
    dictionaries['cz'] = [word[:-1].upper() for word in dictfile.readlines()[2:]]

with open('dictionaries/twl06.txt', encoding='utf-8') as dictfile:
    dictionaries['en'] = [word[:-1].upper() for word in dictfile.readlines()[2:]]


class Anagrams:
    '''implements the mechanics of pirate scrabble (anagrams)'''

    def __init__(self, language, min_word_len, score_handicap):
        self.lang = language
        self.min_word_len = min_word_len
        self.score_handicap = score_handicap
        if self.lang == 'cz':
            self.dictionary = dictionaries['cz']
        elif self.lang == 'en':
            self.dictionary = dictionaries['en']
        self.reset()


    def reset(self):
        if self.lang == 'en':
            self.alphabet = string.ascii_uppercase
            # use letter distribution from wikipedia article "Anagrams"
            starting_pool = [13,5,6,7,24,6,7,6,12,2,2,8,8,11,15,4,2,12,10,10,6,2,4,2,2,2]

        if self.lang == 'cz':
            self.alphabet = 'AÁBCČDĎEÉĚFGHIÍJKLMNŇOÓPQRŘSŠTŤUÚŮVWXYÝZŽ'
            #                A,Á,B,C,Č,D,Ď,E,É,Ě,F,G,H,I,Í,J,K,L,M,N,Ň,O,Ó,P,Q,R,Ř,S,Š,T,Ť,U,Ú,Ů,V,W,X,Y,Ý,Z,Ž
            starting_pool = [5,2,2,3,1,3,1,5,2,2,1,1,3,4,3,2,3,3,3,5,1,6,1,3,1,3,2,4,2,4,1,3,1,1,4,1,1,2,2,2,1]
            # double the number of each letter
            starting_pool = [x*2 for x in starting_pool]

        self.pool = ''.join([self.alphabet[i]*num for i, num in enumerate(starting_pool)])
        self.pool_flipped = ''
        self.played_words = {}
        self.possible_plays = []
        self.num_possible_plays = 0
        for i in range(self.min_word_len):
            self.flipletter()
        self.add_until_playable()


    def add_until_playable(self):
        while self.num_possible_plays == 0:
            self.flipletter()
            self.possible_plays = self.findplays()
            self.num_possible_plays = len(self.possible_plays)
        return


    def get_state(self):
        state_attrs = ['lang', 'min_word_len', 'score_handicap', 'pool', 'pool_flipped', 'played_words']
        return {key:getattr(self, key) for key in state_attrs}


    def calc_score(self, words):
        '''for each word, subtract the handicap to get the score'''
        handicap = self.score_handicap
        return sum( max(0, len(word)-handicap) for word in words )


    def flipletter(self):
        '''randomly pick a letter from the pool and move it to pool_flipped'''
        letter = random.choice(self.pool)
        self.pool = self.pool.replace(letter, '', 1)
        self.pool_flipped = self.pool_flipped + letter
        return letter


    def check_fully_contained(self, donor, target):
        '''Check if donor is fully contained in target. Return any remaining letters from target'''
        remaining = target
        for letter in donor:
            index = remaining.find(letter)
            if index < 0:
                # letter not in target word - abort
                return target
            else:
                # remove the letter
                remaining = remaining[:index] + remaining[index+1:]

        # return remaining letters from target word
        return remaining


    def getword(self, target, played_words, depth):
        target = target.upper()
        indent = ' ' * depth * 2
        logging.debug(indent + f'target: {target}  letterpool: {self.pool}  played_words: {played_words})')
        played_words_new = deepcopy(played_words)

        for player, player_words in played_words.items():
            for donor in player_words:
                # Check if any of the played words are fully contained in the target word
                remaining_letters = self.check_fully_contained(donor, target)
                if donor in target:
                    logging.debug(f'can\'t steal {donor}, you need to rearrange the letters in a word to steal it')
                    continue
                elif remaining_letters == target:
                    # nothing to steal. try the next word
                    continue
                elif remaining_letters == '':
                    # found a word to steal, no letters remaining in target
                    if depth == 0:
                        logging.debug('can\'t steal just a single word - must combine with other words or letters')
                        continue
                    else:
                        played_words_new[player].remove(donor)
                        logging.debug(indent + 'stealing ' + donor)
                        return True, self.pool_flipped, played_words_new
                else:
                    # found a word to steal for some of the letters needed - we need to go deeper
                    played_words_new[player].remove(donor)
                    logging.debug(indent + f'trying to steal: {donor} to make {target}.  remaining: {remaining_letters}')
                    result, newpool, played_words_new = self.getword(remaining_letters, played_words_new, depth+1)
                    if result:
                        return True, newpool, played_words_new

        logging.debug(indent + 'failed to find a word to steal for the letters: ' + target)
        poollist = list(self.pool_flipped)
        for letter in target:
            if letter in poollist:
                poollist.remove(letter)
            else:
                logging.debug(indent + f'failed to find this letter from {target} in the pool: {letter} - backtracking')
                return False, self.pool_flipped, played_words

        logging.debug(indent + 'taking these letters from the pool: ' + target)
        return True, ''.join(poollist), played_words

        
    def findplays(self):
        played_words = self.played_words
        letters = self.pool_flipped
        flat_word_list = []
        for player_words in played_words.values():
            for word in player_words:
                flat_word_list.append(word)

        available_letters = ''.join(flat_word_list) + letters
        available_set = set(available_letters) 

        words_from_avail_letters = []
        possible_plays = []
        for word in self.dictionary:
            if self.check_fully_contained(word, available_letters) == available_letters:
                pass
            else:
                words_from_avail_letters.append(word)

        for word in words_from_avail_letters:
            result = False
            if len(word) < self.min_word_len:
                continue
            else:
                result, _, _ = self.getword(word, self.played_words, 0)
                if result:
                    possible_plays.append(word)

        return possible_plays

        

if __name__ == '__main__':
    # play in the terminal with an imaginary and passive opponent
    logging.basicConfig(stream=sys.stderr, level=logging.ERROR)


    lang = 'en'
    min_word_length = 3
    score_handicap = 2
    game = Anagrams(lang, min_word_length, score_handicap)

    playerid = 'me'
    game.played_words[playerid] = []
    game.played_words['otherguy'] = ['CAT', 'HAT', 'FAT']


    while True:

        print()
        print('tiles in pool: ', end='')
        print(game.pool_flipped)
        for player, words in sorted(game.played_words.items())[::-1]:
            print(f'{player}:  {" ".join(words)}')
            print(f'score: {game.calc_score(words)}')

        word = input('enter word: ').upper()

        result = False

        # is it a valid word?
        if len(word) == 0:
            letter = game.flipletter()
            print('flipped over', letter)
        elif len(word) < min_word_length:
            print('That word is too short. Minimum length is', min_word_length)
        elif word not in game.dictionary:
            print(word, 'is not even a word ⚆_⚆')
        else:
            result, game.pool_flipped, game.played_words = game.getword(word, game.played_words, 0)

        if result:
            print('You claimed ' + word)
            game.played_words[playerid].append(word)
