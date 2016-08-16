# -*- coding:utf-8 -*-

"""
    Cache Store.
    All cache related APis stay in this file.

    author: lwb@fronware
"""

from time import time
from copy import deepcopy, copy
from threading import Lock


class SimpleCache(object):
    """
        A simple in-memory store.
        APIs: 
            add, filter, exclude
            APIs are thread-safe.
    """

    def __init__(self, outdate_cond=None, timing=None):
        """
            input:
                outdate_cond
                    a callback,
                    which decide whether a cached is outdated
                    if None, no maintenance.
                timing:
                    a decimal
                    maintaining process will proceed at at least every `timing` secods.
                    if None, maintaining process before every action.
        """
        self.cache = []
        self.outdate_cond = outdate_cond
        if self.outdate_cond is not None:
            assert callable(self.outdate_cond)

        self.timing = timing


    def _exclude(self, exclude_cond=None):
        if exclude_cond:
            assert callable(exclude_cond)

            excluded = filter(
                lambda rec: exclude_cond(rec),
                self.cache
            )
            self.cache = filter(
                lambda rec: not exclude_cond(rec),
                self.cache
            )
        else:
            # remove all
            excluded = self.cache
            self.cache = []

        return excluded


    @property
    def maintain_deadline(self):
        if not hasattr(self, '_maintain_deadline'):
            if self.timing:
                self._maintain_deadline = time() + self.timing
            else:
                self._maintain_deadline = None

        return self._maintain_deadline

    @maintain_deadline.setter
    def maintain_deadline(self, value):
        self._maintain_deadline = value


    def maintain(self):
        """
            remove outdated records,
            according to the returned value of outdate_cond
        """
        if not self.outdate_cond:
            # no outdate condition, do not maintain.
            return

        if self.timing is None:
            self._exclude(self.outdate_cond)
        else:
            if time() >= self.maintain_deadline:
                self._exclude(self.outdate_cond)
                self.maintain_deadline = time() + self.timing

    # decorator
    def _maintained(method):
        def new_method(self, *args, **kwargs):
            self.maintain()
            return method(self, *args, **kwargs)
        return new_method


    @property
    def lock(self):
        if not hasattr(self, '_lock'):
            self._lock = Lock()

        return self._lock

    # decorator
    def _threadsafe(method):
        def new_method(self, *args, **kwargs):
            with self.lock:
                return method(self, *args, **kwargs)

        return new_method

    ##################
    # APIs
    ##################

    @_threadsafe
    @_maintained
    def __iter__(self):
        return iter(self.cache)

    @_threadsafe
    @_maintained
    def __getitem__(self, given):
        """
            input:
                given -> slice or index
        """
        return self.cache[given]

    @_threadsafe
    @_maintained
    def add(self, *records):
        """
            append records to cache.
        """
        self.cache.extend(records)

    @_threadsafe
    @_maintained
    def filter(self, filter_cond=None):
        """
            filter cached message with callback filter_cond
        """

        if filter_cond:
            assert callable(filter_cond)
            return filter(filter_cond, self.cache)
        else:
            return copy(self.cache)

    @_threadsafe
    @_maintained
    def exclude(self, exclude_cond=None):
        """
            exclude cached data according to exclude_cond
        """

        return self._exclude(exclude_cond)

    del _maintained
    del _threadsafe


#####################
# improvements:
#   1) redis may be a better choice. (which has built-in persistence)
#####################


if __name__ == '__main__':

    # test case

    from threading import Thread
    from time import sleep
    from random import randrange
    import json

    def read_task(cache, timeout=10):
        deadline = time() + timeout
        while time() <= deadline:
            print '---------------'
            print json.dumps(
                cache.filter(), 
                indent=4
            )
            print ''
            sleep(0.5)

    def write_task(cache, timeout=10):
        deadline = time() + timeout
        while time() <= deadline:
            cache.add(
                {'a': 'invalid', 'b': randrange(1, 10)}, 
                {'a': randrange(10,20), 'b': randrange(1, 10)}
            )
            sleep(0.7)

    cache = SimpleCache(
        outdate_cond=lambda rec: dict(rec).get('a') == 'invalid',
        timing=2
    )

    read_t = Thread(target=read_task, args=(cache, 10))
    write_t = Thread(target=write_task, args=(cache, 10))

    read_t.start()
    write_t.start()

    read_t.join()
    write_t.join()

