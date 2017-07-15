import sys
from copy import copy
from fnmatch import fnmatchcase
from collections import Mapping, Sequence, MutableMapping, MutableSequence

from wildpath.keyparser import KeyParser

__author__ = "Lars van Gemerden"

try:
    value_sequence_types = (basestring, bytearray, bytes, buffer)
except NameError:
    value_sequence_types = (str, bytearray, bytes)


_marker = object()


class BasePath(tuple):
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

    def __new__(cls, string_or_seq=None):
        string_or_seq = string_or_seq or ()
        if isinstance(string_or_seq, str):
            return tuple.__new__(cls, string_or_seq.split(cls.sep))
        else:
            return tuple.__new__(cls, string_or_seq)

    def __getitem__(self, key):
        if isinstance(key, slice):
            return self.__class__(tuple.__getitem__(self, key))
        return tuple.__getitem__(self, key)

    def __getslice__(self, i, j):
        return self.__getitem__(slice(i, j))

    def get_in(self, obj, default=_marker):
        try:
            return self._get_in(obj)
        except (IndexError, KeyError, AttributeError):
            if default is _marker:
                raise
            return default

    def set_in(self, obj, value):
        return self._set_in(obj, value)

    def del_in(self, obj):
        return self._del_in(obj)

    def _get_in(self, obj):
        raise NotImplementedError

    def _set_in(self, obj, value):
        raise NotImplementedError

    def _del_in(self, obj):
        raise NotImplementedError

    def pop_in(self, obj):
        result = self._get_in(obj)
        self._del_in(obj)
        return result

    def has_in(self, obj):
        """checks presence of item at wildpath 'self' from the 'obj'"""
        try:
            self._get_in(obj)
        except (KeyError, IndexError, AttributeError):
            return False
        return True

    def __add__(self, other):
        return self.__class__(tuple.__add__(self, other))

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

    def _set_in(self, obj, value):
        """sets item at wildpath 'self' from the 'obj' to 'value'"""
        obj = self[:-1]._get_in(obj)
        if isinstance(obj, MutableMapping):
            obj[self[-1]] = value
        elif isinstance(obj, MutableSequence):
            obj[int(self[-1])] = value
        else:
            setattr(obj, self[-1], value)

    def _del_in(self, obj):
        """deletes item at wildpath 'self' from the 'obj'"""
        obj = self[:-1]._get_in(obj)
        if isinstance(obj, MutableMapping):
            del obj[self[-1]]
        elif isinstance(obj, MutableSequence):
            del obj[int(self[-1])]
        else:
            delattr(obj, self[-1])


def _get_with_key(value, k):
    if isinstance(value, Mapping):
        return value[k]
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

    tokens = "!&|*?:"

    algebra = KeyParser()

    _preprocessed = {}

    def __new__(cls, string_or_seq=None, parse=algebra.parse, tokens=tokens):
        self = super(WildPath, cls).__new__(cls, string_or_seq)
        preprocessed = cls._preprocessed
        for wild_key in self:
            #  if wild_cards or slicing is used, multiple results are returned and the boolean logic is applied
            if wild_key not in preprocessed and any(t in wild_key for t in tokens):
                preprocessed[wild_key] = parse(wild_key, simplify=True)
        return self

    def _get_in(self, obj, _preprocessed=_preprocessed):
        """returns item at wildpath 'self' from the 'obj'"""
        if not len(self):
            return obj
        key = self[0]
        if key in _preprocessed:  # this is not a single key or index
            if len(self) == 1:
                if isinstance(obj, Mapping):
                    return obj.__class__((k, obj[k]) for k in _preprocessed[key](*obj))
                elif isinstance(obj, Sequence):
                    return obj.__class__(obj[i] for i in _preprocessed[key](*range(len(obj))))
                else:
                    return {k: obj.__dict__[k] for k in _preprocessed[key](*obj.__dict__)}
            else:
                if isinstance(obj, Mapping):
                    return obj.__class__((k, self[1:]._get_in(obj[k])) for k in _preprocessed[key](*obj))
                elif isinstance(obj, Sequence):
                    return obj.__class__(self[1:].get_in(obj[i]) for i in _preprocessed[key](*range(len(obj))))
                else:
                    return {k: self[1:]._get_in(obj.__dict__[k]) for k in _preprocessed[key](*obj.__dict__)}
        else:
            if len(self) == 1:
                if isinstance(obj, Mapping):
                    return obj[key]
                elif isinstance(obj, Sequence):
                    return obj[int(key)]
                else:
                    return obj.__dict__[key]
            else:
                if isinstance(obj, Mapping):
                    return self[1:].get_in(obj[key])
                elif isinstance(obj, Sequence):
                    return self[1:].get_in(obj[int(key)])
                else:
                    return self[1:].get_in(obj.__dict__[key])


    def _set_in(self, obj, value, get_with_key=_get_with_key,  # speed up function access
                                  get_with_index=_get_with_index,
                                  _preprocessed=_preprocessed):
        """sets item(s) at wildpath 'self' of 'obj' to 'value'"""
        key = self[0]
        if key in _preprocessed:
            if len(self) == 1:
                if isinstance(obj, MutableMapping):
                    for k in _preprocessed[key](*obj):
                        obj[k] = get_with_key(value, k)
                elif isinstance(obj, MutableSequence):
                    for i, j in enumerate(_preprocessed[key](*range(len(obj)))):
                        obj[j] = get_with_index(value, i)
                else:
                    for k in _preprocessed[key](*obj.__dict__):
                        obj.__dict__[k] = get_with_key(value, k)
            else:
                if isinstance(obj, MutableMapping):
                    for k in _preprocessed[key](*obj):
                        self[1:]._set_in(obj[k], get_with_key(value, k))
                elif isinstance(obj, MutableSequence):
                    for i, j in enumerate(_preprocessed[key](*range(len(obj)))):
                        self[1:]._set_in(obj[j], get_with_index(value, i))
                else:
                    for k in _preprocessed[key](*obj.__dict__):
                        self[1:]._set_in(obj.__dict__[k], get_with_key(value, k))
        else:
            if len(self) == 1:
                if isinstance(obj, MutableMapping):
                    obj[key] = value
                elif isinstance(obj, MutableSequence):
                    obj[int(key)] = value
                else:
                    obj.__dict__[key] = value
            else:
                if isinstance(obj, MutableMapping):
                    self[1:]._set_in(obj[key], _get_with_key(value, key))
                elif isinstance(obj, MutableSequence):
                    self[1:]._set_in(obj[int(key)], _get_with_index(value, int(key)))
                else:
                    self[1:]._set_in(obj.__dict__[key], _get_with_key(value, key))


    def _del_in(self, obj, _preprocessed=_preprocessed):
        """deletes item(s) at wildpath 'self' from the 'obj'"""
        key = self[0]
        if key in _preprocessed:
            if len(self) == 1:
                if isinstance(obj, MutableMapping):
                    for k in _preprocessed[key](*obj):
                        del obj[k]
                elif isinstance(obj, MutableSequence):
                    for i in _preprocessed[key](*range(len(obj))):
                        obj[i] = _marker  # marked for deletion
                    obj[:] = [v for v in obj if v is not _marker]
                else:
                    for k in _preprocessed[key](*obj.__dict__):
                        del obj.__dict__[k]
            else:
                if isinstance(obj, MutableMapping):
                    for k in _preprocessed[key](*obj):
                        self[1:]._del_in(obj[k])
                elif isinstance(obj, MutableSequence):
                    for i in _preprocessed[key](*range(len(obj))):
                        self[1:]._del_in(obj[i])
                else:
                    for k in _preprocessed[key](*obj.__dict__):
                        self[1:]._del_in(obj.__dict__[k])
        else:
            if len(self) == 1:
                if isinstance(obj, MutableMapping):
                    del obj[key]
                elif isinstance(obj, MutableSequence):
                    del obj[int(key)]
                else:
                    del obj.__dict__[key]
            else:
                if isinstance(obj, MutableMapping):
                    self[1:]._del_in(obj[key])
                elif isinstance(obj, MutableSequence):
                    self[1:]._del_in(obj[int(key)])
                else:
                    self[1:]._del_in(obj.__dict__[key])




if __name__ == "__main__":
    pass