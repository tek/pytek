import sys
from itertools import izip

def zip_fill(default, *seqs):
    filler = lambda *seq: [el if el is not None else default for el in seq]
    return map(filler, *seqs)

class Silencer(object):
    """ Context manager that suppresses output to stdout.

    """
    def __enter__(self):
        sys.stdout = self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = sys.__stdout__

    def write(self, data):
        pass

def repr_params(*params):
    return '(' + ', '.join(map(repr, params)) + ')'

def str_list(l, j=', '):
    return j.join(map(str, l))

def choose(lst, indicator):
    return [l for l, i in izip(lst, indicator) if i]

def make_list(*args):
    result = []
    for a in args:
        if a is not None:
            if isinstance(a, list):
                result.extend(filter(lambda e: e is not None, a))
            else:
                result.append(a)
    return result
