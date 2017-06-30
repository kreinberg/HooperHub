import os
import re
import pickle
import datetime

import tensorflow as tf

from dateutil import parser
from collections import defaultdict
from datetime import datetime, timedelta

from hooperhub.seq2seq_model import Seq2SeqModel
from hooperhub.util import EntityTable, data_utils


class Lexer(object):
    """ Responsible for creating Seq2SeqModel and running it to retrieve
        the decoded output, which is an array of entity tags that match
        with the given query. This also creates a EntityTable object by
        parsing through the entity tags and mapping them to the sentence.
    """

    def __init__(self, raw_sentence):
        """ Creates the Lexer object.
            Args:
                raw_sentence: The string taken directory from the API POST
                    request.
        """
        self.dates = {"DATE-A": None, "DATE-B": None}
        self.computed_dates = []
        vocab_path = data_utils.VOCAB_SET_PATH
        self.vocab = pickle.load(open(vocab_path, 'rb'))
        self.date_parser = parser.parse
        self.sentence_txt, self.sentence = self._prepare_sentence(raw_sentence.lower())
        self.id2target = pickle.load(open(data_utils.ID2TARGET_PATH, 'rb'))


    def _prepare_sentence(self, raw_sentence):
        """ Preprocesses the sentence before being fed into the Seq2SeqModel.
            It does this by parsing the sentence for dates and storing them
            later, as well as filtering out words that are not in the
            vocabulary set.
            Args:
                raw_sentence: The string taken directory from the API POST
                    request.
            Returns:
                A sentence that only contains vocabulary words represented as
                their token id's.
        """
        # remove all unecessary punctuation
        unecessary_punctuation = {'?', '.', ',', '!', '\'s'}
        for p in unecessary_punctuation:
            raw_sentence = raw_sentence.replace(p, ' ')
        words = raw_sentence.split()
        s_len = len(words)

        # iterate through 1-grams in words looking for mm/dd, mm/dd/yy, and·
        # mm/dd/yyyy patterns
        date_pattern = '^(0?[0-9]|1[0-2])/(0?[0-9]|1[0-9]|2[0-9]|3[0-1])(/(\d\d|\d\d\d\d))?$'
        for i in range(s_len):
            if re.match(date_pattern, words[i]):
                if not self.dates["DATE-A"]:
                    self.dates["DATE-A"] = self.date_parser(words[i]).date()
                    words[i] = "DATE-A"
                else:
                    self.dates["DATE-B"] = self.date_parser(words[i]).date()
                    words[i] = "DATE-B"

        # iterate through 3-grams in words looking for <MONTH> <DAY> <YEAR>
        # or <DAY> <MONTH> <YEAR> patterns
        for i in range(s_len-2):
            three_gram = ' '.join(words[s_len-i-3:s_len-i])
            try:
                date = self.date_parser(three_gram)
                if not self.dates["DATE-A"]:
                    self.dates["DATE-A"] = date.date()
                    words[s_len-i-3:s_len-i] = ["DATE-A"]*3
                else:
                    self.dates["DATE-B"] = date.date()
                    words[s_len-i-3:s_len-i] = ["DATE-B"]*3
            except:
                pass

        # iterate through 2-grams in words looking for <MONTH> <DAY> patterns
        for i in range(s_len-1):
            two_gram = ' '.join(words[s_len-i-2:s_len-i])
            try:
                date = self.date_parser(two_gram)
                if not self.dates["DATE-A"]:
                    self.dates["DATE-A"] = date.date()
                    words[s_len-i-2:s_len-i] = ["DATE-A"]*2
                else:
                    self.dates["DATE-B"] = date.date()
                    words[s_len-i-2:s_len-i] = ["DATE-B"]*2
            except:
                pass

        # iterate through words looking for YYYY, YY-YY, and YYYY-YY patterns
        # and recording them as seasons
        year_pattern1 = "^(\d\d\d\d-\d\d)$"
        year_pattern2 = "^(\d\d-\d\d)$"
        year_pattern3 = "^(\d\d\d\d)$"
        for i in range(s_len):
            if re.match(year_pattern1, words[i]):
                self.dates["SEASON"] = int(words[i][:4])
            elif re.match(year_pattern2, words[i]):
                self.dates["SEASON"] = 1900 + int(words[i][:2])
                if int(words[i][:2]) < 45:
                    self.dates["SEASON"] += 100
            elif re.match(year_pattern3, words[i]):
                self.dates["SEASON"] = int(words[i])-1

        sentence = []
        last_word = ''
        # filter out all non-vocabulary words
        for w in words:
            if w in self.vocab and last_word != w:
                sentence.append(w)
            last_word = w

        word2id = pickle.load(open(data_utils.INPUT2ID_PATH, 'rb'))
        return sentence, data_utils.sentence_to_token_ids(sentence, word2id)


    def decode(self):
        """ Creates a Seq2SeqModel object and runs the sentence through it.
            Returns:
                The decoded output as a list of tags.
        """
        tf.reset_default_graph()
        model = Seq2SeqModel(1100,  # source_vocab_size
                             200,   # target_vocab_size
                             512,   # layer_size
                             50,    # batch_size
                             0.001, # learn_rate
                             train=False)
        with tf.Session() as sess:
            data_dir = os.path.join(os.environ['HH_ROOT'],
                                    'hooperhub/data/')
            ckpt = tf.train.get_checkpoint_state(data_dir)
            if ckpt and tf.train.checkpoint_exists(ckpt.model_checkpoint_path):
                model_meta_graph = os.path.join(data_dir, 'model.ckpt.meta')
                saver = tf.train.import_meta_graph(model_meta_graph)
                saver.restore(sess, tf.train.latest_checkpoint(data_dir))
                sentence_batch, sentence_len = model.get_batch([self.sentence])
                targets = [0] * len(self.sentence)
                target_batch, _ = model.get_batch([targets])
                input_feed = {
                    model.enc_inputs: sentence_batch,
                    model.enc_inputs_len: sentence_len,
                    model.dec_targets: target_batch
                }
                predict = model.make_prediction(sess, input_feed)
                target_list = []
                for elem in predict.T[0]:
                    target_list.append(self.id2target[elem])
                return target_list
            else:
                print("No checkpoint exists. Please run the trainer first.")
                return None



    def _read_entity(self, entity_table, entity_name, entity):
        """ Helper method for the parser.
            Args:
                entity_name: A string containing the entity tag name.
                entity: A string with the entity value.
            Returns:
                A method name that the entity table will execute as well as the
                    parameter for that method.
        """
        if entity_name == 'PLAYER':
            entity_table.player_name = ' '.join(entity)
        if entity_name == 'PLAYOFFS':
            entity_table.playoff_rd = 1
        if entity_name == 'DATE-A':
            self.computed_dates.append(self.dates['DATE-A'])
        if entity_name == 'DATE-B':
            self.computed_dates.append(self.dates['DATE-B'])
        if entity_name == 'BEFORE_DATE':
            if 'DATE-A' in entity:
                entity_table.end_date = self.dates['DATE-A']
            elif 'DATE-B' in entity:
                entity_table.end_date = self.dates['DATE-B']
        if entity_name == 'AFTER_DATE':
            if 'DATE-A' in entity:
                entity_table.start_date = self.dates['DATE-A']
            elif 'DATE-B' in entity:
                entity_table.start_date = self.dates['DATE-B']
        if entity_name == 'HOME':
            entity_table.home_game = True
        if entity_name == 'AWAY':
            entity_table.home_game = False
        if entity_name == 'START':
            entity_table.started_game = True
        if entity_name == 'BENCH':
            entity_table.started_game = False
        if entity_name == 'WIN':
            entity_table.game_won = True
        if entity_name == 'LOSS':
            entity_table.game_won = False
        if entity_name.startswith('OPP'):
            entity_table.played_against = int(entity_name.replace('OPP-', ''))
        if entity_name.startswith('STAT'):
            entity_table.add_stat(entity_name.replace('STAT-', '').lower())


    def parse(self, tags):
        """ Creates a EntityTable object that will be read by the Interpreter.
            Args:
                tags: A list of entity tags given from the decoder.
            Returns:
                A EntityTable which includes useful query information (e.g.,
                player_name, playoff_rd, etc.).
        """
        entity_table = EntityTable()
        s_len = len(self.sentence_txt)
        idx = 0
        et_dict = defaultdict(list)
        # ensure that loop will break after 50 loops
        safety = 0
        while idx < s_len:
            if safety > 50:
                break
            if tags[idx].startswith('B'):
                tag_name = tags[idx][2:]
                et_dict[tag_name].append(self.sentence_txt[idx])
                idx += 1
                while idx < s_len and tags[idx].startswith('I'):
                    et_dict[tag_name].append(self.sentence_txt[idx])
                    idx += 1
            safety += 1
        for k,v in et_dict.items():
            self._read_entity(entity_table, k,v)
        self.computed_dates = sorted(self.computed_dates)
        if "SEASON" in self.dates:
            season = self.dates["SEASON"]
            entity_table.start_date = datetime(season, 10, 1).date()
            entity_table.end_date = datetime(season+1, 7, 1).date()
        elif len(self.computed_dates) == 1:
            entity_table.start_date = self.computed_dates[0] - timedelta(days=1)
            entity_table.end_date = self.computed_dates[0] + timedelta(days=1)
        elif len(self.computed_dates) > 1:
            entity_table.start_date = self.computed_dates[0]
            entity_table.end_date = self.computed_dates[1]
        return entity_table


