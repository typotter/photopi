import os
from subprocess import Popen, PIPE
from threading import Thread

class RaspistillSpec(Thread):

    def Test(path=None):
        spec = RaspistillSpec(output = os.path.join(path, "test.jpg"), quality=5)
        return spec

    def __init__(self, label=None, output=None, quality=75):
        Thread.__init__(self)
        self.label = label
        self.output = output
        self.quality = quality

    def __str__(self):
        return str(self.__dict__)

    def _get_cmd(self):
        args = []
        if self.output:
            args = args + ["-o", self.output]
        if self.quality:
            args = args + ["-q", str(self.quality)]

        cmd = ["raspistill"] + args
        return cmd

    def run(self):
        p = Popen(self._get_cmd(), stdin=PIPE, stdout=PIPE, stderr=PIPE)

        self.stdout = p.stdout

        self.output, self.err = p.communicate()
        self.returncode = p.returncode

