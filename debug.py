from os import environ

dodebug = environ.has_key("PYTHONDEBUG")

def debug(*message):
    if dodebug:
        print "debug:", " ".join(map(str, message))
