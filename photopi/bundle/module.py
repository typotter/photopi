""" Defines the Module for working with bundles of images. """

import fnmatch
import logging
import os

from photopi.core.borg import Borg
from photopi.core.cmd import RsyncCmd
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
            return self._ls(config, args)

        if args['fetch']:
            return self._fetch(config, args)

    def _fetch(self, config, args):
        srcnode = args['--src']
        self._log.info("Fetching bundles from %s", srcnode)

        srcpath = config.storage_node(srcnode)
        if srcpath is None:
            self._log.error("Invalid src node")
            return False

        bundles = self._get_bundles(srcpath, args['--device'], args['--label'])

        self._log.debug(bundles)

        if args['--dest']:
            destpath = config.storage_node(args['--dest'])
            if destpath is None:
                self._log.error("Invalid dest node")
                return False
        else:
            destpath = config.storage_node()

        specs = self._get_specs(bundles, srcpath)
        for spec in specs:
            for fname in spec.archives(done=args['--done']):
                RsyncCmd(fname, destpath).run()

    def _ls(self, config, args):
        """ List the bundles accessible by this node."""

        if args['--node']:
            nodes = [{args['--node'], config['storage_nodes'][args['--node']]}]
        else:
            nodes = config['storage_nodes'].items()

        bundles = {}
        for key, path in nodes:
            bundles[key] = self._get_bundles(path, args['--device'], args['--label'])

        self._log.debug("bundles found %s", bundles)

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
            for archive in spec.archives():
                print(archive)

        return True

    @staticmethod
    def _get_specs(bundles, path):
        specs = []
        for device, labels in bundles.items():
            for label in labels:
                specs.append(BundleSpec(device, label, path))
        return specs

    @staticmethod
    def _get_bundles(path, device_lim=None, label_lim=None):

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

        return archives

MODULE = ("bundle", BundleModule)
