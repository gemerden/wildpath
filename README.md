#WildPath

A path abstraction to handle composite (e.g. JSON) objects in python.

##Introduction

This module is intended primarily as a practical tool to access data in compax data structures. Especially accessing multiple items usually requires for-loops or other constructs and there is no straightforward way to pass nested locations as single parameters. This module solves this problem by introducing 2 classes: `Path` and `WildPath`:
 
  - `Path` is optimized for speed, allows access to single items in the data structure,
  - `WildPath` allows wildcards for access to multiple items in the same call,
  - Both have iterators (in the common baseclass) to run through all paths and values in a data structure.
  
 ##Examples
 To show what this gets you in practice, here are some examples:
 
 Starting with a somewhat complex example structure:
 
 ```python
agenda = {
    "meeting": "progress on project X",
    "date": "2017-8-14",
    "time": ["10:00", "11:00"],
    "invited": ["Joe", "Ann", "Boo"],
    "items": [
        {
            "name": "opening",
            "time": "5 minutes",
            "subjects": ["purpose of the meeting"],
        },
        {
            "name": "progress",
            "time": "25 minutes",
            "subject": ["milestones", "project delays", "actions"],
        },
        {
            "name": "closing",
            "time": "5 minutes",
            "subject": ["questions", "roundup"],
        },
    ]
}
```

This might be a data used for every meeting in some tool. The 'Path' class let you get, set or delete items at a specific location:

```python
from wildpath.paths import Path

path = Path("items.0.time")

time = path.get_in(agenda)  # retrieves value at path location
assert time == "5 minutes"

path.set_in(agenda, "10 minutes")  # sets value at path location
assert path.get_in(agenda) == "10 minutes"

path.del_in(agenda)  # deletes key-value at path loation
try:
    path.get_in(agenda)
except KeyError:
    print(str(path)+ " is gone")
```

**Notes**:

 - `get_in` takes a default parameter, which is returned if a value does not exist at the path location,
 - if a data structure contains python objects, the Path methods will attempt to find values in the objects `__dict__`. 

##Prerequisites

What things you need to install the software and how to install them

###Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

#Give examples
##Installing

A step by step series of examples that tell you have to get a development env running

Say what the step will be

Give the example
And repeat

until finished
End with an example of getting some data out of the system or using it for a little demo

##Running the tests

Explain how to run the automated tests for this system

Break down into end to end tests

Explain what these tests test and why

Give an example
And coding style tests

Explain what these tests test and why

Give an example
Deployment

Add additional notes about how to deploy this on a live system


Please read CONTRIBUTING.md for details on our code of conduct, and the process for submitting pull requests to us.

##Versioning

We use SemVer for versioning. For the versions available, see the tags on this repository.

##Authors

Billie Thompson - Initial work - PurpleBooth
See also the list of contributors who participated in this project.

##License

This project is licensed under the MIT License - see the LICENSE.md file for details

##Acknowledgments

Hat tip to anyone who's code was used
Inspiration
etc