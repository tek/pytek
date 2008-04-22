#!/usr/bin/env python

from subprocess import Popen, PIPE

def process_output(args):
	""" runs process 'args' and returns a list containing the
	    output lines without trailing newline characters """
	proc = Popen(args, stdout=PIPE, stderr=PIPE)
	proc.wait()
	ret = proc.stdout.readlines()
	for i, line in enumerate(ret): ret[i] = line.rstrip('\n')
	return ret

if __name__ == "__main__":
	import sys
	sys.exit(1)
