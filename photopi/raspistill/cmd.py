import os
from subprocess import Popen, PIPE
from threading import Thread

class RaspistillCmd(Thread):

    def Test(path=None, verbose=False):
        spec = RaspistillCmd(path=path,
            output="test.jpg",
            verbose=verbose,
            quality=5)
        return spec

    def Timelapse(path=None, label=None, interval=None, timeout=None, verbose=True, filestart=None):
        if not interval:
            interval = 5000
        if not timeout:
            timeout = 32400000

        spec = RaspistillCmd(
            path=os.path.join(path, label),
            output="image%06d.jpg",
            interval=interval,
            timeout=timeout,
            verbose=verbose,
            filestart=filestart)
        return spec

    def __init__(self, label=None, output=None, quality=75, path=None, verbose=False, timeout=None, interval=None):
        Thread.__init__(self)
        self.path = path
        self.label = label
        self.output = output
        self.quality = quality
        self.verbose = verbose
        self.timeout = timeout
        self.interval = interval

    def __str__(self):
        return str(self.__dict__)

    def _get_cmd(self):
        args = []
        if self.output:
            args = args + ["-o", os.path.join(self.path, self.output)]
        if self.quality:
            args = args + ["-q", str(self.quality)]
        if self.verbose:
            args = args + ["-v"]
        if self.interval:
            args = args + ["-tl", str(self.interval)]
        if self.timeout:
            args = args + ["-t", str(self.timeout)]
        if self.filestart:
            args = args + ["-fs", str(self.filestart)]

        cmd = ["raspistill"] + args
        return cmd

    def run(self):
        p = Popen(self._get_cmd(), stdin=PIPE, stdout=PIPE, stderr=PIPE)

        self.stdout = p.stdout

        self.output, self.err = p.communicate()
        self.returncode = p.returncode

