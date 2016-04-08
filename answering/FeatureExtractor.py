# encoding: utf-8
from __future__ import unicode_literals
__author__ = 'avnishs'

import re
from itertools import chain
import Queue
import threading
from spacy.en import English
from nltk.corpus import wordnet as wn
import nltk as nl


class FeatureExtractor:
    TAGGER = None
    PATTERN = re.compile(r"(\w+):(\w+) (.+)")

    '''Extract WH-WORD'''

    def extract_wh_word(self, terms):
        wh_list = ['whose', 'when', 'where', 'why', 'how', 'what', 'who', 'which','whom']
        for term in terms[::-1]:
            if term.lower() in wh_list:
                return term
        return [terms[0].lower()]

    '''Extract HEAD-WORD'''

    def extract_head(self, terms):
        if terms[0] in ['when', 'where', 'why']:
            return None

        elif terms[0] == 'how':
            return terms[1]

        elif terms[0] == 'what':
            if terms[1] in {'is', 'are'}:
                if terms[-2:] in [['composed', 'of'], ['made', 'of']] or terms[-3:] == ['made', 'out', 'of']:
                    return 'enty_subs'

                if terms[-2:] == ['used', 'for']:
                    return 'desc_reason_p2'

                if len(terms) < 5:
                    return 'desc_def_p1'

            elif terms[1] in {'do', 'does'}:
                if terms[-1:] in {'mean', 'means'}:
                    return 'desc_def_p2'

                if terms[-2:] == ['stand', 'for']:
                    return 'abbr_exp'

                if terms[0] == 'does' and terms[-1:] == 'do':
                    return 'desc_desc'

                if terms[1:4] == ['do', 'you', 'call']:
                    return 'entity_term'

            elif terms[1] in {'causes', 'cause'}:
                return 'desc_reason_p1'

        elif terms[0] == 'who' and terms[1] in {'is', 'are', 'was', 'were'} and (
                    (terms[2] == 'the' and nl.pos_tag(terms[3])[0][1].startswith('NN')) or nl.pos_tag(terms[2])[0][
                    1].startswith('NN')):
            return 'hum_desc'

        tags = nl.pos_tag(terms)
        for i in range(len(terms)):
            if tags[i][1].startswith('NN'):
                return terms[i]

    '''Extract WORD-SHAPE'''

    def extract_word_shape(self, head_word):
        if head_word.isdigit():
            return 'digits'
        elif head_word.isalpha():
            if head_word.islower():
                return 'lower'
            elif head_word.isupper():
                return 'upper'
            else:
                return 'mixed'
        else:
            return 'other'

    '''Extact N-GRAMS'''

    def extract_ngrams(self, terms, n=2):
        n_grams = map(list, zip(*[terms[i:] for i in range(n)]))
        return ['-'.join(n_gram) for n_gram in n_grams]

    def extract_tagged_seq(self, sentence):
        q1 = Queue.Queue()
        q2 = Queue.Queue()
        sentence = self.TAGGER(sentence)
        threading.Thread(target=self.extract_POS_tags, args=(sentence, q1)).start()
        threading.Thread(target=self.extract_NER_tags, args=(sentence, q2)).start()
        pos_tags = q1.get()
        ner_tags = q2.get()
        rel_ner = list()
        rel_pos = list()
        rel_cat = list()
        for i in range(len(ner_tags)):
            if len(ner_tags[i]) != 0 or pos_tags[i].startswith(u'NN') or pos_tags[i].startswith(u'VB') or \
                    pos_tags[i].startswith(u'RB') or pos_tags[i].startswith(u'JJ'):
                rel_ner.append(ner_tags[i])
                rel_pos.append(pos_tags[i])
                if pos_tags[i][0] in {'R', 'N', 'V'}:
                    word_cat = wn.synsets(sentence._py_tokens[i].text, pos_tags[i][0].lower())
                    if len(word_cat) > 0:
                        rel_cat.append(word_cat[0].lexname().split('.')[-1])

        if len(rel_cat) == 0:
            rel_cat.append(u'')

        return rel_cat, rel_ner, rel_pos

    def extract_NER_tags(self, tagged_sen, q):
        q.put([word.ent_type_ for word in tagged_sen])

    def extract_POS_tags(self, tagged_sen, q):
        q.put([word.tag_ for word in tagged_sen])

    '''Extract WORDNET SEMANTIC FTRS'''

    def extract_wordnet_sem(self):
        pass

    def extract_priors(self,wh_term):
        with open('qa_classification_pr.txt','r') as f:
            lines = f.readlines()

        for line in lines:
            match = self.PATTERN.match(line)


    def __init__(self):
        self.TAGGER = English()

    def extract_features(self, sentence):
        terms = nl.word_tokenize(sentence)
        feature_vector = list()
        feature_vector.append(self.extract_wh_word(terms))
        rel_cat, rel_ner, rel_pos = self.extract_tagged_seq(u"{}".format(sentence))
        feature_vector.append(rel_cat)
        feature_vector.append(rel_ner)
        feature_vector.append(rel_pos)
        feature_vector.append(self.extract_ngrams(rel_ner,n=2))
        feature_vector.append(self.extract_ngrams(rel_pos,n=2))
        # feature_vector.append(self.extract_head(terms))
        # feature_vector.append(terms)
        return list(chain.from_iterable(feature_vector))
