#!/usr/local/bin/python
import asyncio
import itertools
import sys

CHAR_BACKSPACE = '\x08'


@asyncio.coroutine
def spin(msg):
    write, flush = sys.stdout.write, sys.stdout.flush
    status = ''
    for char in itertools.cycle('|/-\\'):
        status = f'{char} {msg}'
        write(status)
        flush()
        write(CHAR_BACKSPACE * len(status))
        try:
            yield from asyncio.sleep(0.1)
        except asyncio.CancelledError:
            # print('cancelled')
            break

    write(' ' * len(status) + CHAR_BACKSPACE * len(status))


@asyncio.coroutine
def slow_function():
    yield from asyncio.sleep(3)
    return 42


#                   / spinner       \
# main - supervisor - slow_function - supervisor - main
@asyncio.coroutine
def supervisor():
    spinner = asyncio.create_task(spin('thinking!'))
    print('spinner object:', spinner)
    result = yield from slow_function()
    spinner.cancel()
    return result


def main():
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(supervisor())
    loop.close()
    print('answer:', result)


if __name__ == '__main__':
    main()