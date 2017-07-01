import sys
from copy import deepcopy, copy

from fnmatch import fnmatchcase
from itertools import starmap
from collections import Mapping, Sequence, MutableMapping, MutableSequence


__author__ = "Lars van Gemerden"

if sys.version_info[0] < 3:
    value_sequence_types = (basestring, bytearray, bytes, buffer)
else:
    value_sequence_types = (str, bytearray, bytes)


_marker = object()


class BasePath(list):
    """
    Helper classes to be able to use '.' separated paths to access elements in objects, lists and dictionaries.
    """
    sep = "."


    @classmethod
    def items(cls, obj, all=False, _path=None):
        """ iterates over all (wildpath, value) items in the (nested) object """
        if _path is None:
            _path = cls()
        elif all:
            yield _path, copy(obj)
        if isinstance(obj, value_sequence_types):
            if not all:
                yield _path, obj
        elif isinstance(obj, Mapping):
            for key, sub_obj in obj.items():
                for sub_path, sub_obj in cls.items(sub_obj, all, _path + cls(key)):
                    yield sub_path, sub_obj
        elif isinstance(obj, Sequence):
            for index, sub_obj in enumerate(obj):
                for sub_path, sub_obj in cls.items(sub_obj, all, _path + cls(str(index))):
                    yield sub_path, sub_obj
        elif hasattr(obj, "__dict__"):
            for key, sub_obj in obj.__dict__.items():
                for sub_path, sub_obj in cls.items(sub_obj, all, _path + cls(key)):
                    yield sub_path, sub_obj
        elif not all:
            yield _path, obj

    @classmethod
    def paths(cls, obj, all=False):
        for sub_path, _ in cls.items(obj, all=all):
            yield sub_path

    @classmethod
    def values(cls, obj, all=False):
        for _, sub_obj in cls.items(obj, all=all):
            yield sub_obj

    def __init__(self, string_or_seq=None):
        string_or_seq = string_or_seq or ()
        if isinstance(string_or_seq, str):
            list.__init__(self, string_or_seq.split(self.sep))
        else:
            list.__init__(self, string_or_seq)

    def __getitem__(self, key):
        if isinstance(key, slice):
            return self.__class__(list.__getitem__(self, key))
        return list.__getitem__(self, key)

    def __getslice__(self, i, j):
        return self.__getitem__(slice(i, j))

    def get_in(self, obj, default=_marker):
        try:
            return self._get_in(obj)
        except (IndexError, KeyError, AttributeError):
            if default is _marker:
                raise
            return default

    def _get_in(self, obj):
        raise NotImplementedError

    def set_in(self, obj, value):
        raise NotImplementedError

    def del_in(self, obj):
        raise NotImplementedError

    def pop_in(self, obj):
        result = self._get_in(obj)
        self.del_in(obj)
        return result

    def has_in(self, obj):
        """checks presence of item at wildpath 'self' from the 'obj'"""
        try:
            self._get_in(obj)
        except (KeyError, IndexError, AttributeError):
            return False
        return True

    def __add__(self, other):
        return self.__class__(list.__add__(self, other))

    def __str__(self):
        return self.sep.join(str(v) for v in self)


class Path(BasePath):
    """
    Fast implementation of the baseclass that does not allow wildcards and slicing.
    """

    def _get_in(self, obj):
        """returns item at wildpath 'self' from the 'obj'"""
        for key in self:
            if isinstance(obj, Mapping):
                obj = obj[key]
            elif isinstance(obj, Sequence):
                obj = obj[int(key)]
            else:
                obj = getattr(obj, key)
        return obj

    def set_in(self, obj, value):
        """sets item at wildpath 'self' from the 'obj' to 'value'"""
        obj = self[:-1]._get_in(obj)
        if isinstance(obj, MutableMapping):
            obj[self[-1]] = value
        elif isinstance(obj, MutableSequence):
            obj[int(self[-1])] = value
        else:
            setattr(obj, self[-1], value)

    def del_in(self, obj):
        """deletes item at wildpath 'self' from the 'obj'"""
        obj = self[:-1]._get_in(obj)
        if isinstance(obj, MutableMapping):
            del obj[self[-1]]
        elif isinstance(obj, MutableSequence):
            del obj[int(self[-1])]
        else:
            delattr(obj, self[-1])


def parse_slice(wild_slice, parse_item=lambda v: int(v) if v else None):
    try:
        return slice(*map(parse_item, wild_slice.split(':')))
    except (ValueError, TypeError) as e:
        raise IndexError("sequence index wildcard can only be '*' or slice (e.g. 1:3)")


def _iter_indices(wild_slice, count):
    if '*' in wild_slice or ':' in wild_slice or '!' in wild_slice:
        negate = (wild_slice[0] == "!")
        if negate:
            wild_slice = wild_slice[1:]
        if wild_slice == "*":
            slice_ = slice(None)
        else:
            slice_ = parse_slice(wild_slice)

        slice_indices = range(*slice_.indices(count))
        if negate:
            if slice_.step and slice_.step < 0:
                return (i for i in reversed(range(count)) if i not in slice_indices)
            return (i for i in range(count) if i not in slice_indices)
        return slice_indices
    else:
        return [int(wild_slice)]


def _iter_keys(wild_key, keys):
    if '*' in wild_key or '?' in wild_key or "|" in wild_key or '!' in wild_key:
        if wild_key[0] == '!':
            wild_keys = wild_key[1:].split('|')
            return (k for k in keys if not any(fnmatchcase(k, key) for key in wild_keys))
        wild_keys = wild_key.split('|')
        return (k for k in keys if any(fnmatchcase(k, key) for key in wild_keys))
    else:
        return [wild_key]


def _get_with_key(value, k):
    try:
        return value.__getitem__(k)
    except AttributeError:
        return value


def _get_with_index(value, index):
    if isinstance(value, value_sequence_types):
        return value
    if isinstance(value, Sequence):
        return value[index]
    return value


class WildPath(BasePath):
    """
    Implementation of the baseclass that allows for wildcards, multiple keys and slicing.
    """

    sep = "."

    def _get_in(self, obj):
        """returns item at wildpath 'self' from the 'obj'"""
        if not len(self):
            return obj
        elif isinstance(obj, Mapping):
            return obj.__class__((k, self[1:]._get_in(obj[k])) for k in _iter_keys(self[0], obj))
        elif isinstance(obj, Sequence):
            return obj.__class__(self[1:]._get_in(obj[i]) for i in _iter_indices(self[0], len(obj)))
        else:
            return {k: self[1:]._get_in(obj[k])  for k in _iter_keys(self[0], obj.__dict__)}

    def set_in(self, obj, value):
        """sets item(s) at wildpath 'self' from the 'obj' to 'value'"""
        key = self[0]
        if len(self) == 1:
            if isinstance(obj, MutableMapping):
                for k in _iter_keys(key, obj):
                    obj[k] = _get_with_key(value, k)
            elif isinstance(obj, MutableSequence):
                for i in _iter_indices(key, len(obj)):
                    obj[i] = _get_with_index(value, i)
            else:
                for k in _iter_keys(key, obj.__dict__):
                    setattr(obj, _get_with_key(value, k))
        else:
            if isinstance(obj, MutableMapping):
                for k in _iter_keys(key, obj):
                    self[1:].set_in(obj[k], _get_with_key(value, k))
            elif isinstance(obj, MutableSequence):
                for i in _iter_indices(key, len(obj)):
                    self[1:].set_in(obj[i], _get_with_index(value, i))
            else:
                for k in _iter_keys(key, obj.__dict__):
                    self[1:].set_in(obj.__dict__[k], _get_with_key(value, k))

    def del_in(self, obj):
        """deletes item(s) at wildpath 'self' from the 'obj'"""
        key = self[0]
        if len(self) == 1:
            if isinstance(obj, MutableMapping):
                for k in _iter_keys(key, obj):
                    del obj[k]
            elif isinstance(obj, MutableSequence):
                for i in _iter_indices(key, len(obj)):
                    del obj[i]
            else:
                for k in _iter_keys(key, obj.__dict__):
                    delattr(obj, k)
        else:
            if isinstance(obj, MutableMapping):
                for k in _iter_keys(key, obj):
                    self[:-1].del_in(obj[k])
            elif isinstance(obj, MutableSequence):
                for i in _iter_indices(key, len(obj)):
                    self[:-1].del_in(obj[i])
            else:
                for k in _iter_keys(key, obj.__dict__):
                    self[:-1].del_in(obj.__dict__[k])



if __name__ == "__main__":
    pass