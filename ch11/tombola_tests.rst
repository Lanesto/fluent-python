============
Tombola Test
============

Blahblah

Init and load::

    >>> balls = list(range(3))
    >>> globe = ConcreteTombola(balls)
    >>> globe.loaded()
    True
    >>> globe.inspect()
    (0, 1, 2)

Pick::

    >>> picks = []
    >>> picks.append(globe.pick())
    >>> picks.append(globe.pick())
    >>> picks.append(globe.pick())

Check status

    >>> globe.loaded()
    False
    >>> sorted(picks) == balls
    True

Load it back

    >>> globe.load(balls)
    >>> globe.loaded()
    True
    >>> picks = [globe.pick() for i in balls]
    >>> globe.loaded()
    False

LookupError on pick from empty

    >>> globe = ConcreteTombola([])
    >>> try:
    ...     globe.pick()
    ... except LookupError:
    ...     print('OK')
    OK

Test on 100 balls

    >>> balls = list(range(100))
    >>> globe = ConcreteTombola(balls)
    >>> picks = []
    >>> while globe.inspect():
    ...     picks.append(globe.pick())
    >>> len(picks) == len(balls)
    True
    >>> set(picks) == set(balls)
    True

Check order is changed

    >>> picks != balls
    True
    >>> picks[::-1] != balls
    True
