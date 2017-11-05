from photopi.core.cmd import Cmd

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
