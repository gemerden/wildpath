from collections import Mapping, Sequence


try:
    value_sequence_types = (basestring, bytearray, bytes, buffer)
except NameError:
    value_sequence_types = (str, bytearray, bytes)


def flatten(item_s):
    """ turns nested sequences and mappings into flat list """
    out = []
    if isinstance(item_s, value_sequence_types):
        out.append(item_s)
    elif isinstance(item_s, Mapping):
        out.extend(sum((flatten(v) for v in item_s.itervalues()), []))
    elif isinstance(item_s, Sequence):
        out.extend(sum((flatten(v) for v in item_s), []))
    else:
        out.append(item_s)
    return out

