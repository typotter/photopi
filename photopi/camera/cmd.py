""" Defines useful stuff for running `raspistill`. """

import logging
import os
import time

from subprocess import Popen, PIPE
from threading import Thread

from photopi.core.cmd import Cmd


class RaspistillCmd(Cmd):
    """ Class to manage running a `raspistill` command."""

    @staticmethod
    def Test(path=None, verbose=False):
        """ Take a low quality photo and save it to `test.jpg`. """
        cmd = RaspistillCmd(path=path,
            output="test.jpg",
            verbose=verbose,
            quality=5)
        return cmd

    @staticmethod
    def Continuous(path=None, label=None, interval=None, timeout=None,
                   verbose=True, filestart=None):
        """ Continuously take photos. """
        if not interval:
            interval = 5000
        if not timeout:
            timeout = 32400000

        cmd = RaspistillCmd(
            path=path,
            output="image%06d.jpg",
            interval=interval,
            timeout=timeout,
            verbose=verbose,
            filestart=filestart)
        return cmd

    def __init__(self, output=None, quality=75, path=None, verbose=False,
                 timeout=None, interval=None, filestart=None):
        Cmd.__init__(self)

        self._args = []
        if output:
            self._args += ["-o", os.path.join(path, output)]
        if quality:
            self._args += ["-q", str(quality)]
        if verbose:
            self._args += ["-v"]
        if interval:
            self._args += ["-tl", str(interval)]
        if timeout:
            self._args += ["-t", str(timeout)]
        if filestart:
            self._args += ["-fs", str(filestart)]

        self._log = logging.getLogger(
            "{}.{}".format(self.__class__.__module__, self.__class__.__name__))

    def _arguments(self):
        return self._args

    def _cmd(self):
        return "raspistill"
