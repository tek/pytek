from os import environ

def debug(*message):
    if environ.has_key("PYTHONDEBUG"): print "debug:", " ".join(str(part) for part in message)
