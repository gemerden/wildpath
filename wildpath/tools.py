from typing import Mapping, Sequence

value_sequence_types = (str, bytearray, bytes)

BIGINT = 10**9


def dedoubled(lst):
    out_list = []
    for item in lst:
        if item not in out_list:
            out_list.append(item)
    return out_list


def flatten(item_s, depth=BIGINT):
    """ turn values in nested sequences and mappings into a flat list """
    out = []
    if isinstance(item_s, value_sequence_types):
        out.append(item_s)
    elif isinstance(item_s, Mapping) and depth>-1:
        out.extend(sum((flatten(v, depth-1) for v in item_s.values()), []))
    elif isinstance(item_s, Sequence) and depth>-1:
        out.extend(sum((flatten(v, depth-1) for v in item_s), []))
    else:
        out.append(item_s)
    return out

