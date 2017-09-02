from collections import Mapping, Sequence

try:
    value_sequence_types = (basestring, bytearray, bytes, buffer)
except NameError:
    value_sequence_types = (str, bytearray, bytes)

BIGINT = 10**9


def flatten(item_s, depth=BIGINT):
    """ turn values in nested sequences and mappings into a flat list """
    out = []
    if isinstance(item_s, value_sequence_types):
        out.append(item_s)
    if isinstance(item_s, Mapping) and depth>-1:
        out.extend(sum((flatten(v, depth-1) for v in item_s.values()), []))
    elif isinstance(item_s, Sequence) and depth>-1:
        out.extend(sum((flatten(v, depth-1) for v in item_s), []))
    else:
        out.append(item_s)
    return out


class encoder(object):
    def __init__(self, *encoders):
        self.encoders = encoders

    def __call__(self, value):
        for encoder in self.encoders:
            value = encoder(value)
        return value


class caller(object):
    def __init__(self, encoders, *args, **kwargs):
        self.encoder = encoder(*encoders)
        self.args = args
        self.kwargs = kwargs

    def __call__(self, callable_):
        return self.encoder(callable_(*self.args, **self.kwargs))

