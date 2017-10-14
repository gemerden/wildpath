from copy import copy
from collections import Mapping, Sequence, MutableMapping, MutableSequence
from inspect import ismethod

from wildpath.keyparser import KeyParser
from wildpath.tools import value_sequence_types, flatten

__author__ = "Lars van Gemerden"


_marker = object()


class BasePath(tuple):
    """
    Helper classes to be able to use '.' separated paths to access elements in objects, lists and dictionaries.
    """
    sep = "."

    @classmethod
    def _get_object_items(cls, obj, _call=False):
        for name in dir(obj):
            if not (name.startswith("__") and name.endswith("__")):
                attr = getattr(obj, name)
                if name in obj.__dict__ or (_call and callable(attr)):
                    yield name, attr
                else:
                    cls_attr = getattr(obj.__class__, name, None)
                    if not callable(cls_attr):
                        if (isinstance(cls_attr, property) or
                                hasattr(cls_attr, "__get__") or
                                hasattr(cls_attr, "__set__")):
                            yield name, attr

    @classmethod
    def get_object_dict(cls, obj):
        return {name: getattr(obj, name) for name in dir(obj) if not (name.startswith("__") and name.endswith("__"))
                and not callable(getattr(obj, name))}

    @classmethod
    def items(cls, obj, all=False, _path=None, _call=False):
        """ iterates over all (wildpath, value) items in the (nested) object """
        if _path is None:
            _path = cls()
        elif all:
            yield _path, copy(obj)
        if _call and callable(obj):
            yield _path, obj
        elif isinstance(obj, value_sequence_types):
            if not all:
                yield _path, obj
        elif isinstance(obj, Mapping):
            for key, sub_obj in obj.items():
                for sub_path, sub_obj in cls.items(sub_obj, all, _path + cls(key), _call=_call):
                    yield sub_path, sub_obj
        elif isinstance(obj, Sequence):
            for index, sub_obj in enumerate(obj):
                for sub_path, sub_obj in cls.items(sub_obj, all, _path + cls(str(index)), _call=_call):
                    yield sub_path, sub_obj
        elif hasattr(obj, "__dict__"):
            for key, sub_obj in cls._get_object_items(obj, _call):
                for sub_path, sub_obj in cls.items(sub_obj, all, _path + cls(key), _call=_call):
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
        return self._get_in(obj, default)

    def set_in(self, obj, value):
        return self._set_in(obj, value)

    def del_in(self, obj):
        return self._del_in(obj)

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

    def call_in(self, obj, *args, **kwargs):
        raise NotImplementedError

    def _get_in(self, obj, default=_marker):
        raise NotImplementedError

    def _set_in(self, obj, value):
        raise NotImplementedError

    def _del_in(self, obj):
        raise NotImplementedError

    def __add__(self, other):
        return self.__class__(tuple.__add__(self, other))

    def __str__(self):
        return self.sep.join(str(v) for v in self)


class Path(BasePath):
    """
    Fast implementation of the baseclass that does not allow wildcards and slicing.
    """

    def call_in(self, obj, *args, **kwargs):
        return self.get_in(obj)(*args, **kwargs)

    def _get_in(self, obj, default=_marker):
        """returns item at wildpath 'self' from the 'obj'"""
        try:
            for key in self:
                if isinstance(obj, Mapping):
                    obj = obj[key]
                elif isinstance(obj, Sequence):
                    obj = obj[int(key)]
                else:
                    obj = getattr(obj, key)
        except (KeyError, IndexError, AttributeError):
            if default is _marker:
                raise
            return default
        else:
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

    def __new__(cls, string_or_seq=None, _parse=algebra.parse, _tokens=tokens):
        self = super(WildPath, cls).__new__(cls, string_or_seq)
        preprocessed = cls._preprocessed
        for wild_key in self:
            #  if wild_cards or slicing is used, multiple results are returned and the boolean logic is applied
            if wild_key not in preprocessed and any(t in wild_key for t in _tokens):
                preprocessed[wild_key] = _parse(wild_key, simplify=True)
        self.depth = self._get_depth()
        return self

    def _get_depth(self):
        prep = self._preprocessed
        return len([k for k in self if k in prep])-1

    def call_in(self, obj, *args, **kwargs):
        results = self.get_in(obj)
        for path, instance_method in Path.items(results, _call=True):
            path.set_in(results, instance_method(*args, **kwargs))
        return results

    def get_in(self, obj, default=_marker, flat=False):
        result = super(WildPath, self).get_in(obj, default)
        if flat:
            return flatten(result, depth=self.depth)
        return result

    def _get_in(self, obj, default=_marker, _preprocessed=_preprocessed):
        """returns item(s) at wildpath 'self' from the 'obj'"""
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
                    obj_dict = self.get_object_dict(obj)
                    return {k: obj_dict[k] for k in _preprocessed[key](*obj_dict)}
            else:
                if isinstance(obj, Mapping):
                    return obj.__class__((k, self[1:]._get_in(obj[k], default)) for k in _preprocessed[key](*obj))
                elif isinstance(obj, Sequence):
                    return obj.__class__(self[1:].get_in(obj[i], default) for i in _preprocessed[key](*range(len(obj))))
                else:
                    obj_dict = self.get_object_dict(obj)
                    return {k: self[1:]._get_in(obj_dict[k], default) for k in _preprocessed[key](*obj_dict)}
        else:
            if len(self) == 1:
                try:
                    if isinstance(obj, Mapping):
                        return obj[key]
                    elif isinstance(obj, Sequence):
                        return obj[int(key)]
                    else:
                        return getattr(obj, key)
                except (KeyError, IndexError, AttributeError):
                    if default is _marker:
                        raise
                    return default
            else:
                if isinstance(obj, Mapping):
                    return self[1:]._get_in(obj[key], default)
                elif isinstance(obj, Sequence):
                    return self[1:]._get_in(obj[int(key)], default)
                else:
                    return self[1:]._get_in(getattr(obj, key), default)

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
                    for k in _preprocessed[key](*self.get_object_dict(obj)):
                        setattr(obj, k, get_with_key(value, k))
            else:
                if isinstance(obj, MutableMapping):
                    for k in _preprocessed[key](*obj):
                        self[1:]._set_in(obj[k], get_with_key(value, k))
                elif isinstance(obj, MutableSequence):
                    for i, j in enumerate(_preprocessed[key](*range(len(obj)))):
                        self[1:]._set_in(obj[j], get_with_index(value, i))
                else:
                    obj_dict = self.get_object_dict(obj)
                    for k in _preprocessed[key](*obj_dict):
                        self[1:]._set_in(obj_dict[k], get_with_key(value, k))
        else:
            if len(self) == 1:
                if isinstance(obj, MutableMapping):
                    obj[key] = value
                elif isinstance(obj, MutableSequence):
                    obj[int(key)] = value
                else:
                    setattr(obj, key, value)
            else:
                if isinstance(obj, MutableMapping):
                    self[1:]._set_in(obj[key], _get_with_key(value, key))
                elif isinstance(obj, MutableSequence):
                    self[1:]._set_in(obj[int(key)], _get_with_index(value, int(key)))
                else:
                    self[1:]._set_in(getattr(obj, key), _get_with_key(value, key))


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
                    for k in _preprocessed[key](*self.get_object_dict(obj)):
                        delattr(obj, k)
            else:
                if isinstance(obj, MutableMapping):
                    for k in _preprocessed[key](*obj):
                        self[1:]._del_in(obj[k])
                elif isinstance(obj, MutableSequence):
                    for i in _preprocessed[key](*range(len(obj))):
                        self[1:]._del_in(obj[i])
                else:
                    obj_dict = self.get_object_dict(obj)
                    for k in _preprocessed[key](*obj_dict):
                        self[1:]._del_in(obj_dict[k])
        else:
            if len(self) == 1:
                if isinstance(obj, MutableMapping):
                    del obj[key]
                elif isinstance(obj, MutableSequence):
                    del obj[int(key)]
                else:
                    delattr(obj, key)
            else:
                if isinstance(obj, MutableMapping):
                    self[1:]._del_in(obj[key])
                elif isinstance(obj, MutableSequence):
                    self[1:]._del_in(obj[int(key)])
                else:
                    self[1:]._del_in(getattr(obj, key))




if __name__ == "__main__":
    pass