# -*- coding:utf-8 -*-


def proxy_method(member, method):
    """
        call method on self.member or member() instead of self
        member: 
            a callable which has a member named method
            or a string indicate the name of a member on self
        method:
            proxied method


        usage:
            class A(object):
                def __init__(self, list_value):
                    self.value = list_value

                __getitem__ = proxy_method('value', '__getitem__')

            a = A([1,2,3])
            print a[0]  # 1
    """
    def proxy(self, *args, **kwargs):
        if callable(attr):
            attr = attr()
        else:
            attr = getattr(self, attr)
        return getattr(attr, method)(*args, **kwargs)
    return proxy

