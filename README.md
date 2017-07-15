![Travis](https://travis-ci.org/gemerden/wildpath.svg?branch=master)

# WildPath

A path abstraction to access items in composite (e.g. JSON) objects in python.

## Introduction

This module is intended primarily as a practical tool to access data in complex data structures. Especially accessing multiple items usually requires for-loops or other constructs and there is no straightforward way to pass nested locations as single parameters. This module solves this problprecedenceoducing 2 classes: `Path` and `WildPath`:
 
  - `Path` is optimized for speed, allowing to get, set and delete single items in the data structure,
  - `WildPath` allows wildcards and boolean logic (and, or, not) in paths to get, set and delete to multiple items in one call,
  -  Both have iterators (in the common baseclass) to run through all paths and values in a data structure.

As an typical example we take the JSON response of a call to `maps.googleapis.com` for the route between 2 addresses. The response is about 400 lines of JSON if nicely formatted. However we will only be interested in the geo_locations of the individual steps (turn-by-turn instructions) of the route.

In normal code this would look something like (with `json_route` the result from the call to the google API):
```python
def get_geo_locations(json_route):
    geo_locs = []
    for json_step in json_route["routes"][0]["legs"][0]["steps"]:  #  there is only 1 route and 1 leg in the response
        geo_locs.append({"start_location": json_step["start_location"],
                         "end_location": json_step["end_location"]})
    return geo_locs
    
geo_locations = get_geo_locations(json_route)
```

Using `WildPath` the same result is obtained by:

```python
location_path = WildPath("routes.0.legs.0.steps.*.*_location")

geo_locations = location_path.get_in(json_route)
```

Both produce the same list of items:
```python
[
    {
        "start_location": {
            "lat": 52.0800134,
            "lng": 4.3271703
        },
        "end_location": {
            "lat": 52.0805958,
            "lng": 4.3286669
        }
    }, 
    ...
]
```
Essentially the function definition is replaced by a string, using `WildPath.get_in` for the correct lookup logic. This has some advantages:
 
 - Less lines of code means lower likelyhood of bugs,
 - Better readability and maintainablity (once you get used to the path-notation),
 - A `Path` or `WildPath` is easily serializable (`str(Path("a.b.c")) == "a.b.c"`), where a function definition is not.

## Prerequisites
The module `wildpaths` has been tested for both `python 2.7` and `python 3.6`. `wildpath` uses `boolean.py` (`pip install boolean.py`). Note the `.py`.
  
## Functionality
The **`Path`** class supports, with e.g. `path = Path("a.0.b")` and `obj = {"a": [{"b": 1}]}`:

 - `get_in`: getting items from data structures, as in: `path.get_in(obj)`,
 - `set_in`: setting values in data structures, as in: `path.set_in(obj, value)`,
 - `del_in`: deleting items from data structures, as in: `path.del_in(obj)`,
 - `has_in`: checking whether a value exists at path, as in: `path.has_in(obj)`,
 - `pop_in`: deleting and returning items from data structures, as in: `path.pop_in(obj)`.
 
 It also has some iterators that run through all paths and values in a data structure:
  
 - `Path.items(obj)`: iterator over all `(path, value)` tuples in the objects, 
 - `Path.paths(obj)`: iterator over all paths in the objects, 
 - `Path.values(obj)`: iterator over all values in the objects. 
 
The **`WildPath`** class supports the same functionality as `Path`, but with the following additions:

 - Keys referring to mappings (e.g. `dict`) or python class objects can contain wildcards: `WildPath("*.a*.b?")`, with `*` for any string and `?` for any single character. Wildcards use the standard python `fnmatch.fnmatchcase`,
 - Keys referring to sequences (e.g. `list`, `tuple`) can contain slices: `WildPath("1:3.::2")`, with `:` from standard python slice notation `some_list[start:stop:step]`,
 - All keys can contain boolean logic, using `&` for AND, `|` for OR and `!` for NOT: `WildPath("a*&!*b")`: keys starting with `'a'` and not ending with `'b'`.
 
Note that:
 - The iterator methods of `WildPath` return paths of type `WildPath`, instead of `Path`,
 - If a key, index or attribute is not found in the data, a `KeyError`, `IndexError` or `AttributeError` will be raised,
 - `get_in` can take a `default` parameter, that is returned if no value exists at the path location: `path.get_in(obj, None)`,
 - Using wildpaths will return instances of the classes in the original object for mappings and sequences. For (other) python objects it will return a `dict`. For example `WildPath(":2").get_in((1, 2, 3))` will return `(1, 2)`.


## Examples
Starting with this example structure of an agenda item in some tool:
 
 ```python
agenda = {
    "meeting": "progress on project X",
    "date": "2017-8-14",
    "start_time": "10:00",
    "end_time": "11:00",
    "invited": ["Joe", "Ann", "Boo"],
    "items": [
        {
            "name": "opening",
            "duration": "5 minutes",
            "subjects": ["purpose of the meeting"],
        },
        {
            "name": "progress",
            "duration": "25 minutes",
            "subjects": ["milestones", "project delays", "actions"],
        },
        {
            "name": "closing",
            "duration": "5 minutes",
            "subjects": ["questions", "roundup"],
        },
    ]
}
```


### class `Path`
The 'Path' class let you get, set or delete items at a specific location:

```python
from wildpath.paths import Path

path = Path("items.0.duration")
assert str(path) == "items.0.duration"  # str(..) returns the original path string

duration = path.get_in(agenda)  # retrieves value at path location
assert duration == "5 minutes"

path.set_in(agenda, "10 minutes")  # sets value at path location
assert path.get_in(agenda) == "10 minutes"

path.del_in(agenda)  # deletes key-value at path loation
assert path.has_in(agenda) == False  # has_in checks the presenca of a value at the path location
```
 
### class `WildPath`
`WildPath` supports the same API as `Path`, but additionally lets you use wildcards and slicing in the path definition to access multiple items in the structure (the `Path` class is there because for single lookups it is substantially faster):
 
```python
from wildpath.paths import WildPath

wildpath = WildPath("items.*.duration")  # basic 'star' notation
 
durations = wildpath.get_in(agenda)  # retrieves all the durations of the items on the agenda
assert durations == ["5 minutes", "25 minutes", "5 minutes"]

wildpath.set_in(agenda, ["10 minutes", "50 minutes", "10 minutes"])  # setting all the values, 
assert wildpath.get_in(agenda) == ["10 minutes", "50 minutes", "10 minutes"]

wildpath.set_in(agenda, "30 minutes")  #  or replacing all with a single value, 
assert wildpath.get_in(agenda) == ["30 minutes", "30 minutes", "30 minutes"]

wildpath.del_in(agenda)  # delete all the items at wildpath from the structure
assert wildpath.has_in(agenda) == False  # `has_in` checks if all the items at wildpath are there
```
To get the start and end time of the meeting:
```python
wildpath = WildPath("*_time")
assert wildpath.get_in(agenda) == {"start_time": "10:00", "end_time": "11:00"}
```
Similarly it supports slices as wildcard like path-elements 
```python
wildpath = WildPath("items.0:2.name")
assert wildpath.get_in(agenda) == ["opening", "progress"]

wildpath = WildPath("items.!0:2.name")  # slices can be negated
assert wildpath.get_in(agenda) == [ "closing"]

wildpath = WildPath("items.-1::-1.name")  # extended slicing also works, but orders are not reversed for a negative step parameter
assert wildpath.get_in(agenda) == ["opening", "progress", "closing"]
```

WildPath supports a boolean logic:
```python
# '|' is the OR operator

assert WildPath("start_time|end_time").get_in(agenda) == {"start_time": "10:00", "end_time": "11:00"}

# '&' is the AND operator

assert WildPath("start_*&*_time").get_in(agenda) == {"start_time": "10:00"}


# '!' is the NOT operator:

assert WildPath("!item?").get_in({"item1": "chair", "item2": "table", "count": 2}) == {"count": 2}

# parentheses can be use to indicate precedence:

assert WildPath("!(a|b)") != WildPath("!a|b")
```
Similarly it supports slices as wildcard like path-elements 
```python
wildpath = WildPath("items.0:2.name")
assert wildpath.get_in(agenda) == ["opening", "progress"]

wildpath = WildPath("items.!0:2.name")  # slices can be negated
assert wildpath.get_in(agenda) == [ "closing"]

wildpath = WildPath("items.-1::-1.name")  # extended slicing also works, but orders are not reversed for a negative step parameter
assert wildpath.get_in(agenda) == ["opening", "progress", "closing"]
```
**Notes**:
 - WildPath also supports attribute lookup in nested objects, list attributes in objects, etc.,
 - All the examples of `WildPath.get_in` also work for `set_in`, `del_in`, `pop_in` and `has_in`.

### Iterators
The Path classes also have some iterator classmethods defined:

```python
from wildpath.paths import Path

for path, value in Path.items(agenda):
    print(" ".join([str(path), ":", value]))
```
prints
```text
date : 2017-8-14
end_time : 11:00
invited.0 : Joe
invited.1 : Ann
invited.2 : Boo
items.0.duration : 5 minutes
items.0.name : opening
items.0.subjects.0 : purpose of the meeting
items.1.duration : 25 minutes
items.1.name : progress

etc...
```
To create an alternative representation of the datastructure:
```python
D = {str(path): value for path, value in Path.items(agenda)}
```
Path.items() has an optional argument `all` that if set to `True` will iterate over all path, value combination, including intermediary paths:
```python
from wildpath.paths import Path

for path, value in Path.items(agenda, all=True):
    print(" ".join([str(path), ":", value]))
```
will print:
```text
date : 2017-8-14
end_time : 11:00
invited : ['Joe', 'Ann', 'Boo']
invited.0 : Joe
invited.1 : Ann
invited.2 : Boo
items : [{'duration': '5 minutes', 'subjects': ['purpose of the meeting'], ...]
items.0 : {'duration': '5 minutes', 'subjects': ['purpose of the meeting'], 'name': 'opening'}
items.0.duration : 5 minutes
items.0.name : opening
items.0.subjects : ['purpose of the meeting']
items.0.subjects.0 : purpose of the meeting

etc...
```
With the `Path.items(obj, all=True)` and the ordering the items are produced, more manipulations are possible, e.g.:
````python
from datetime import datetime
from wildpath.paths import Path

sample = {
    "name": "sample",
    "times": [datetime(1999,1,2,3), datetime(1999,1,2,4)]
}

new_sample = {}
for path, value in Path.items(sample, all=True):
    if isinstance(value, datetime):
        value = str(value)  # all values of type datetime are converted to strings
    path.set_in(new_sample, value)
    
# new_sample is now serializable to JSON
````

**Notes**:
 - Currently these iterators cannot handle circular relationships. This will result in a RuntimeError (recursion depth) ,
 - The iterators return generators, not lists or dicts. To do this, use `list(Path.items(obj))`, `dict(Path.items(obj))`, 
 - These iterators can also be useful the get an alternative view on a datastructure: a starting point to define WildPaths,
 - To turn the items into a `dict` with string keys, use `dct = {str(p): v for p, v in Path.items(obj)}`,
 
### Path manipulations
`Path` and `WildPath` are subclasses of tuple (via BasePath), so (almost) all tuple methods can be used with both, e.g.:
```python
from wildpath.paths import Path

assert Path("a.b") + Path("c") == Path("a.b.c")
assert Path("a.b.c")[1:] == Path("b.c")
assert repr(Path("a.b.c")) == "('a', 'b', 'c')"

# however, this is not the tuple implementation for __str__:

assert str(Path("a.b.c")) == "a.b.c"

```
Note that some methods (like `__add__` and `path[1:]`) are overridden to return the correct class (Path or WildPath)
 
 
## Limitations
Because of the characters used to parse the paths, some keys in the target datastructures will cause the system to fail:
 - In python objects Path and WildPath will lookup keys in the instance `__dict__`. This means that some constructions like `property` and overridden `__getattr__` will not be taken into account,
 - for `Path` and `WildPath`: keys in Mappings (e.g. dict, OrderedDict) cannot contain a `.`,
 - for `WildPath`: keys in Mappings cannot contain the characters `*`, `?`, `!`, `|` and `&`, or to be precise, if they are present, they cannot be used in paths for lookups,
 - note that the `.` separator can easily be replaced in a subclass, allowing paths like `"a/b/3/x"` instead of `"a.b.3.x"` (and therefore path `"a/b.c/3/x"` with `b.c` a dictionary key):
 
 ```python
from wildpath.paths import Path, WildPath
 
class SlashPath(Path):
    sep = '/'
 
class WildSlashPath(WildPath):
    sep = '/'
```
Overriding `!`, `|` and `&` will take a little more work: override class-attribute `tokens` in `WildPath` and override `KeyParser.DEFAULT_TOKENS`. Currently there is no way to override hte tokens `*` and `?` in `WildPath`.

## Testing

The unittests are standard python unittests and can be run as such.

## Authors

Lars van Gemerden (rational-it) - initial code and documentation.

## License

This project is licensed under the license in LICENSE.txt.

## Acknowledgments

 - For convincing me to open-source this module, a big thanks to Jasper Hartong,
 - For the creators of the module `boolean.py`, thanks for making boolean parsing a lot easier.
