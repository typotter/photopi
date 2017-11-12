""" Defines the Module for working with bundles of images. """

import fnmatch
import logging
import os

from photopi.core.borg import Borg
from photopi.bundle.spec import BundleSort, BundleSpec

class BundleModule(Borg):
    """ Module for working with bundles of images. """
    def __init__(self):
        Borg.__init__(self)
        self._log = logging.getLogger(
            "{}.{}".format(self.__class__.__module__, self.__class__.__name__))

    def main(self, args, config):
        """ Determines which command to run and runs it. """
        self._log.debug(args)
        self._log.debug(config)

        if args['ls']:
            self._ls(config, args)

    def _ls(self, config, args):
        """ List the bundles accessible by this node."""

        if args['--node']:
            nodes = [{args['--node'], config['storage_nodes'][args['--node']]}]
        else:
            nodes = config['storage_nodes'].items()

        bundles = {}
        for key, path in nodes:
            bundles[key] = self._get_bundles(path, args['--device'], args['--label'])

        tupled = []
        for key, bundle in bundles.items():
            print(key)
            for device, labels in bundle.items():
                print("\t{}".format(device))
                for label in labels:
                    print("\t\t{}".format(label))
                    tupled.append((key, device, label))

        if len(tupled) == 1:
            (key, device, label) = tupled[0]
            spec = BundleSpec(device, label, config['storage_nodes'][key])
            print("Bundle has the following parts")
            print(spec.parts())

    def _get_bundles(self, path, device_lim=None, label_lim=None):

        archives = {}
        for root, devices, __ in os.walk(path):
            for device in devices:
                if device_lim and device != device_lim:
                    continue
                archives[device] = []
                for ___, ____, files in os.walk(os.path.join(root, device)):
                    for filename in fnmatch.filter(files, "*.tar.gz"):
                        label = BundleSort.get_label(filename)
                        if label_lim and label != label_lim:
                            continue
                        if label not in archives[device]:
                            archives[device].append(label)

        self._log.debug("archives found %s", archives)
        return archives

MODULE = ("bundle", BundleModule)
