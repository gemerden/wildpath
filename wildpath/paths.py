from collections import Mapping, Sequence, MutableMapping, MutableSequence
from fnmatch import fnmatchcase
from itertools import imap


class BasePath(list):
    """
        helper classes to be able to use '.' separated paths to access elements in (e.g. json) dictionaries.
        For examples see the tests.
    """
    sep = "."


    def __init__(self, string_or_seq=()):
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

    def get_in(self, obj):
        raise NotImplementedError

    def set_in(self, obj, value):
        raise NotImplementedError

    def del_in(self, obj):
        raise NotImplementedError

    def pop_in(self, obj):
        result = self.get_in(obj)
        self.del_in(obj)
        return result

    def has_in(self, obj):
        """checks presence of item at path 'self' from the 'obj'"""
        try:
            self.get_in(obj)
        except (KeyError, IndexError, AttributeError):
            return False
        return True

    def __add__(self, other):
        return self.__class__(list.__add__(self, other))

    def __str__(self):
        return self.sep.join(str(v) for v in self)


class Path(BasePath):

    def get_in(self, obj):
        """returns item at path 'self' from the 'obj'"""
        for key in self:
            if isinstance(obj, Mapping):
                obj = obj[key]
            elif isinstance(obj, Sequence):
                obj = obj[int(key)]
            else:
                obj = getattr(obj, key)
        return obj

    def set_in(self, obj, value):
        """sets item at path 'self' from the 'obj' to 'value'"""
        obj = self[:-1].get_in(obj)
        if isinstance(obj, MutableMapping):
            obj[self[-1]] = value
        elif isinstance(obj, MutableSequence):
            obj[int(self[-1])] = value
        else:
            setattr(obj, self[-1], value)

    def del_in(self, obj):
        """deletes item at path 'self' from the 'obj'"""
        obj = self[:-1].get_in(obj)
        if isinstance(obj, MutableMapping):
            del obj[self[-1]]
        elif isinstance(obj, MutableSequence):
            del obj[int(self[-1])]
        else:
            delattr(obj, self[-1])


def parse_slice(key, parse_item=lambda v: int(v) if v else None):
    return slice(*map(parse_item, key.split(':')))


def match_key(k, wild_key, sep='|'):
    return any(fnmatchcase(k, key) for key in wild_key.split(sep))


class WildPath(BasePath):
    """
    Adds wildcards, multiple keys and slicing to Path. e.g WildPath("items.*.start|end.time*.:2).get_in(some_obj):
    - WildPath(
    """
    sep = "."

    def get_in(self, obj, parse_slice=parse_slice):
        """returns item at path 'self' from the 'obj'"""
        if not len(self):
            return obj
        key = self[0]
        if '*' in key or '?' in key or ':' in key or "|" in key:
            tail = self[1:]
            if isinstance(obj, Mapping):
                return obj.__class__((k, tail.get_in(v)) for k, v in obj.iteritems() if match_key(k, key))
            elif isinstance(obj, Sequence):
                if key == "*":
                    return obj.__class__(map(tail.get_in, obj))
                try:
                    return obj.__class__(map(tail.get_in, obj[parse_slice(key)]))
                except (ValueError, TypeError) as e:
                    raise IndexError("sequence index wildcard can only be '*' or slice (e.g. 1:3)")
            else:
                return {k: tail.get_in(v) for k, v in obj.__dict__.iteritems() if match_key(k, key)}
        else:
            if isinstance(obj, Mapping):
                return self[1:].get_in(obj[key])
            elif isinstance(obj, Sequence):
                return self[1:].get_in(obj[int(key)])
            else:
                return self[1:].get_in(getattr(obj, key))

    def set_in(self, obj, value):
        """sets item(s) at path 'self' from the 'obj' to 'value'"""
        key = self[0]
        if '*' in key or '?' in key or ':' in key or "|" in key:
            if len(self) == 1:
                if isinstance(obj, MutableMapping):
                    [obj.__setitem__(k, value[k]) for k in obj if match_key(k, key)]
                elif isinstance(obj, MutableSequence):
                    if key == '*':
                        obj[:] = value
                    else:
                        try:
                            obj[parse_slice(key)] = value
                        except (ValueError, TypeError) as e:
                            raise IndexError("sequence index wildcard can only be '*' or slice (e.g. 1:3)")
                else:
                    [setattr(obj, k, value[k]) for k in obj.__dict__ if match_key(k, key)]
            else:
                tail = self[1:]
                if isinstance(obj, MutableMapping):
                    map(tail.set_in, *zip(*((v, value[k]) for k, v in obj.iteritems() if match_key(k, key))))
                elif isinstance(obj, MutableSequence):
                    if key == '*':
                        map(tail.set_in, obj, value)
                    else:
                        try:
                            map(tail.set_in, obj[parse_slice(key)], value)
                        except (ValueError, TypeError) as e:
                            raise IndexError("sequence index wildcard can only be '*' or slice (e.g. 1:3)")
                else:
                    map(tail.set_in, *zip(*((v, value[k]) for k, v in obj.__dict__.iteritems() if match_key(k, key))))
        else:
            if len(self) == 1:
                if isinstance(obj, MutableMapping):
                    obj[key] = value
                elif isinstance(obj, MutableSequence):
                    obj[int(key)] = value
                else:
                    setattr(obj, key, value)
            else:
                if isinstance(obj, Mapping):
                    self[1:].set_in(obj[key], value)
                elif isinstance(obj, Sequence):
                    self[1:].set_in(obj[int(key)], value)
                else:
                    self[1:].set_in(getattr(obj, key), value)

    def del_in(self, obj):
        """deletes item(s) at path 'self' from the 'obj'"""
        key = self[0]
        if '*' in key or '?' in key or ':' in key or "|" in key:
            if len(self) == 1:
                if isinstance(obj, MutableMapping):
                    [obj.__delitem__(k) for k in obj.keys() if match_key(k, key)]
                elif isinstance(obj, MutableSequence):
                    if key == '*':
                        del obj[:]
                    else:
                        try:
                            del obj[parse_slice(key)]
                        except (ValueError, TypeError) as e:
                            raise IndexError("sequence index wildcard can only be '*' or slice (e.g. 1:3)")
                else:
                    [delattr(obj, k) for k in obj.__dict__.keys() if match_key(k, key)]
            else:
                tail = self[1:]
                if isinstance(obj, MutableMapping):
                    map(tail.del_in, (v for k, v in obj.iteritems() if match_key(k, key)))
                elif isinstance(obj, MutableSequence):
                    if key == '*':
                        map(tail.del_in, obj)
                    else:
                        try:
                            map(tail.del_in, obj[parse_slice(key)])
                        except (ValueError, TypeError) as e:
                            raise IndexError("sequence index wildcard can only be '*' or slice (e.g. 1:3)")
                else:
                    map(tail.del_in, (v for k, v in obj.__dict__.iteritems() if match_key(k, key)))
        else:
            if len(self) == 1:
                if isinstance(obj, MutableMapping):
                    del obj[key]
                elif isinstance(obj, MutableSequence):
                    del obj[int(key)]
                else:
                    delattr(obj, key)
            else:
                if isinstance(obj, Mapping):
                    self[1:].del_in(obj[key])
                elif isinstance(obj, Sequence):
                    self[1:].del_in(obj[int(key)])
                else:
                    self[1:].del_in(getattr(obj, key))



if __name__ == "__main__":
    pass