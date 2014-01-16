
import functools

def generated_list(func):
    @functools.wraps(func)
    def wrapper(self, *a, **kw):
        return list(func(self, *a, **kw))
    return wrapper

def generated_sum(func, init=0):
    @functools.wraps(func)
    def wrapper(self, *a, **kw):
        return sum(func(self, *a, **kw), init)
    return wrapper
