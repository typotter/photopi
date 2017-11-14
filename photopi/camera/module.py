""" Defines the Module for working the camera. """

import logging

from photopi.camera.cmd import RaspistillCmd
from photopi.core.borg import Borg


class CameraModule(Borg):
    """ Module for working with the camera. """
    def __init__(self):
        Borg.__init__(self)
        self._log = logging.getLogger(
            "{}.{}".format(self.__class__.__module__, self.__class__.__name__))

    def main(self, args, config):
        """ Determines which command to run and runs it. """
        self._log.debug(args)
        self._log.debug(config)

        if args['test']:
            return self._test(args, config)

        return False

    def _test(self, args, config):
        if args['--node']:
            path = config.storage_node(args['--node'])
            if path is None:
                self._log.error("Invalid node")
                return False
        else:
            path = config.local_path

        cmd = RaspistillCmd.Test(path=path)

        return cmd.runandblock() == 0


MODULE = ("camera", CameraModule)
