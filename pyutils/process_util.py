# -*- coding:utf-8 -*-

import os, sys
import signal

import resource
import errno


def close_all_files():
    maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[0]
    if maxfd == resource.RLIM_INFINITY:
        maxfd = 1024

    for fd in xrange(maxfd):
        try:
            os.close(fd)
        except OSError as e:
            if e.errno == errno.EBADF:
                continue
            else:
                raise


class Daemon(object):
    def __init__(self, pidfile, func=None, stdin=os.devnull, stdout=os.devnull, stderr=os.devnull):
        self.pidfn = pidfile
        self.func = func
        self.stdin_fn = stdin
        self.stdout_fn = stdout
        self.stderr_fn = stderr

    def _setup_context(self):
        close_all_files()
        os.umask(0)
        os.chdir('/')
        sys.stdin = open(self.stdin_fn, 'r')
        sys.stdout = open(self.stdout_fn, 'a', False)
        sys.stderr = open(self.stderr_fn, 'a', False)

    @property
    def pid(self):
        if not os.path.exists(self.pidfn):
            return None
        with open(self.pidfn, 'r') as f:
            try:
                return int(f.read())
            except ValueError as e:
                # pid file is broken.
                return None

    @pid.setter
    def pid(self, value):
        with open(self.pidfn, 'w') as f:
            f.write(str(value))


    def del_pid_file(self):
        if os.path.exists(self.pidfn):
            os.remove(self.pidfn)

    def run(self):
        assert callable(self.func), 'invalid function'
        return self.func()

    def start(self):
        pid = os.fork()
        assert pid >= 0, 'failed to call fork'

        if pid > 0:
            # reap first child
            os.waitpid(pid, 0)
            return

        # new session:
        #   detach from parent's session (terminal)
        #   become leader of the new session.
        #   becom leader of new process group.
        os.setsid()

        pid2 = os.fork()
        assert pid2 >= 0, 'failed to call fork secondly'
        if pid2 > 0:
            # make grandchild an orphan
            os._exit(0)

        self._setup_context()

        # here's the daemon.
        assert (self.pid is None), 'daemon is running, %d' % self.pid
        self.pid = os.getpid()
        try:
            self.run()
        finally:
            self.del_pid_file()

        os._exit(0)

    def signal(self, sig):
        return os.kill(self.pid, sig)

    def stop(self):
        return self.signal(signal.SIGTERM)

    @property
    def running(self):
        return self.pid is not None

    def cleanup(self):
        assert not self.running(), 'daemon is running.'
        self.del_pid_file()


if __name__ == '__main__':
    std_log = '/home/lwb/test.log'
    pidfn = '/home/lwb/test.pid'
    
    class Termination(BaseException):
        pass
    
    def sigterm_handler(signum, frame):
        raise Termination, 'exit from SIGTERM'
    
    def task():
        signal.signal(signal.SIGTERM, sigterm_handler)
    
        import time
        try:
            while 1:
                print 'heart beat:', time.time()
                time.sleep(0.5)
        except Termination as e:
            print 'end'
    
    daemon = Daemon(
        pidfn,
        func=task, 
        stdout=std_log,
        stderr=std_log
    )

    daemon.start()


