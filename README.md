# pyutils
various python utilities

## cls.py 
1. `class singleton(object)`

> create a singleton

```python
    @singleton
    class A(Object):
        @property
        def a(self):
            return "some value"

        @a.setter
        def a(self, value):
            print("set value of a")

        def func(self):
            print("this is a function.")
    
    print A.a   # "some value"
    A.a = 3     # "set value of a"
    A.func()    # "this is a function."
```


## data.py

> some utilities to manipulate binary data.

## dict.py

> some utilities to manipulate dict.

## func.py
1. `proxy_method(property_name, method_name)`

> This is mainly used to create a wrapper for array.

```python

    class A(object):
        def __init__(self, list_value):
            self.value = list_value
        __getitem__ = proxy_method('value', '__getitem__')
    a = A([1,2,3])
    print a[0]  # 1

```

## process_util.py
> process utilities

1. `daemonized(pidfile, **options)`

> make calling of func in a daemon
> options:
>    stdin -> default: os.devnull
>    stdout -> default: os.devnull
>    stderr -> default: os.devnull

```python
    pidfile = '/var/run/test.pid'
    logfile = '/var/log/test.log'
    @daemonized(pidfile, stdout=logfile, stderr=logfile)
    def test_daemon(header, info='heartbeat'):
        import time
        while True:
            print '%s - %s' % (header, info)
            time.sleep(0.5)
    test_daemon.start()
    print test_daemon.pid
    print test_daemon.running   # True
    test_daemon.stop()  # send SIGTERM
```


2. `class SignalContext(object)`

> A convient context to handle linux signals.

```python
    sig_context = SignalContext()
    class Termination(BaseException):
        pass
    @sig_context.on(signal.SIGTERM)
    def termination(signum, stack):
        raise Termination, 'terminated'
    def main():
        import time
        try:
            with sig_context:
                while 1:
                    print 'heartbeat'
                    time.sleep(0.5)
        except Termination as e:
            print 'end'
    if __name__ == '__main__':
        main()  # keep print heartbeat until SIGTERM
```


## proxy.py
1. `class ListProxy(object)`

> proxying operation on part of a list

```python

    l = range(10)
    pl1 = ListProxy(l)
    pl2 = ListProxy(l, start=3, length=4)
    pl3 = ListProxy(l, start=3, stop=7)
    pl4 = ListProxy(l, start=3, stop=-4)    # if size of l is changed, pl4 will be changed

```


## thread_util.py

1. `threaded(**options)`

> make calling of func in a new thread
> options:
>   name -> default : decorated function name
>   daemon -> default : False
>   start -> default : True

```python
    @threaded(name='test_function', start=False, daemon=True)
    def test():
        print 'test'
    t = test()
    t.start()
    t.join()
```
 

2. `wait_threads(tasks, timeout=5)` 

> wait until all threads end, or timeout
> return False if timeout
