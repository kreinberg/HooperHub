#!/usr/bin/env python3

""" A small demonstration of the NER tagger implemented in HooperHub """

# disable all TF debugging information
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import sys

from prettytable import PrettyTable

from hooperhub.lexer import Lexer
from hooperhub.util import EntityTable


if __name__ == '__main__':
    sys.stdout.write("Enter your query below ([q/Q] to quit)\n")
    sys.stdout.write("> ")
    sys.stdout.flush()
    raw_sentence = sys.stdin.readline().strip()
    while raw_sentence not in {'', 'q', 'Q'}:
        try:
            lexer = Lexer(raw_sentence)
            ent_tags = lexer.decode()
            print("Output tags: ", end='')
            print(ent_tags)
            ent_tab = lexer.parse(ent_tags)
            pt = PrettyTable(['entity name', 'entity value'])
            for k,v in ent_tab:
                pt.add_row([k,v])
            print(pt)
        except Exception as e:
            print(e)
        finally:
            sys.stdout.write("> ")
            sys.stdout.flush()
            raw_sentence = sys.stdin.readline().strip()


