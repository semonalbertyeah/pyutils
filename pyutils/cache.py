# -*- coding:utf-8 -*-

"""
    Cache Store.
    All cache related APis stay in this file.

    author: lwb@fronware
"""

from time import time
from copy import deepcopy, copy
# from threading import Lock
from threading import local
import sqlite3

from .thread_util import mthread_safe


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


    # @property
    # def lock(self):
    #     if not hasattr(self, '_lock'):
    #         self._lock = Lock()

    #     return self._lock

    # # decorator
    # def _threadsafe(method):
    #     def new_method(self, *args, **kwargs):
    #         with self.lock:
    #             return method(self, *args, **kwargs)

    #     return new_method

    ##################
    # APIs
    ##################

    # @_threadsafe
    @mthread_safe
    @_maintained
    def __iter__(self):
        return iter(self.cache)

    # @_threadsafe
    @mthread_safe
    @_maintained
    def __getitem__(self, given):
        """
            input:
                given -> slice or index
        """
        return self.cache[given]

    # @_threadsafe
    @mthread_safe
    @_maintained
    def add(self, *records):
        """
            append records to cache.
        """
        self.cache.extend(records)

    # @_threadsafe
    @mthread_safe
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

    # @_threadsafe
    @mthread_safe
    @_maintained
    def exclude(self, exclude_cond=None):
        """
            exclude cached data according to exclude_cond
        """

        return self._exclude(exclude_cond)

    del _maintained
    # del _threadsafe


try:
    import cPickle as pickle
except ImportError, e:
    import pickle


class SqliteStoreValue(object):
    def __init__(self, value):
        self.value = value

    @staticmethod
    def dumps(store_v):
        assert isinstance(store_v, SqliteStoreValue)
        return pickle.dumps(store_v.value)

    @staticmethod
    def loads(raw):
        return SqliteStoreValue(pickle.loads(raw))


class SqliteStore(object):

    tab_name = 'litestore'

    def __init__(self, path=':memory:', value_type=SqliteStoreValue, converter=None, adapter=None):
        self.vtype= value_type
        self.dbpath = path
        self.vtype_name = value_type.__name__

        # ---- value_type.loads and value_type.dumps must be staticmethod ----
        self.converter = converter or getattr(value_type, 'loads', None) or pickle.loads
        self.adapter = adapter or getattr(value_type, 'dumps', None) or pickle.dumps

        self.local = local()
        self._init_db()


    def _init_db(self):
        sqlite3.register_adapter(self.vtype, self.adapter)
        sqlite3.register_converter(self.vtype_name, self.converter)

        self.db.execute('''
            CREATE TABLE IF NOT EXISTS %s(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                value %s
            )
        ''' % (self.tab_name, self.vtype_name))
        self.db.commit()


    def get_db(self):

        db = sqlite3.connect(self.dbpath, detect_types=sqlite3.PARSE_DECLTYPES)

        db.create_function('check_filter', 1, self._check_filter)
        db.create_function('check_exclude', 1, self._check_exclude)
        db.execute('''
            CREATE TABLE IF NOT EXISTS %s(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                value %s
            )
        ''' % (self.tab_name, self.vtype_name))
        db.commit()

        return db


    @property
    def db(self):
        if not hasattr(self.local, 'db'):
            self.local.db = self.get_db()

        return self.local.db


    def get_cols(self):
        # self.cursor.execute("SELECT * FROM %s LIMIT 1;" % self.tab_name)
        # self.cursor.fetchall()
        # return [desc[0] for desc in self.cursor.description]

        cursor = self.db.execute("SELECT * FROM %s LIMIT 1;" % self.tab_name)
        cursor.fetchall()
        return [desc[0] for desc in cursor.description]


    @mthread_safe
    def add(self, *values):
        print '\nadd'
        if not values:
            return

        values = [
                (v if isinstance(v, self.vtype) else self.vtype(v), )
                for v in values
            ]
        # self.cursor.executemany('INSERT INTO %s(value) VALUES(?)' % self.tab_name, values)
        self.db.executemany('INSERT INTO %s(value) VALUES(?)' % self.tab_name, values)
        print 'add - before commit'
        self.db.commit()
        print 'add end\n'


    def _check_filter(self, raw_value):
        if self._filter_conds:
            value = self.converter(raw_value)
            return int(
                    all([cond(value) for cond in self._filter_conds])
                )
        else:
            return int(True)

    @mthread_safe
    def filter(self, *filter_conds):
        self._filter_conds = filter_conds

        # self.cursor.execute('SELECT value FROM %s WHERE check_filter(value);' % self.tab_name)
        # values = [row[0] for row in self.cursor.fetchall()]
        cursor = self.db.execute('SELECT value FROM %s WHERE check_filter(value);' % self.tab_name)
        values = [row[0] for row in cursor.fetchall()]
        if self.vtype is SqliteStoreValue:
            values = [v.value for v in values]

        self._filter_conds = []
        return values


    def _check_exclude(self, raw_value):
        if self._exc_conds:
            value = self.converter(raw_value)
            return int(all([cond(value) for cond in self._exc_conds]))
        else:
            return int(True)

    @mthread_safe
    def exclude(self, *exclude_conds):
        print '\nexclude:'
        values = self.filter(*exclude_conds)
        print 'values:', values

        self._exc_conds = exclude_conds

        # self.cursor.execute('DELETE FROM %s WHERE check_exclude(value);' % self.tab_name)
        self.db.execute('DELETE FROM %s WHERE check_exclude(value);' % self.tab_name)
        self.db.commit()

        self._exc_conds = []
        print 'end exclude\n'
        return values




#####################
# improvements:
#   1) redis may be a better choice. (which has built-in persistence)
#####################


#########################
# unit tests
#########################

import unittest


class TestSqliteStore(unittest.TestCase):
    def test_basic(self):
        cache = SqliteStore()

        msgs = [{'v': 1}, {'v':2}, {'v': 3}]
        cache.add(*msgs)

        # fmsgs = [msg.value for msg in cache.filter()]
        fmsgs = cache.filter()
        self.assertEqual(fmsgs, msgs)

        fmsgs = cache.exclude()
        self.assertEqual(fmsgs, msgs)

        fmsgs = cache.filter()
        self.assertEqual(len(fmsgs), 0)


    def test_custom_types(self):
        import json

        class DictValue(object):
            def __init__(self, d):
                assert isinstance(d, dict)
                self.dict_v = d

            @staticmethod
            def loads(raw):
                return DictValue(json.loads(raw))

            @staticmethod
            def dumps(dv):
                return json.dumps(dv.dict_v)

            def __eq__(self, other):
                return self.dict_v == other.dict_v

            def __ne__(self, other):
                return not self.__eq__(other)

        cache = SqliteStore(value_type=DictValue)

        msgs = [DictValue({'v': 1}), DictValue({'v':2}), DictValue({'v': 3})]
        cache.add(*msgs)

        # fmsgs = [msg.value for msg in cache.filter()]
        fmsgs = cache.filter()
        self.assertEqual(fmsgs, msgs)

        fmsgs = cache.exclude()
        self.assertEqual(fmsgs, msgs)

        fmsgs = cache.filter()
        self.assertEqual(len(fmsgs), 0)


    def test_cond(self):
        import json

        class DictValue(object):
            def __init__(self, d):
                assert isinstance(d, dict)
                self.dict_v = d

            @staticmethod
            def loads(raw):
                return DictValue(json.loads(raw))

            @staticmethod
            def dumps(dv):
                return json.dumps(dv.dict_v)

            def __eq__(self, other):
                return self.dict_v == other.dict_v

            def __ne__(self, other):
                return not self.__eq__(other)

        cache = SqliteStore(value_type=DictValue)

        msgs = [DictValue({'v': 1}), DictValue({'v':2}), DictValue({'v': 3})]
        cache.add(*msgs)

        fmsgs = cache.filter(lambda dv: dv.dict_v['v'] == 1)
        msg = fmsgs[0]
        self.assertEqual(len(fmsgs), 1)
        self.assertEqual(msg, msgs[0])

        fmsgs = cache.exclude(lambda dv: dv.dict_v['v'] == 1 or dv.dict_v['v'] == 2)
        self.assertEqual(len(fmsgs), 2)
        fmsgs = cache.exclude()
        self.assertEqual(fmsgs[0], msgs[2])




def test_SqliteStore_threadsafe():
    from . import thread_util
    import json, time, random

    class DictValue(object):
        def __init__(self, d):
            assert isinstance(d, dict)
            self.dict_v = d

        @staticmethod
        def loads(raw):
            return DictValue(json.loads(raw))

        @staticmethod
        def dumps(dv):
            return json.dumps(dv.dict_v)

        def __repr__(self):
            return repr(self.dict_v)

        def __eq__(self, other):
            return self.dict_v == other.dict_v

        def __ne__(self, other):
            return not self.__eq__(other)

    cache = SqliteStore(value_type=DictValue)

    @thread_util.threaded()
    def writer_t(cache, timeout=10):
        deadline = time.time() + timeout
        while time.time() <= deadline:
            print '------- writer ----------'
            cache.add(
                DictValue({'v': random.randint(0, 99)}),
                DictValue({'v': random.randint(0, 99)}),
                DictValue({'v': random.randint(0, 99)}),
            )
            time.sleep(0.9)

        print '----- writer end ------'

    @thread_util.threaded()
    def reader_t(cache, timeout=10):
        deadline = time.time() + timeout
        while time.time() <= deadline:
            print '---------- reader ----------'
            values = cache.exclude()
            print values
            time.sleep(0.5)
        print '---------- reader end ---------'

    wt = writer_t(cache)
    rt = reader_t(cache)

    wt.join()
    rt.join()



def test_SimpleCache_threadsafe():
    # test case SimpleCache

    from threading import Thread
    from time import sleep
    from random import randrange
    import json

    def read_task(cache, timeout=10):
        deadline = time() + timeout
        while time() <= deadline:
            print '---------------'
            print json.dumps(
                cache.exclude(), 
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




if __name__ == '__main__':

    print 'running'
    # unittest.main()
    test_SqliteStore_threadsafe()

    # test_SimpleCache_threadsafe()

