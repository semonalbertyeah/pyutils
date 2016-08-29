# -*- coding:utf-8 -*-


def is_subdict(con, sub):
    for key, value in sub.iteritems():
        if not con.has_key(key):
            return False
        if con[key] != value:
            return False

    return True

def merge_dicts(*dicts):
    result = {}
    for d in dicts:
        result.update(d)
    return result

def dict_has_keys(d, keys):
    if not isinstance(keys, (list, tuple)):
        keys = [keys]
    # return all (key in d for key in keys)
    for key in keys:
        if not d.has_key(key):
            return False
    return True

def sub_dict(d, *keys):
    return dict((key, d[key]) for key in keys if key in d)
