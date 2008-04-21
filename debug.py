#!/usr/bin/env python

from __future__ import absolute_import
from os import environ

def debug(*message):
	if environ.has_key("PYTHON_DEBUG"): print "debug:", " ".join(str(part) for part in message)
