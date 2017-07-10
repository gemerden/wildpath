#WildPath

A path abstraction to handle composite (e.g. JSON) objects in python.

##Introduction

This module is intended primarily as a practical tool to access data in complex data structures. Especially accessing multiple items usually requires for-loops or other constructs and there is no straightforward way to pass nested locations as single parameters. This module solves this problem by introducing 2 classes: `Path` and `WildPath`:
 
  - `Path` is optimized for speed, allowing to get, set and delete single items in the data structure,
  - `WildPath` allows wildcards in paths to get the same access to multiple items in the same call,
  -  Both have iterators (in the common baseclass) to run through all paths and values in a data structure.

As an typical example we take the JSON response of a basic call to `maps.googleapis.com`, where we ask it for the route between 2 addresses. The response is about 400 lines of JSON if nicely formatted. However we will only be interested in the geo_locations of the individual steps (turn-by-turn instructions) of the route.

In traditional code this would look something like (with `json_route` the result from the call to the google API):
```python
def get_geo_locations(json_route):
    geo_locs = []
    for json_step in json_route["routes"][0]["legs"][0]["steps"]:  #  there is only 1 route and 1 leg in the response
        geo_locs.append({"start_location": json_step["start_location"],
                         "end_location": json_step["end_location"]})
    return geo_locs
    
geo_locations = get_geo_locations(json_route)
```

Using `WildPath` the same result would be obtained by:

```python
location_path = WildPath("routes.0.legs.0.steps.*.*_location")

geo_locations = location_path.get_in(json_route)
```

Both produce a list of items looking like this:
```python
{
    "start_location": {
        "lat": 52.0800134,
        "lng": 4.3271703
    },
    "end_location": {
        "lat": 52.0805958,
        "lng": 4.3286669
    }
}
```
Basically the function definition is replaced by a string, using `WildPath.get_in` for the correct lookup logic. This has some advantages:
 
 - Less lines of code means lower likelyhood of bugs,
 - Better readability and maintainablity (once you get used to the path-notation),
 - A `Path` or `WildPath` is easily serializable (`Path(str(path)) == path`), where a function definition isn't.


##Prerequisites
The module `wildpaths` has been tested for both `python 2.7` and `python 3.6`. The only dependencies are on standard python libraries.
  
##Examples
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


###class `Path`
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

**Notes**:
 - `Path.get_in(obj)` can take a `default` parameter, that is returned if no value exists at the path location,
 - `Path.pop_in(obj)` is also supported, removing the value at `path` in the object and returning it,
 - If a data structure contains python objects, the Path methods will attempt to find values in the objects `__dict__`,
 - If a key, index or attribute is not found in the data, a `KeyError`, `IndexError` or `AttributeError` will be raised,
 
###class `WildPath`
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
WildPath supports a number of additional wildcard(-like) constructs:
```python
# '|' lets you select multiple keys

wildpath = WildPath("start_time|end_time")
assert wildpath.get_in(agenda) == {"start_time": "10:00", "end_time": "11:00"}

# '?' stands for a single character

assert WildPath("item?").get_in({"item1": "chair", "item2": "table", "count": 2}) == {"item1": "chair", "item2": "table"}

# '!' at the start of a key definition negates the key (items are taken that do not match the rest of the key):

assert WildPath("!item?").get_in({"item1": "chair", "item2": "table", "count": 2}) == {"count": 2}
```
Similarly it supports slices as wildcard like path-elements 
```python
wildpath = WildPath("items.0:2.name")
assert wildpath.get_in(agenda) == ["opening", "progress"]

wildpath = WildPath("items.!0:2.name")  # slices can be negated
assert wildpath.get_in(agenda) == [ "closing"]

wildpath = WildPath("items.-1::-1.name")  # extended slicing also works, in this case reversing the order
assert wildpath.get_in(agenda) == [ "closing", "progress", "opening"]
```
**Notes**:
 - WildPath also supports attribute lookup in nested objects, list attributes in objects, etc.,
 - All the examples of `WildPath.get_in` also work for `set_in`, `del_in`, `pop_in` and `has_in`.

###Iterators
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
items.1.subjects.0 : milestones
items.1.subjects.1 : project delays
items.1.subjects.2 : actions
items.2.duration : 5 minutes
items.2.name : closing
items.2.subjects.0 : questions
items.2.subjects.1 : roundup
meeting : progress on project X
start_time : 10:00
```
To create an alternative representation of the datastructure:
```python
D = {str(path): value for path, value in Path.items(agenda)}
```
Path.items() has an optional argument `all` that if set to `True` will iterate over all path, value combination, including sub-paths of the paths above:
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
items : [{'duration': '5 minutes', 'subjects': ['purpose of the meeting'], 'name': 'opening'}, {'duration': '25 minutes', 'subjects': ['milestones', 'project delays', 'actions'], 'name': 'progress'}, {'duration': '5 minutes', 'subjects': ['questions', 'roundup'], 'name': 'closing'}]
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
        value = str(value)
    path.set_in(new_sample, value)
    
# new_sample is now serializable to JSON
````
You can also filter out specific items (e.g. None values) by adding an if statement in the loop. Doing this, take care to not remove subpaths from the items, as nested lists and dicts are not automatically created by `set_in`.

**Notes**:
 - As a convenience `Path.paths(obj)` and `Path.values(obj)` are also implemented, iterating over the paths and values of the data structure,
 - Currently these iterators cannot handle circular relationships. This will result in a RuntimeError (recursion depth) ,
 - The iterators return generators, not lists. To create lists, use `list(Path.items(obj))`, `list(Path.paths(obj))`, etc.
 - They are implemented on the baseclass of `Path` and `WildPath`, so you might as well use `WildPath.items(obj)`, etc.
 - These iterators can also be useful the get an alternative view on a datastructure: a starting point to define WildPaths,
 
### Path manipulations
Until here we have not changed paths once generated. However, since `Path` and `WildPath` are subclasses of of `list` (via BasePath), (almost?) all list methods can be used with both, e.g.:
```python
from wildpath.paths import Path

assert Path("a.b") + Path("c") == Path("a.b.c")
assert Path("a.b.c")[1:] == Path("b.c")
assert repr(Path("a.b.c")) == "['a', 'b', 'c']"

#  however

assert str(Path("a.b.c")) == "a.b.c"

```
**Notes**:
 - some methods (like `__add__` and `path[1:]`) are overridden to return the correct class (Path or WildPath)
 
 
##Restrictions
Because of the characters used to parse the paths, some keys in the terget datastructures will cause the system to fail:
 - In python objects Path and WildPath will lookup keys in the instance `__dict__`. This means that some constructions like `property` and overridden `__getattr__` will not be taken into account,
 - for `Path` and `WildPath`: keys in Mappings (e.g. dict, OrderedDict) cannot contain a `.`,
 - for `WildPath`: keys in Mappings cannot contain the characters `*`, `?`, `!` and `|`, or to be precise, if they are present, they cannot be used in paths for lookups,
 - note that the `.` separator can easily be replaced in a subclass, allowing paths like `"a/b/3/x"` instead of `"a.b.3.x"` (and therefore path `"a/b.c/3/x"` with `b.c` a dictionary key):
 
 ```python
from wildpath.paths import Path, WildPath
 
class SlashPath(Path):
    sep = '/'
 
class WildSlashPath(WildPath):
    sep = '/'
```
Currently there is no way to override the other meaningful characters in `WildPath`.

##Testing

The unittests are standard python unittests and can be run as such.

##Authors

Lars van Gemerden (rational-it) - initial code and documentation.

##License

This project is licensed under the MIT License - see the LICENSE.md file for details

##Acknowledgments

A big thanks to Jasper Hartong for convincing me to open-source this module.  