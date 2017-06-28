""" Data utilities used for training and natural language processing """

import os
import re
import pickle


PAD = "PAD"
EOS = "EOS"
START_VOCAB = [PAD, EOS]

try:
    PROJECT_ROOT = os.environ['HH_ROOT']
except KeyError:
    raise Exception("Please export HH_ROOT as the project directory")
VOCAB_SET_PATH = os.path.join(PROJECT_ROOT, 'hooperhub/data/pkl/vocab_set.pkl')
INPUT2ID_PATH = os.path.join(PROJECT_ROOT, 'hooperhub/data/pkl/input2id.pkl')
TARGET2ID_PATH = os.path.join(PROJECT_ROOT, 'hooperhub/data/pkl/target2id.pkl')
ID2INPUT_PATH = os.path.join(PROJECT_ROOT, 'hooperhub/data/pkl/id2input.pkl')
ID2TARGET_PATH = os.path.join(PROJECT_ROOT, 'hooperhub/data/pkl/id2target.pkl')

TRAINING_INPUT_PATH = os.path.join(PROJECT_ROOT,
                                   'hooperhub/data/training.in')
TRAINING_TARGET_PATH = os.path.join(PROJECT_ROOT,
                                    'hooperhub/data/training.tgt')
TESTING_INPUT_PATH = os.path.join(PROJECT_ROOT,
                                  'hooperhub/data/testing.in')
TESTING_TARGET_PATH = os.path.join(PROJECT_ROOT,
                                  'hooperhub/data/testing.tgt')


def sentence_to_token_ids(sentence, word2id):
    """ Gets token id's of each word in the sentence and returns a list of
        those words. Is called by data_to_token_ids and the Lexer.
        Args:
            sentence: A list of word tokens.
            word2id: A dictionary that maps words to its given id. This can
                be for the input or target vocabulary.
    """
    tokenized_sentence = []
    for word in sentence:
        tokenized_sentence.append(str(word2id[word]))
    return tokenized_sentence


def data_to_token_ids(data_path, use_existing_vocab=True):
    """ Convert a set of training pairs to their respective token id's.
        Args:
            data_path: Path to where training pairs are located.
            use_existing_vocab: A boolean that determines whether or not to use
                a pre-existing vocabulary or not. If false, then a new
                vocabulary set is created.
    """
    input2id_exists = os.path.isfile(INPUT2ID_PATH)
    target2id_exists = os.path.isfile(TARGET2ID_PATH)
    id2input_exists = os.path.isfile(ID2INPUT_PATH)
    id2target_exists = os.path.isfile(ID2TARGET_PATH)
    all_files_exist = (input2id_exists and target2id_exists and
                      id2input_exists and id2target_exists and use_existing_vocab)
    # Create the vocabulary files if they do not exist
    if not all_files_exist:
        input_vocab, target_vocab = initialize_vocabulary(data_path)
        create_vocabulary(input_vocab, target_vocab)
    else:
        print("* Using an already existing vocabulary.")

    print("* Saving token ID's...")
    input_list, target_list = [], []
    input2id = pickle.load(open(INPUT2ID_PATH, 'rb'))
    target2id = pickle.load(open(TARGET2ID_PATH, 'rb'))
    with open(data_path, 'r') as f:
        for line in f:
            data_pair = tuple(map(eval, line.split('\t')))
            input_list.append(sentence_to_token_ids(data_pair[0],
                                                    input2id))
            target_list.append(sentence_to_token_ids(data_pair[1],
                                                     target2id))
    input_path = TRAINING_INPUT_PATH
    target_path = TRAINING_TARGET_PATH
    with open(input_path, 'w') as input_file:
        for line in input_list:
            input_file.write(" ".join(line)+'\n')
    with open(target_path, 'w') as target_file:
        for line in target_list:
            target_file.write(" ".join(line)+'\n')

    print("* Data preparation complete!")


def create_vocabulary(input_vocab, target_vocab):
    """ Creates vocabulary files for converting source/target data to
        their id's, and vice versa.
        Args:
            input_vocab: A list of input vocabulary.
            target_vocab: A list of target vocabulary.
    """
    print("* Creating vocabulary files...")
    id2input = START_VOCAB + list(input_vocab)
    id2target = START_VOCAB + list(target_vocab)
    input2id, target2id = {}, {}
    for i in range(len(id2input)):
        input2id[id2input[i]] = i
    for i in range(len(id2target)):
        target2id[id2target[i]] = i
    pickle.dump(id2input, open(ID2INPUT_PATH, 'wb'))
    pickle.dump(id2target, open(ID2TARGET_PATH, 'wb'))
    pickle.dump(input2id, open(INPUT2ID_PATH, 'wb'))
    pickle.dump(target2id, open(TARGET2ID_PATH, 'wb'))
    print("  * All vocabulary files created.")


def initialize_vocabulary(data_path):
    """ Initializes sets of vocabulary based on the training data.
        Args:
            data_path: Path to where the training/testing data is located.
        Returns:
            A 2-item tuple with the input and target vocabulary sets.
    """
    print("* Initializing vocabulary...")
    input_vocab, target_vocab = set(), set()

    with open(data_path, 'r') as f:
        for line in f:
            data_pair = tuple(map(eval, line.split('\t')))
            input_vocab = input_vocab.union(data_pair[0])
            target_vocab = target_vocab.union(data_pair[1])
    print("* Created vocabulary sets")
    print("  * Input vocab size: {}".format(len(input_vocab)))
    print("  * Target vocab size: {}".format(len(target_vocab)))

    print("* Writing input vocab as vocab_set.pkl.")
    pickle.dump(input_vocab, open(VOCAB_SET_PATH, 'wb'))

    return input_vocab, target_vocab


