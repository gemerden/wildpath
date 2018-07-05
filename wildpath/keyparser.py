from fnmatch import fnmatchcase

import sys
from boolean import BooleanAlgebra, AND, OR, NOT, Symbol
from boolean import ParseError, TOKEN_SYMBOL, TOKEN_NOT, TOKEN_AND, TOKEN_OR, TOKEN_LPAR, TOKEN_RPAR
from boolean.boolean import PARSE_UNKNOWN_TOKEN

from wildpath.tools import dedoubled

try:
    basestring
except NameError:
    basestring = str


class WildSymbol(Symbol):

    ALL = object()

    def __init__(self, wild_key, parse_slice_item=lambda v: int(v) if v else None):
        if wild_key == '*' or wild_key == ':':
            super(WildSymbol, self).__init__(self.ALL)
        elif ':' in wild_key:
            super(WildSymbol, self).__init__(slice(*map(parse_slice_item, wild_key.split(':'))))
        else:
            super(WildSymbol, self).__init__(wild_key)

    def __call__(self, *keys):
        wild_key = self.obj
        if not len(keys) or wild_key is self.ALL:
            return list(keys)
        if isinstance(keys[0], str):  # all keys are str or all keys are int
            return [k for k in keys if fnmatchcase(k, wild_key)]
        try:
            index = int(wild_key)
        except TypeError:
            return list(range(*wild_key.indices(len(keys))))
        else:
            while index < 0:
                index += len(keys)
            return [index] if index in keys else []

    def __lt__(self, other):
        """ due to small bug in boolean.py """
        return NotImplemented



class LIST_NOT(NOT):

    def __call__(self, *keys):
        not_keys = self.args[0](*keys)
        return [k for k in keys if k not in not_keys]


class LIST_OR(OR):

    def __call__(self, *keys):
        return dedoubled(sum((a(*keys) for a in self.args), []))


class LIST_AND(AND):

    def __call__(self, *keys):
        key_lists = [a(*keys) for a in self.args]
        return [k for k in key_lists[0] if all(k in kl for kl in key_lists)]


class KeyParser(BooleanAlgebra):

    DEFAULT_TOKENS = {
        '&': TOKEN_AND,
        '|': TOKEN_OR,
        '!': TOKEN_NOT,
        '(': TOKEN_LPAR,
        ')': TOKEN_RPAR,
    }

    def __init__(self, TOKENS=None, *args, **kwargs):
        super(KeyParser, self).__init__(Symbol_class=WildSymbol,
                                        OR_class=LIST_OR,
                                        AND_class=LIST_AND,
                                        NOT_class=LIST_NOT,
                                        *args, **kwargs)
        self.TOKENS = TOKENS or self.DEFAULT_TOKENS

    def tokenize(self, expr):
        """
        Return an iterable of 3-tuple describing each token given an expression
        unicode string.

        This 3-tuple contains (token, token string, position):
        - token: either a Symbol instance or one of TOKEN_* token types..
        - token string: the original token string.
        - position: starting position of the token in the original string

        The token position is used only for error reporting and can be None or
        empty.

        Raise ParseError on errors. The ParseError.args is a tuple of:
        (token_string, position, error message)

        You can use this tokenizer as a base to override the tokens used to parse the original expression string.

        A TOKEN_SYMBOL is returned for any string without tokens
        """
        if not isinstance(expr, basestring):
            raise TypeError('expr must be string but it is %s.' % type(expr))
        TOKENS = self.TOKENS
        length = len(expr)
        position = 0
        while position < length:
            tok = expr[position]

            sym = tok not in TOKENS
            if sym:
                position += 1
                while position < length:
                    char = expr[position]
                    if char not in TOKENS:
                        position += 1
                        tok += char
                    else:
                        break
                position -= 1

            try:
                yield TOKENS[tok], tok, position
            except KeyError:
                if sym:
                    yield TOKEN_SYMBOL, tok, position
                else:
                    raise ParseError(token_string=tok, position=position, error_code=PARSE_UNKNOWN_TOKEN)
            position += 1


if __name__ == "__main__":
    pass

