import functools


def generated_list(func):
    @functools.wraps(func)
    def wrapper(*a, **kw):
        return list(func(*a, **kw))
    return wrapper


def generated_sum(init=0):
    def decorate(func):
        @functools.wraps(func)
        def wrapper(*a, **kw):
            return sum(func(*a, **kw), init)
        return wrapper
    return decorate
