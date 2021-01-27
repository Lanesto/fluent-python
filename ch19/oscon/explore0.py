#!/usr/local/bin/python
from keyword import iskeyword
from collections import abc


class FrozenJSON:
    """

    >>> from osconfeed import load
    >>> raw_feed = load()
    >>> feed = FrozenJSON(raw_feed)
    >>> len(feed.Schedule.speakers)
    354
    >>> sorted(feed.Schedule.keys())
    ['conferences', 'events', 'speakers', 'venues']
    >>> for key, value in sorted(feed.Schedule.items()):  # doctest: +ELLIPSIS
    ...     print('{:3} {}'.format(len(value), key))
    ...
      1 conferences
    485 events
    354 speakers
     53 venues
    >>> feed.Schedule.speakers[-1].name
    'Carina C. Zona'
    >>> talk = feed.Schedule.events[40]
    >>> type(talk)
    <class '__main__.FrozenJSON'>
    >>> talk.name
    'There *Will* Be Bugs'
    >>> talk.speakers
    [3471, 5199]
    >>> talk.flavor
    Traceback (most recent call last):
        ...
    KeyError: 'flavor'
    >>> talk.class
    Traceback (most recent call last):
        ...
    SyntaxError: invalid syntax
    >>> data = FrozenJSON({'class': 1, '2be': 3})
    >>> data.class
    Traceback (most recent call last):
        ...
    SyntaxError: invalid syntax
    >>> data.class_
    1
    >>> data.2be
    Traceback (most recent call last):
        ...
    SyntaxError: invalid syntax
    """

    def __new__(cls, arg):
        if isinstance(arg, abc.Mapping):
            return super().__new__(cls)
        elif isinstance(arg, abc.MutableSequence):
            return [cls(item) for item in arg]
        else:
            return arg

    def __init__(self, mapping):
        new_mapping = {}
        for key, value in mapping.items():
            if iskeyword(key):
                key += "_"

            new_mapping[key] = value

        self.__data = new_mapping

    def __getattr__(self, name):
        if hasattr(self.__data, name):
            return getattr(self.__data, name)
        else:
            cls = type(self)
            return cls(self.__data[name])


if __name__ == "__main__":
    import doctest

    doctest.testmod()
