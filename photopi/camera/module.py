""" Defines the Module for working the camera. """

import logging
import os

from photopi.bundle.spec import BundleSpec
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

        if args['continuous']:
            return self._continuous(args, config)

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

        self._log.info("test image captured")

        return cmd.run()

    def _continuous(self, args, config):
        # build a bundle for the continuouse shooting.
        bundle = BundleSpec.FromArgsAndConfig(args, config)
        self._log.debug(bundle)

        lastimage = bundle.last_image_number()
        if lastimage == -1:
            leadoff = 0
        else:
            leadoff = 100 - (lastimage % 100) + lastimage

        cmd = RaspistillCmd.Continuous(
            label=bundle.label,
            path=os.path.join(bundle.path),
            interval=args['--interval'],
            timeout=args['--timeout'],
            filestart=leadoff)

        os.makedirs(bundle.path, exist_ok=True)

        return cmd.run()

MODULE = ("camera", CameraModule)
