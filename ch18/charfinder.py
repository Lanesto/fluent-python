#!/usr/local/bin/python
import re
import sys
import warnings
import pickle
import unicodedata
import functools
import itertools
from collections import namedtuple


RE_WORD = re.compile(r"\w+")
RE_UNICODE_NAME = re.compile(r"^[A-Z0-9 -]+$")
RE_UNICODE_CODEPOINT = re.compile(r"U\+([0-9A-F]{4,6})")

INDEX_FILENAME = "chartfinder_index.pickle"
MINIMUM_SAVE_LEN = 10000
CJK_UNI_PREFIX = "CJK UNIFIED IDEOGRAPH"
CJK_CMP_PREFIX = "CJK COMPATIBILITY IDEOGRAPH"

sample_chars = [
    "$",  # DOLLAR SIGN
    "A",  # LATIN CAPITAL LETTER A
    "a",  # LATIN SMALL LETTER A
    "\u20a0",  # EURO-CURRENCY SIGN
    "\u20ac",  # EURO SIGN
]

CharDescription = namedtuple("CharDescription", "code_str char name")
QueryResult = namedtuple("QueryResult", "count items")


def tokenize(text):
    for match in RE_WORD.finditer(text):
        yield match.group().upper()


def query_type(text):
    text = text.upper()
    if "U+" in text:
        return "CODEPOINT"
    elif RE_UNICODE_NAME.match(text):
        return "NAME"
    else:
        return "CHARACTERS"


class UnicodeNameIndex:
    def __init__(self, chars=None):
        self.load(chars)

    def load(self, chars=None):
        self.index = None
        if chars is None:
            try:
                with open(INDEX_FILENAME, "rb") as fp:
                    self.index = pickle.load(fp)
            except OSError:
                pass

        if self.index is None:
            self.build_index(chars)

        if len(self.index) > MINIMUM_SAVE_LEN:
            try:
                self.save()
            except OSError as exc:
                warnings.warn(f"could not save {INDEX_FILENAME!r}: {exc}")

    def save(self):
        with open(INDEX_FILENAME, "wb") as fp:
            pickle.dump(self.index, fp)

    def build_index(self, chars=None):
        if chars is None:
            chars = (chr(i) for i in range(32, sys.maxunicode))

        index = {}
        for char in chars:
            try:
                name = unicodedata.name(char)
            except ValueError:
                continue

            if name.startswith(CJK_UNI_PREFIX):
                name = CJK_UNI_PREFIX
            elif name.startswith(CJK_CMP_PREFIX):
                name = CJK_CMP_PREFIX

            for word in tokenize(name):
                index.setdefault(word, set()).add(char)

        self.index = index

    def word_rank(self, top=None):
        res = [(len(self.index[key]), key) for key in self.index]
        res.sort(key=lambda item: (-item[0], item[1]))
        if top is not None:
            res = res[:top]

        return res

    def word_report(self, top=None):
        for postings, key in self.word_rank(top):
            print(f"{postings:5} {key}")

    def find_chars(self, query, start=0, stop=None):
        stop = sys.maxsize if stop is None else stop
        result_sets = []
        for word in tokenize(query):
            chars = self.index.get(word)
            if chars is None:
                result_sets = []
                break

            result_sets.append(chars)

        if not result_sets:
            return QueryResult(0, ())

        result = functools.reduce(set.intersection, result_sets)
        result = sorted(result)
        result_iter = itertools.islice(result, start, stop)
        return QueryResult(len(result), (char for char in result_iter))

    def describe(self, char):
        code_str = f"U+{ord(char):04X}"
        name = unicodedata.name(char)
        return CharDescription(code_str, char, name)

    def find_descriptions(self, query, start=0, stop=None):
        for char in self.find_chars(query, start, stop).items:
            yield self.describe(char)

    def get_descriptions(self, chars):
        for char in chars:
            yield self.describe(char)

    def describe_str(self, char):
        return "{:7}\t{}\t{}".format(*self.describe(char))

    def find_description_strs(self, query, start=0, stop=None):
        for char in self.find_chars(query, start, stop).items:
            yield self.describe_str(char)

    @staticmethod
    def status(query, counter):
        if counter == 0:
            msg = "No match"
        elif counter == 1:
            msg = "1 match"
        else:
            msg = f"{counter} matches"

        return f"{msg} for {query!r}"


def main(*args):
    index = UnicodeNameIndex()
    query = " ".join(args)
    n = 0
    for n, line in enumerate(index.find_description_strs(query), 1):
        print(line)

    print("({})".format(index.status(query, n)))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(*sys.argv[1:])
    else:
        print("usage: {} word1 [word2 ...]".format(sys.argv[0]))
