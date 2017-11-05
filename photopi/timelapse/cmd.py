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
        self._process = Popen(cmd)
        self.stdout = self._process.stdout
        self.output, self.err = self._process.communicate()
        self.returncode = self._process.returncode

class MencoderCmd(Cmd):

    def AllFiles(src, avi_fname):
        return MencoderCmd(avi_fname, "mf://{}/*.jpg".format(src))

    def CustomFilelist(manifest, avi_fname):
        return MencoderCmd(avi_fname, manifest)

    def __init__(self, avi_fname, manifest):
        Cmd.__init__(self)
        self._fname = avi_fname
        self._manifest = manifest

    def _cmd(self):
        return "mencoder"

    def _arguments(self):
        args = "-nosound -ovc lavc -lavcopts".split(" ")
        args += ["vcodec=mpeg4:aspect=16/9:vbitrate=8000000"]
        args += ["-vf", "scale=1920:1080"]
        args += ["-o", self._fname]
        args += ["-mf", "type=jpeg:fps=24", self._manifest]
        return args
