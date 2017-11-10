import os
from subprocess import Popen, PIPE
from threading import Thread

class Cmd(Thread):
    def __init__(self):
        Thread.__init__(self)
        self._process = None
        self.stdout = None
        self.output = None
        self.returncode = None

    def stop(self):
       if self._process is not None:
          self._process.kill()

    def __str__(self):
        return str(self.__dict__)

    def _cmd(self):
        raise NotImplementedError("Please implement this method")

    def _arguments(self):
        raise NotImplementedError("Please implement this method")

    def run(self):
        cmd = self._arguments()
        cmd.insert(0, self._cmd())
        print(cmd)
        self._process = Popen(cmd)
        self.stdout = self._process.stdout
        self.output, self.err = self._process.communicate()
        self.returncode = self._process.returncode

class RsyncCmd(Cmd):
    def Move(src, dest):
        return RsyncCmd(src, dest, move=True)

    def __init__(self, src, dest, move=False):
        Cmd.__init__(self)
        self._src = src
        self._dest = dest
        self._args = ["-rvh", "--progress"]
        if move:
            self._args.append("--remove-source-files")

        self._args.append(src)
        self._args.append(dest)

    def _arguments(self):
        return self._args
    def _cmd(self):
        return "rsync"
