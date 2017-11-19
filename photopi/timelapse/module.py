from datetime import datetime
import logging
import os
import time

from photopi.core.borg import Borg
from photopi.core.cmd import RsyncCmd
from photopi.timelapse.spec import TimelapseSpec
from photopi.timelapse.cmd import MencoderCmd
from photopi.bundle.spec import BundleSpec
from photopi.bundle.module import BundleModule


def _prompt(prompt, options):
    result = None
    rng = range(len(options))
    while result is None or result not in rng:
        for i in rng:
            print("{}) {}".format(i, options[i]))
        try:
            result = int(input(prompt))
        except ValueError:
            result = None

    return options[result]

class TimelapseModule(Borg):
    """ Module for building timelapse videos. """
    def __init__(self):
        Borg.__init__(self)
        self._log = logging.getLogger(
            "{}.{}".format(self.__class__.__module__, self.__class__.__name__))

    def main(self, args, config):
        """ Main method. """
        spec = BundleSpec.FromArgsAndConfig(args, config)
        self._log.debug("Timelapse Module for %s", spec)

        return self._suite(args, config)

    def _suite(self, args, config):
        done = False
        while not done:
            self._log.debug(args)
            self._log.debug(config)

            bundle_mod = BundleModule()
            bundles = bundle_mod.filter_bundles(args, config)

            self._log.info(bundles)

            nodes = sorted(list(bundles.keys()))
            if not nodes:
                self._log.info("No nodes reachable. Exiting")
                continue
            elif len(nodes) > 1:
                node = _prompt("Select Node> ", nodes)
            else:
                node = nodes[0]

            devices = sorted(bundles[node])
            if not devices:
                self._log.info("No devices. Exiting")
                continue
            elif len(devices) > 1:
                device = _prompt("Select Device> ", devices)
            else:
                device = devices[0]

            labels = sorted(bundles[node][device])
            if not labels:
                self._log.info("No bundles. Exiting")
                continue
            elif len(labels) > 1:
                label = _prompt("Select Label> ", labels)
            else:
                label = labels[0]

            bundle = BundleSpec(device, label, config.storage_node(node))

            print("Processing {}/{}/{}".format(node, device, label))

            loaded = bundle_mod.expand(bundle, config)

            if not loaded:
                self._log.error("Unable to load")
                return False

            destnode = _prompt("Select destination node> ",
                               list(config.storage_nodes.keys()))

            destpath = config.storage_node(destnode)
            if not destpath:
                self._log.warning("node [%s] is not configured",
                                  args['--node'])
                return False

            fname = input("Enter timelapse name> ")

            dest_avi = os.path.join(destpath,
                                    "{}-{}-timelapse-{}.avi".format(
                                        bundle.device, bundle.label, fname))

            loadedpath = os.path.join(config.swap_path, bundle.device,
                                      bundle.label)

            cmd = MencoderCmd.AllFiles(loadedpath, dest_avi)
            cmd.start()

            while not cmd.is_alive():
                time.sleep(1)

            cont = input("timelapse complete. Another? Y/n")
            done = cont == "y" or cont == "Y"

        return True


MODULE = ("timelapse", TimelapseModule)
