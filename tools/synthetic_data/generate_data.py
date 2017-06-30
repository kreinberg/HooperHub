#!/usr/bin/env python3


import os
import argparse
import json
import pickle
import random

from random import *

PROJECT_ROOT = os.environ['HH_ROOT']
json_phrases_path = os.path.join(PROJECT_ROOT, 'tools/synthetic_data/phrases.json')
player_dict_path = os.path.join(PROJECT_ROOT, 'tools/synthetic_data/players.pkl')
team_dict_path = os.path.join(PROJECT_ROOT, 'tools/synthetic_data/teams.pkl')
JSON_PHRASES = json.loads(open(json_phrases_path, 'r').read())
PLAYER_DICT = pickle.load(open(player_dict_path, 'rb'))
TEAM_DICT = pickle.load(open(team_dict_path, 'rb'))


def write_pairs(pairs):
    queries = []
    tags = []
    for p in pairs:
        for i in range(len(p[1])):
            queries.append(p[1][i])
            prefix = "B-" if i == 0 else "I-"
            tags.append(prefix+p[0])
    print(str(queries)+'\t'+str(tags))


def select_condition(cond_type):
    # the key for each condition type is its IOB tag and the value is a
    # randomly selected phrase associated with that tag
    cond_key = choice(list(JSON_PHRASES[cond_type].keys()))
    if cond_key != "NONE":
        cond_value = choice(JSON_PHRASES[cond_type][cond_key])
        return cond_key, cond_value
    return None, None


def flatten_date_phrase(phrase):
    flat_phrase = []
    for word in phrase:
        if type(word) == list:
            flat_phrase.append(choice(word))
        else:
            flat_phrase.append(word)
    return ' '.join(flat_phrase).split()


def flatten_stat_phrase(phrase):
    # randomly unfold a list of sub phrases into one phrase
    flat_phrase = []
    for word in phrase:
        if type(word) == list:
            flat_phrase.append(choice(word))
        elif word[0] == '<':
            flat_phrase.append(choice(JSON_PHRASES[word[1:-1]]))
        else:
            flat_phrase.append(word)
    return ' '.join(flat_phrase).split()


def generate_example():
    phrases = {}

    # randomly select player
    player_name = PLAYER_DICT[choice(list(PLAYER_DICT))]
    phrases['PLAYER'] = player_name.split()

    phrases.update([select_condition('home_or_away'),
                    select_condition('start_or_bench'),
                    select_condition('win_or_loss'),
                    select_condition('playoffs')])

    # randomly select one team from DB (may not be used)
    team_key = choice(list(TEAM_DICT.keys()))
    team_names = TEAM_DICT[team_key][1]

    opp_key, opp_phrase = select_condition('opp')
    opp_value = None
    if opp_key:
        opp_key += '-' + str(team_key)
        opp_value0 = choice(opp_phrase[0])
        opp_value1 = opp_phrase[1].replace('<TEAM>',
                                           choice(team_names))
        opp_value = [opp_value0, opp_value1]
    phrases[opp_key] = opp_value

    # select between 0 and 1 stat phrases
    stat_count = choice(range(2))
    stats = sample(list(JSON_PHRASES['stats'].keys()), stat_count)
    for st in stats:
        stat_phrase = choice(JSON_PHRASES['stats'][st])
        stat_value = flatten_stat_phrase(stat_phrase)
        phrases[st] = stat_value

    # select a date phrase
    date_key = choice(list(JSON_PHRASES['dates'].keys()))
    if date_key == "DATE":
        dates = sample(JSON_PHRASES['dates'][date_key], choice([1,2]))
        for date in dates:
            date_value = flatten_date_phrase(date)
            phrases[date_value[0]] = date_value
    elif date_key != "NONE":
        date_phrase = choice(JSON_PHRASES['dates'][date_key])
        date_value = flatten_date_phrase(date_phrase)
        phrases[date_key] = date_value

    if None in phrases:
        del phrases[None]

    phrase_list = list(phrases.items())
    shuffle(phrase_list)

    write_pairs(phrase_list)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--num_examples',
                        type = int,
                        default = 100,
                        help = "number of training/testing examples to produce")
    args = parser.parse_args()

    for _ in range(args.num_examples):
        generate_example()


