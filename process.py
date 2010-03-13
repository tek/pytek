from subprocess import Popen, PIPE

def process(args, wait=True, pipe=True):
    """ Run process 'args' and return the Popen instance after it's
        finished.

    """
    kwargs = {}
    if pipe:
        kwargs.update(stdout=PIPE, stderr=PIPE)
    proc = Popen(args, **kwargs)
    if wait:
        proc.wait()
    return proc
    
def process_output(args):
    """ runs process 'args' and returns a list containing the
        stdoutput lines without trailing newline characters """
    return [line.rstrip('\n') for line in process(args).stdout.readlines()]
