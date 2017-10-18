import unittest

from copy import deepcopy

from tests.samples import agenda
from tests.samples import google_route
from wildpath.keyparser import KeyParser
from wildpath.paths import Path, WildPath


class Object(object):

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def add(self, x, y, z=0):
        return self.s + x + y + z

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other


class TestBase(unittest.TestCase):

    def setUp(self):
        self.simple = Object(
            a=1,
            b=[2, 3],
            c=dict(d=4, e=5),
            d=Object(e=6),
            e=[dict(a=7, b=8),
               dict(b=9, c=0),
               Object()],
            f=[[dict(a=[7,7], b=[8,8]),
                dict(b=[9,9], c=[0,0,0])],
               [dict(a=[1,1], b=[2,2]),
                dict(b=[3,3], c=[4,4,4])]],
        )
        self.complex = Object(
            aa=1,
            ba=[2, 3],
            bb=[4, 5],
            ca=dict(d=6, e=7, f=8),
            cb=Object(e=9),
            ff=[1,2,3,4,5,6],
            gg=[dict(a=1, b=2), dict(b=3, c=4), dict(a=5, b=6, c=7)],
        )

        self.agenda = agenda
        self.google_route = google_route


class TestPath(TestBase):

    def test_slice(self):
        path = Path("1.a.2.b.3.c")
        self.assertEqual(type(path[-1:0:-2]), Path)
        self.assertEqual(path[::2], Path("1.2.3"))
        self.assertEqual(path[1:-1], Path("a.2.b.3"))
        self.assertEqual(path[-1:0:-2], Path("c.b.a"))

    def test_some_basics(self):
        path = Path('')

    def test_basic_get(self):
        p1 = Path("a")
        p2 = Path("1")
        self.assertEqual(p1.get_in(dict(a=1)), 1)
        self.assertEqual(p2.get_in([0, 1]), 1)
        self.assertEqual(p1.get_in(Object(a=1)), 1)

    def test_basic_set(self):
        p1 = Path("a")
        p2 = Path("1")
        d = dict(a=1)
        l = [0, 1]
        o = Object(a=1)
        p1._set_in(d, 0)
        p2._set_in(l, 0)
        p1._set_in(o, 0)
        self.assertEqual(p1.get_in(d), 0)
        self.assertEqual(p2.get_in(l), 0)
        self.assertEqual(p1.get_in(o), 0)

    def test_basic_del(self):
        p1 = Path("a")
        p2 = Path("1")
        d = dict(a=1)
        l = [0, 1]
        o = Object(a=1)
        p1._del_in(d)
        p2._del_in(l)
        p1._del_in(o)
        self.assertEqual(d, {})
        self.assertEqual(l, [0])
        self.assertEqual(len(o.__dict__), 0)

    def test_longer_get(self):
        s = deepcopy(self.simple)
        p = Path("b.0")
        self.assertEqual(p.get_in(s), 2)
        p = Path("c.d")
        self.assertEqual(p.get_in(s), 4)
        p = Path("d.e")
        self.assertEqual(p.get_in(s), 6)
        p = Path("e.1.b")
        self.assertEqual(p.get_in(s), 9)

    def test_longer_set(self):
        s = deepcopy(self.simple)
        p = Path("b.0")
        p._set_in(s, 11)
        self.assertEqual(p.get_in(s), 11)
        p = Path("c.d")
        p._set_in(s, 11)
        self.assertEqual(p.get_in(s), 11)
        p = Path("d.e")
        p._set_in(s, 11)
        self.assertEqual(p.get_in(s), 11)

    def test_longer_del(self):
        s = deepcopy(self.simple)
        p = Path("b.0")
        p._del_in(s)
        self.assertEqual(s.b, [3])
        p = Path("c.d")
        p._del_in(s)
        self.assertEqual(s.c, {"e": 5})
        p = Path("d.e")
        p._del_in(s)
        self.assertEqual(len(s.d.__dict__), 0)

    def test_exceptions(self):
        s = deepcopy(self.simple)
        with self.assertRaises(KeyError):
            Path("e.1.a").get_in(s)
        with self.assertRaises(IndexError):
            Path("e.5.a").get_in(s)
        with self.assertRaises(AttributeError):
            Path("e.2.x").get_in(s)

class TestWildPath(TestBase):

    def test_pop(self):
        for path_string in ["b*", "ca|cb", "ca.d", "gg.*.b", "ff.*", "ff.:", "*", "ff.::2", "ff.-1:0:-2"]:
            obj = deepcopy(self.complex)
            path = WildPath(path_string)
            get = path.get_in(obj)
            self.assertEqual(path.pop_in(obj), get)

    def test_slice(self):
        path = WildPath("1.a.2.b.3.c")
        self.assertEqual(type(path[-1:0:-2]), WildPath)
        self.assertEqual(path[::2], WildPath("1.2.3"))
        self.assertEqual(path[1:-1], WildPath("a.2.b.3"))
        self.assertEqual(path[-1:0:-2], WildPath("c.b.a"))

    def test_basic_get(self):
        p1 = WildPath("a")
        p2 = WildPath("1")
        self.assertEqual(p1.get_in(dict(a=1)), 1)
        self.assertEqual(p2.get_in([0, 1]), 1)
        self.assertEqual(p1.get_in(Object(a=1)), 1)

    def test_basic_set(self):
        p1 = WildPath("a")
        p2 = WildPath("1")
        d = dict(a=1)
        l = [0, 1]
        o = Object(a=1)
        p1._set_in(d, 0)
        p2._set_in(l, 0)
        p1._set_in(o, 0)
        self.assertEqual(p1.get_in(d), 0)
        self.assertEqual(p2.get_in(l), 0)
        self.assertEqual(p1.get_in(o), 0)

    def test_basic_del(self):
        p1 = WildPath("a")
        p2 = WildPath("1")
        d = dict(a=1)
        l = [0, 1]
        o = Object(a=1)
        p1._del_in(d)
        p2._del_in(l)
        p1._del_in(o)
        self.assertEqual(d, {})
        self.assertEqual(l, [0])
        self.assertEqual(len(o.__dict__), 0)

    def test_longer_get(self):
        s = deepcopy(self.simple)
        p = WildPath("b.0")
        self.assertEqual(p.get_in(s), 2)
        p = WildPath("c.d")
        self.assertEqual(p.get_in(s), 4)
        p = WildPath("d.e")
        self.assertEqual(p.get_in(s), 6)

    def test_longer_set(self):
        s = deepcopy(self.simple)
        p = WildPath("b.0")
        p._set_in(s, 11)
        self.assertEqual(p.get_in(s), 11)
        p = WildPath("c.d")
        p._set_in(s, 11)
        self.assertEqual(p.get_in(s), 11)
        p = WildPath("d.e")
        p._set_in(s, 11)
        self.assertEqual(p.get_in(s), 11)
        s = deepcopy(self.simple)
        p = WildPath("e.:2.b")
        p._set_in(s, [11, 12])
        self.assertEqual(p.get_in(s), [11,12])

    def test_constant_set(self):
        s = deepcopy(self.simple)
        p = WildPath("e.*.b")
        p._set_in(s, 13)
        self.assertEqual(p.get_in(s), [13,13, 13])

        s = deepcopy(self.simple)
        p = WildPath("e.:2.*")
        p._set_in(s, 13)
        self.assertEqual(p.get_in(s), [{'a': 13, 'b': 13}, {'c': 13, 'b': 13}])

        s = deepcopy(self.simple)
        p = WildPath("e.:2")
        p._set_in(s, 13)
        self.assertEqual(p.get_in(s), [13, 13])

    def test_longer_del(self):
        s = deepcopy(self.simple)
        p = WildPath("b.0")
        p._del_in(s)
        self.assertEqual(s.b, [3])
        p = WildPath("c.d")
        p._del_in(s)
        self.assertEqual(s.c, {"e": 5})
        p = WildPath("d.e")
        p._del_in(s)
        self.assertEqual(len(s.d.__dict__), 0)

    def test_wild_slice(self):
        s = deepcopy(self.complex)
        self.assertEqual(WildPath("ff.::2").get_in(s), [1,3,5])
        self.assertEqual(WildPath("ff.1:3").get_in(s), [2,3])
        self.assertEqual(WildPath("ff.:").get_in(s), [1,2,3,4,5,6])
        self.assertEqual(WildPath("ff.-1:0:-2").get_in(s), [2,4,6])
        self.assertEqual(WildPath("gg.:2.b").get_in(s), [2,3])
        with self.assertRaises(KeyError):
            self.assertEqual(WildPath("gg.:2.a").get_in(s), [6,4,2])

        WildPath("ff.1:3")._set_in(s, [7, 7])
        self.assertEqual(s.ff, [1,7, 7,4,5,6])
        s = deepcopy(self.complex)
        WildPath("ff.0:3")._del_in(s)
        self.assertEqual(s.ff, [4,5,6])

    def test_wildkey_or(self):
        s = deepcopy(self.complex)
        self.assertEqual(WildPath("aa|ba").get_in(s), {"aa": 1, "ba": [2, 3]})
        self.assertEqual(WildPath("ca.d|e").get_in(s), {"d": 6, "e": 7})

        agenda = deepcopy(self.agenda)

        result = WildPath("items.*.name|subjects").get_in(agenda)
        self.assertTrue(len(r) == 2 for r in result)

    def test_wildslice_or(self):
        L = [0,1,2,3,4,5,6,7,8,9]
        path_1 = WildPath(":2|3:")
        path_2 = WildPath("::2|::3")
        path_3 = WildPath("::-2|::-3")
        path_4 = WildPath(":3|2:")  #all
        path_5 = WildPath("!(:2|3:)")

        #  get_in
        self.assertEqual(path_1.get_in(L), [0,1,3,4,5,6,7,8,9])  # not 2
        self.assertEqual(path_2.get_in(L), [0, 2, 3, 4, 6, 8, 9])
        self.assertEqual(path_3.get_in(L), [0, 1, 3, 5, 6, 7, 9])
        self.assertEqual(path_4.get_in(L), L)
        self.assertEqual(path_5.get_in(L), [2])

    def test_wild_get(self):
        s = deepcopy(self.complex)
        self.assertEqual(WildPath("bb.*").get_in(s), [4, 5])
        self.assertEqual(WildPath("b*.1").get_in(s), {'ba': 3, 'bb': 5})
        self.assertEqual(WildPath("c*.e").get_in(s), {'ca': 7, 'cb': 9})
        self.assertEqual(WildPath("c*.e*").get_in(s), {'ca': {'e': 7}, 'cb': {'e': 9}})
        self.assertEqual(set(WildPath("c*.e*").get_in(s, flat=True)), {7, 9})

    def test_wild_set(self):
        p1 = WildPath("bb.*")
        p2 = WildPath("b*.1")
        p3 = WildPath("c*.e")
        p4 = WildPath("c*.e*")
        s = deepcopy(self.complex)
        p1._set_in(s, [14, 15])
        self.assertEqual(p1.get_in(s), [14, 15])
        s = deepcopy(self.complex)
        p2._set_in(s, {'ba': 13, 'bb': 15})
        self.assertEqual(p2.get_in(s), {'ba': 13, 'bb': 15})
        s = deepcopy(self.complex)
        p3._set_in(s, {'ca': 17, 'cb': 18})
        self.assertEqual(p3.get_in(s), {'ca': 17, 'cb': 18})
        s = deepcopy(self.complex)
        p4._set_in(s, {'ca': {'e': 17}, 'cb': {'e': 18}})
        self.assertEqual(p4.get_in(s), {'ca': {'e': 17}, 'cb': {'e': 18}})

    def test_wild_del(self):
        p1 = WildPath("bb.*")
        p2 = WildPath("b*.1")
        p3 = WildPath("c*.e")
        p4 = WildPath("c*.e*")
        p5 = WildPath("*")
        s = deepcopy(self.complex)
        p1._del_in(s)
        self.assertEqual(p1.get_in(s), [])
        s = deepcopy(self.complex)
        p2._del_in(s)
        self.assertEqual(s.ba, [2])
        self.assertEqual(s.bb, [4])
        s = deepcopy(self.complex)
        p3._del_in(s)
        self.assertEqual(s.ca, {"d": 6, "f": 8})
        self.assertEqual(s.cb.__dict__, {})
        s = deepcopy(self.complex)
        p4._del_in(s)
        self.assertEqual(s.ca, {"d": 6, "f": 8})
        self.assertEqual(s.cb.__dict__, {})
        s = deepcopy(self.complex)
        p5._del_in(s)
        self.assertEqual(s.__dict__, {})

    def test_wild_not_slice(self):
        L = [0,1,2,3,4,5]
        path_1 = WildPath("!:")
        path_2 = WildPath("!::2")
        path_3 = WildPath("!1:3")
        path_4 = WildPath("!-1:0:-2")
        #  get_in
        self.assertEqual(path_1.get_in(L), [])
        self.assertEqual(path_2.get_in(L), [1,3,5])
        self.assertEqual(path_3.get_in(L), [0,3,4,5])
        self.assertEqual(path_4.get_in(L), [0, 2, 4])
        #  set_in
        L = [0, 1, 2, 3, 4, 5]
        path_1.set_in(L, [1,2,3])
        self.assertEqual(L, [0, 1, 2, 3, 4, 5])

        L = [0, 1, 2, 3, 4, 5]
        path_2.set_in(L, [1,2,3])
        self.assertEqual(L, [0, 1, 2, 2, 4, 3])

        L = [0, 1, 2, 3, 4, 5]
        path_3.set_in(L, [1,2,3,4])
        self.assertEqual(L, [1, 1, 2, 2, 3, 4])

        L = [0, 1, 2, 3, 4, 5]
        path_4.set_in(L, [1,2,3])
        self.assertEqual(L, [1, 1, 2, 3, 3, 5])
        #  del_in
        L = [0, 1, 2, 3, 4, 5]
        path_1.del_in(L)
        self.assertEqual(L, [0, 1, 2, 3, 4, 5])

        L = [0, 1, 2, 3, 4, 5]
        path_2.del_in(L)
        self.assertEqual(L, [0, 2, 4])

        L = [0, 1, 2, 3, 4, 5]
        path_3.del_in(L)
        self.assertEqual(L, [1, 2])

        L = [0, 1, 2, 3, 4, 5]
        path_4.del_in(L)
        self.assertEqual(L, [1,3,5])

    def test_exceptions(self):
        s = deepcopy(self.simple)
        with self.assertRaises(KeyError):
            WildPath("e.1.a").get_in(s)
        with self.assertRaises(IndexError):
            WildPath("e.5.a").get_in(s)
        with self.assertRaises(AttributeError):
            WildPath("e.2.x").get_in(s)

    def test_string_like_values(self):
        items = list(WildPath.items(self.agenda))
        self.assertTrue(all(len(item[0]) <= 4 for item in items))  # strings are not entered/iterated over characters
        path = WildPath("meeting")
        try:
            path._set_in(agenda, "some other name")  # value is not seen as a Sequence
        except Exception as e:
            self.fail(e)

    def test_flat(self):
        obj=deepcopy(self.simple)
        path = WildPath("f.*.*.*.1")
        self.assertEqual(set(path.get_in(obj, flat=True)), {7, 8, 0, 9, 1, 2, 4, 3})   #order is not preserved for dicts
        path = WildPath("f.*.*.*")
        self.assertTrue(all(isinstance(p, list) for p in path.get_in(obj, flat=True)))

    def test_call_in(self):
        special = Object(s=0)
        special.sub = lambda x, y: x-y
        obj = [
            dict(a=Object(s=1), b=Object(s=2), c=special),
            dict(aa=Object(s=3), bb=Object(s=4), c=special),
        ]
        path = WildPath("*.a*.add")
        self.assertEqual(path.call_in(obj, 1, y=2), [{'a': 4}, {'aa': 6}])
        path = WildPath("*.c.sub")
        self.assertEqual(path.call_in(obj, 2, y=1), [1, 1])



class TestIterators(TestBase):

    def test_iteritems_all(self):
        paths = [path for path in Path.items(self.simple, all=True)]
        self.assertEqual(len(paths), 50)

        new = {}
        for path, value in Path.items(self.simple, all=True):
            path._set_in(new, value)

        for path in Path.paths(new):
            self.assertEqual(path.get_in(self.simple), path.get_in(new))

    def test_iteritems(self):
        items = [path for path in Path.items(self.simple, all=False)]
        self.assertTrue(all(isinstance(item, tuple) for item in items))
        self.assertEqual(len(items), 28)

    def test_iteritems_copy(self):
        simple = deepcopy(self.simple)
        new = {}
        for path, value in Path.items(simple, all=True):
            if isinstance(value, int):
                value = str(value)
            path._set_in(new, value)

        self.assertEqual(simple, self.simple)


class TestKeyParser(unittest.TestCase):
    
    def setUp(self):
        self.keyparser = KeyParser()

    def test_empty(self):
        exp = self.keyparser.parse("*")
        self.assertEqual(exp("a", "b", "c"), {"a", "b", "c"})
        exp = self.keyparser.parse("!*")
        self.assertEqual(exp(*range(5)), set())

    def test_or(self):
        exp = self.keyparser.parse("a|b|c")
        self.assertEqual(exp("a", "b", "d"), {"a", "b"})
        exp = self.keyparser.parse("1|2|3")
        self.assertEqual(exp(*range(5)), {1,2,3})

    def test_and(self):
        exp = self.keyparser.parse("a&b&c")
        self.assertEqual(exp("a", "b", "d"), set())  # no item has and key a and key b and key c
        exp = self.keyparser.parse("1&2&3")
        self.assertEqual(exp(*range(5)), set())

    def test_not(self):
        exp = self.keyparser.parse("!a")
        self.assertEqual(exp("a", "b", "c"), {"b", "c"})  # no item has and key a and key b and key c
        exp = self.keyparser.parse("!1")
        self.assertEqual(exp(*range(5)), {0,2,3,4})

    def test_composite(self):
        exp = self.keyparser.parse("!a&b|c")
        self.assertEqual(exp("a", "b", "c"), {"b", "c"})  # no item has and key a and key b and key c
        exp = self.keyparser.parse("!1&2|3")
        self.assertEqual(exp(*range(5)), {2,3})

    def test_composite_with_slices(self):
        indices = tuple(range(10))
        exp = self.keyparser.parse(":")
        self.assertEqual(exp(*indices), set(indices))
        exp = self.keyparser.parse("*")
        self.assertEqual(exp(*indices), set(indices))
        exp = self.keyparser.parse("1:7|2:8|3:9")
        self.assertEqual(exp(*indices), {1,2,3,4,5,6,7,8})
        exp = self.keyparser.parse("1:7&2:8&3:9")
        self.assertEqual(exp(*indices), {3,4,5,6})
        exp = self.keyparser.parse("(::2&1:6|2::4)&!4")
        self.assertEqual(exp(*indices), {2, 6})

    def test_composite_with_wildcards(self):
        keys = ("a", "b", "c", "aa", "ab", "ac", "bb", "bc", "cc")  # len(keys) == 10
        exp = self.keyparser.parse("*")
        self.assertEqual(exp(*keys), set(keys))
        exp = self.keyparser.parse("a*")
        self.assertEqual(exp(*keys), {"a", "aa", "ab", "ac"})
        exp = self.keyparser.parse("a?")
        self.assertEqual(exp(*keys), {"aa", "ab", "ac"})
        exp = self.keyparser.parse("!a*")  # not starting with "a"
        self.assertEqual(exp(*keys), {"b", "c", "bb", "bc", "cc"})
        exp = self.keyparser.parse("b*|c*")  # not starting with "a"
        self.assertEqual(exp(*keys), {"b", "c", "bb", "bc", "cc"})
        exp = self.keyparser.parse("b*&*c")  # not starting with "a"
        self.assertEqual(exp(*keys), {"bc"})

    def test_simple_keys(self):
        keys = ("a", "b", "c")
        wildkey_expected = {"*": {"a", "b", "c"},
                            "(*)": {"a", "b", "c"},
                            "!(*)":set(),
                            "(!*)": set(),
                            "a": {"a"},
                            "!a": {"b", "c"},
                            "a*": {"a"},
                            "!a*": {"b", "c"},
                            "!(a*)": {"b", "c"},
                            "a|b": {"a", "b"},
                            "a&b": set(),
                            "a|!b": {"a", "c"},
                            "a&!b": {"a"},
                            "!(a|b)": {"c"},
                            "!(a&b)": {"a", "b", "c"}}
        for wildkey, expected in wildkey_expected.items():
            expression = self.keyparser.parse(wildkey)
            self.assertEqual(expression(*keys), expected)

    def test_simple_indexes(self):
        keys = tuple(range(3))
        wildkey_expected = {"*": {0,1,2},
                            ":": {0,1,2},
                            "(:)": {0,1,2},
                            "!(:)":set(),
                            "(!:)": set(),
                            "1": {1},
                            "!1": {0, 2},
                            "1:": {1,2},
                            "!1:": {0},
                            "!(1:)": {0},
                            "1|2": {1, 2},
                            "1&2": set(),
                            "1|!2": {0, 1},
                            "1&!2": {1},
                            "!(1|2)": {0},
                            "!(1&2)": {0,1,2}}
        for wildkey, expected in wildkey_expected.items():
            expression = self.keyparser.parse(wildkey)
            self.assertEqual(expression(*keys), expected)

    def test_alt_keys(self):
        keys = {"a", "b", "a b"}
        wildkey_expected = {"*": {"a", "b", "a b"},
                            "(*)": {"a", "b", "a b"},
                            "!(*)":set(),
                            "(!*)": set(),
                            "a": {"a"},
                            "!a": {"b", "a b"},
                            "a*": {"a", "a b"},
                            "!a*": {"b"},
                            "!(a*)": {"b"},
                            "a|b": {"a", "b"},
                            "a&b": set(),
                            "a|!b": {"a", "a b"},
                            "a&!b": {"a"},
                            "!(a|b)": {"a b"},
                            "!(a&b)": {"a", "b", "a b"}}
        for wildkey, expected in wildkey_expected.items():
            expression = self.keyparser.parse(wildkey)
            self.assertEqual(expression(*keys), expected)


class TestLogicPath(TestBase):

    def test_key_or(self):
        obj = dict(a=1, b=2, c=3, aa=4)
        path = WildPath("a|b|c")
        self.assertEqual(path.get_in(obj), dict(a=1, b=2, c=3))

    def test_key_and(self):
        obj = dict(a=1, b=2, c=3, aa=4)
        path = WildPath("a&b&c")  # no key is a and b and c
        self.assertEqual(path.get_in(obj), dict())

    def test_key_not(self):
        obj = dict(a=1, b=2, c=3)
        path = WildPath("!a")
        self.assertEqual(path.get_in(obj), dict(b=2, c=3))

    def test_key_composite(self):
        obj = dict(a=1, b=2, c=3, aa=4, ab=5, ac=6, bb=7, bc=8, cc=9)
        path = WildPath("b*|c*")  # starting with b or c
        self.assertEqual(path.get_in(obj), dict(b=2, c=3, bb=7, bc=8, cc=9))
        path = WildPath("b*&*c")  # starting with b AND ending with c
        self.assertEqual(path.get_in(obj), dict(bc=8))

    def test_index_or(self):
        obj = list(range(8))
        path = WildPath("1|2|3")
        self.assertEqual(path.get_in(obj), [1,2,3])

    def test_index_and(self):
        obj = list(range(8))
        path = WildPath("1&2&3")
        self.assertEqual(path.get_in(obj), [])

    def test_index_not(self):
        obj = list(range(8))
        path = WildPath("!1")
        self.assertEqual(path.get_in(obj), [0,2,3,4,5,6,7])

    def test_index_composite(self):
        obj = list(range(8))
        path = WildPath("1:3|5:7")  # starting with b or c
        self.assertEqual(path.get_in(obj), [1,2,5,6])
        path = WildPath("::2&::3")  # starting with b AND ending with c
        self.assertEqual(path.get_in(obj), [0, 6])
        path = WildPath("!(::2|::3)")
        self.assertEqual(path.get_in(obj), [1,5,7])

    def test_composite_path(self):
        obj = deepcopy(self.agenda)
        path = WildPath("items.0|2.?u*&!*ion.!1:")  # last key: second char == 'u' and ends with 'ion'
        self.assertEqual(path._get_in(obj), [{'subjects': ['purpose of the meeting']}, {'subjects': ['questions']}])

    def test_simple_keys(self):
        obj = {"a": 1, "b": 2, "c": 3}
        wildkey_expected = {"*": {"a", "b", "c"},
                            "(*)": {"a", "b", "c"},
                            "!(*)":set(),
                            "(!*)": set(),
                            "!a": {"b", "c"},
                            "a*": {"a"},
                            "!a*": {"b", "c"},
                            "!(a*)": {"b", "c"},
                            "a|b": {"a", "b"},
                            "a&b": set(),
                            "a|!b": {"a", "c"},
                            "a&!b": {"a"},
                            "!(a|b)": {"c"},
                            "!(a&b)": {"a", "b", "c"}}
        for wildkey, expected in wildkey_expected.items():
            path = WildPath(wildkey)
            self.assertEqual(set(path.get_in(obj).keys()), expected)


    def test_simple_indices(self):
        obj = tuple(range(3))
        wildkey_expected = {"*": {0,1,2},
                            ":": {0,1,2},
                            "(:)": {0,1,2},
                            "!(:)":set(),
                            "(!:)": set(),
                            "!1": {0, 2},
                            "1:": {1,2},
                            "!1:": {0},
                            "!(1:)": {0},
                            "1|2": {1, 2},
                            "1&2": set(),
                            "1|!2": {0, 1},
                            "1&!2": {1},
                            "!(1|2)": {0},
                            "!(1&2)": {0,1,2}}
        for wildkey, expected in wildkey_expected.items():
            path = WildPath(wildkey)
            self.assertEqual(set(path.get_in(obj)), expected)


class TestVarious(unittest.TestCase):

    def test_orring_negative_indices(self):
        obj = dict(key=[[0,1],[2,3],[4,5],[6,7]])
        path = WildPath("key.0|-1.0")
        self.assertEqual(path.get_in(obj), [0, 6])


    def test_default(self):
        obj = [
            dict(a=[0, 1, 2], b="b1"),
            dict(a=[3, 4, 5], b="b2", c="c"),
        ]
        self.assertEqual(Path("0.c").get_in(obj, "default"), "default")
        self.assertEqual(WildPath("*.c").get_in(obj, "default"), ["default", "c"])

    def test_property(self):
        class Some(object):
            def __init__(self):
                self._prop = "prop"

            @property
            def prop(self):
                return self._prop

            @prop.setter
            def prop(self, string):
                self._prop = string

            @prop.deleter
            def prop(self):
                del self._prop

        some = Some()

        self.assertEqual(Path("prop").get_in(some), "prop")
        self.assertEqual(WildPath("prop").get_in(some), "prop")
        self.assertEqual(WildPath("!_*").get_in(some), {'prop': 'prop'})
        self.assertEqual(dict(Path.items(some)), {('prop',): 'prop', ('_prop',): 'prop'})
        Path("prop").set_in(some, "drop")
        self.assertEqual(Path("prop").get_in(some), "drop")
        Path("prop").del_in(some)
        self.assertFalse(Path("prop").has_in(some))

    def test_descriptor(self):
        class TestDescriptor(object):
            def __get__(self, obj, cls):
                if obj is None:
                    return cls
                return obj.attr

            def __set__(self, obj, value):
                obj.attr = value

            def __delete__(self, obj):
                del obj.attr

        class Test(object):
            desc = TestDescriptor()

            def __init__(self, desc):
                self.desc = desc

        test = Test("attribute")

        self.assertEqual(Path("desc").get_in(test), 'attribute')
        self.assertEqual(WildPath("*").get_in(test), {'attr': 'attribute',
                                                      'desc': 'attribute'})
        Path("desc").set_in(test, "betribute")
        self.assertEqual(Path("desc").get_in(test), 'betribute')
        WildPath("*").set_in(test, "cetribute")  # sets both
        self.assertEqual(Path("desc").get_in(test), 'cetribute')

        Path("desc").del_in(test)
        self.assertEqual(Path("desc").has_in(test), False)

    def test_class_items(self):
        class Test(object):
            dont_find_1 = 1

            @classmethod
            def dont_find_2(cls):
                pass

            @staticmethod
            def dont_find_3(cls):
                pass

        self.assertEqual(list(Path.items(Test())), [])


class TestDocs(TestBase):

    def test_path_example(self):
        agenda = deepcopy(self.agenda)
        try:
            from wildpath.paths import Path

            path = Path("items.0.duration")
            assert str(path) == "items.0.duration"  # str(..) returns the original path string

            duration = path.get_in(agenda)  # retrieves value at path location
            assert duration == "5 minutes"

            path._set_in(agenda, "10 minutes")  # sets value at path location
            assert path.get_in(agenda) == "10 minutes"

            path._del_in(agenda)  # deletes key-value at path loation
            assert path.has_in(agenda) == False  # has_in checks the presenca of a value at the path location
        except Exception as e:
            self.fail(e)

    def test_wild_path_example(self):
        agenda = deepcopy(self.agenda)
        try:
            from wildpath.paths import WildPath

            wildpath = WildPath("items.*.duration")

            durations = wildpath.get_in(agenda)  # retrieves all the durations of the items on the agenda
            assert durations == ["5 minutes", "25 minutes", "5 minutes"]

            wildpath._set_in(agenda, ["10 minutes", "50 minutes", "10 minutes"])  # setting all the values,
            assert wildpath.get_in(agenda) == ["10 minutes", "50 minutes", "10 minutes"]

            wildpath._set_in(agenda, "30 minutes")  # or replacing all with a single value,
            assert wildpath.get_in(agenda) == ["30 minutes", "30 minutes", "30 minutes"]

            wildpath._del_in(agenda)  # delete all the items at wildpath from the structure
            assert wildpath.has_in(agenda) == False  # `has_in` checks if all the items at wildpath are there

            # To get the start and end time of the meeting:

            wildpath = WildPath("*_time")
            assert wildpath.get_in(agenda) == {"start_time": "10:00", "end_time": "11:00"}

            #  WildPath supports a number of wildcard(-like) constructs

            # '|' lets you select multiple keys

            wildpath = WildPath("start_time|end_time")
            assert wildpath.get_in(agenda) == {"start_time": "10:00", "end_time": "11:00"}

            # '?' stands for a single character
            assert WildPath("item?").get_in({"item1": "chair", "item2": "table", "count": 2}) == {"item1": "chair",
                                                                                                  "item2": "table"}

            # '!' at the start of a key definition in a wildpath:
            assert WildPath("!item?").get_in({"item1": "chair", "item2": "table", "count": 2}) == {"count": 2}

            wildpath = WildPath("start_time|end_time")
            assert wildpath.get_in(agenda) == {"start_time": "10:00", "end_time": "11:00"}

            # similarly it supports slices as wildcard like path=elements

            wildpath = WildPath("items.:2.name")  #  takes the names of the first 2 items
            assert wildpath.get_in(agenda) == ["opening", "progress"]

            wildpath = WildPath("items.-1::-1.name")
            assert wildpath.get_in(agenda) == ["opening", "progress", "closing"]
        except Exception as e:
            self.fail(e)

    def test_iterator_examples(self):
        agenda = deepcopy(self.agenda)
        try:
            from wildpath.paths import Path

            for path, value in sorted(Path.items(agenda)):
                print(" ".join([str(path), ":", value]))
            for path, value in sorted(Path.items(agenda, all=True)):
                print(" ".join([str(path), ":", str(value)]))

            new_dict = {}

            for path, value in Path.items(agenda, all=True):
                path._set_in(new_dict, value)

            assert new_dict == agenda
        except Exception as e:
            self.fail(e)

    def test_google_example(self):
        def get_geo_locations(json_route):
            geo_locs = []
            for json_step in json_route["routes"][0]["legs"][0]["steps"]:  # there is only 1 route and 1 leg in the response
                geo_locs.append({"start_location": json_step["start_location"],
                                 "end_location": json_step["end_location"]})
            return geo_locs

        geo_locations_1 = get_geo_locations(self.google_route)

        location_path = WildPath("routes.0.legs.0.steps.*.*_location")
        geo_locations_2 = location_path.get_in(self.google_route)
        self.assertEqual(geo_locations_1, geo_locations_2)

    def test_path_tuple_example(self):
        assert Path("a.b") + Path("c") == Path("a.b.c")
        assert Path("a.b.c")[1:] == Path("b.c")
        assert repr(Path("a.b.c")) == "('a', 'b', 'c')"

        #  however (this is not the tuple implementation of __str__):
        assert str(Path("a.b.c")) == "a.b.c"


if __name__ == "__main__":
    unittest.main()
