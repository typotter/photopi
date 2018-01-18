from datetime import datetime
import logging
import os
import shutil
import time

from photopi.core.borg import Borg
from photopi.core.cmd import RsyncCmd
from photopi.timelapse.spec import TimelapseSpec
from photopi.timelapse.cmd import MencoderCmd
from photopi.bundle.spec import BundleSpec
from photopi.bundle.module import BundleModule

_YESOPTS = ["y", "Y", ""]


def _prompt(prompt, options):
    options = sorted(options)
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
        self._bundlemod = BundleModule()

    def main(self, args, config, prefs=None):
        """ Main method. """
        spec = BundleSpec.FromArgsAndConfig(args, config)
        self._log.debug("Timelapse Module for %s", spec)

        if args['move']:
            return self._movearchives(spec, config)

        if args['auto']:
            return self._autosuite(args, config, prefs)

        return self._suite(args, config)

    def _autosuite(self, args, config, prefs):
        destnode = args['--dest']

        destpath = config.storage_node(destnode)
        if destpath is None:
            self._log.error("Invalid dest node")
            return False

        if not config.storage_node(args['--node']):
            self._log.info("Invalid source node")
            return False

        bundles = self._bundlemod.filter_bundles(args, config)

        specs = []
        path = config.storage_node(args['--node'])
        for device, labels in bundles[args['--node']].items():
            for label in sorted(labels):
                specs.append(BundleSpec(device, label, path))

        self._log.info(specs)

        for spec in specs:
            self._log.info("Loading %s", spec)
            self._bundlemod.expand(spec, config)

            dest_avi = os.path.join(destpath,
                                    "{}-{}-timelapse.avi".format(
                                        spec.label, spec.device))

            if not prefs:
                input("hit <enter> when ready to encode: {}/{}> ".format(
                              spec.device, spec.label))


            self._log.info("Writing %s", dest_avi)

            loadedpath = os.path.join(config.swap_path, spec.device,
                                      spec.label)

            cmd = MencoderCmd.AllFiles(loadedpath, dest_avi)
            cmd.start()

            while cmd.is_alive():
                time.sleep(1)

            if not prefs:
                fname = input("Enter timelapse name for {}/{} > ".format(
                              spec.device, spec.label))
            else:
                fname = ""

            finalfname = os.path.join(destpath,
                                      "{}-{}-timelapse-{}.avi".format(
                                          spec.label, spec.device, fname))
            shutil.move(dest_avi, finalfname)

            if not prefs:
                move = input("timelapse complete. Move archives? Y/n")
                if move in ["y", "Y"]:
                    return self._movearchives(spec, config)
            else:
                if prefs['move']:
                    destpath = config.storage_node(prefs['movedest'])
                    return self._bundlemod.fetch(spec, destpath, move=True)
            return True

    def _suite(self, args, config):
        done = False
        while not done:
            self._log.debug(args)
            self._log.debug(config)

            bundles = self._bundlemod.filter_bundles(args, config)

            self._log.debug(bundles)

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

            loaded = self._bundlemod.expand(bundle, config)

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

            move = input("timelapse complete. Move archives? Y/n")
            if move in _SELFOPTS:
                self._movearchives(bundle, config)

            cont = input("Process another? Y/n")
            done = cont in _YESOPTS

        return True

    def _movearchives(self, bundle, config):
        destnode = _prompt("Select destination node> ",
                           list(config.storage_nodes.keys()))
        destpath = config.storage_node(destnode)
        return self._bundlemod.fetch(bundle, destpath, move=True)

    def _suite(self, args, config):
        self._log.debug(args)
        self._log.debug(config)

        bundle_mod = BundleModule()
        bundles = bundle_mod.filter_bundles(args, config)

        self._log.info(bundles)

        nodes = sorted(list(bundles.keys()))
        if not nodes:
            self._log.info("No nodes reachable. Exiting")
            return True
        elif len(nodes) > 1:
            node = _prompt("Select Node> ", nodes)
        else:
            node = nodes[0]

        devices = sorted(bundles[node])
        if not devices:
            self._log.info("No devices. Exiting")
            return True
        elif len(devices) > 1:
            device = _prompt("Select Device> ", devices)
        else:
            device = devices[0]

        labels = sorted(bundles[node][device])
        if not labels:
            self._log.info("No bundles. Exiting")
            return True
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

        loadedpath = os.path.join(config.swap_path, bundle.device, bundle.label)

        cmd = MencoderCmd.AllFiles(loadedpath, dest_avi)
        cmd.start()

        while not cmd.is_alive():
            time.sleep(1)

        return cmd.returncode == 0 or cmd.returncode == None


MODULE = ("timelapse", TimelapseModule)
