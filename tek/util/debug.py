
from os import environ

__all__ = ['dodebug']

dodebug = "PYTHONDEBUG" in environ
