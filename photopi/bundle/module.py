""" Defines the Module for working with bundles of images. """

from datetime import datetime
import fnmatch
import logging
import os
import shutil
import tarfile

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

        if args['zip']:
            return self._zip(config, args)

    def _buildspec(self, args, config):
        label = args["--label"]
        if not label:
            label = datetime.now().strftime("%Y-%m-%d")

        node = args["--node"] if args["--node"] else "local"
        srcpath = config.storage_node(node)
        if srcpath is None:
            self._log.error("Invalid node")
            return None

        return BundleSpec(args['--device'], label, srcpath)

    def _fragmentimages(self, spec, fragment, maxfiles):
        self._log.info("Moving image files for zip")

        if not maxfiles:
            maxfiles = 1000

        images = spec.images()

        filestomove = images[:maxfiles]

        if filestomove:
            dest = fragment.dirname()
            os.mkdir(dest)

            for stream in filestomove:
                shutil.move(stream, dest)
            return True

        return False

    def _zip_files(self, newtarname, frag):
        files = frag.images()
        if not files:
            return False

        newtar = tarfile.open(newtarname, "w|gz")

        self._log.info("Zipping %d images", len(files))
        for fname in files:
            basename = os.path.basename(fname)
            self._log.info("adding %s", basename)
            newtar.add(fname, basename)

        newtar.close()
        self._log.info("Zipped %d files", len(files))

        lastnum = frag.last_image_number()

        self._log.info("removing files")
        for fname in files:
            os.remove(fname)
        self._log.info("Done zipping part %d", frag.partnum)

        donefile = frag.donefilename

        stream = open(donefile, "w")
        stream.write(str(lastnum))
        stream.close()
        return True

    def _zip(self, config, args):
        spec = self._buildspec(args, config)
        if not spec:
            return False
        self._log.debug("Zipping Bundle %s/%s", spec.device, spec.label)

        frag = None

        if args['--part']:
            frag = spec.part_spec(int(args['--part']))
        else:
            frag = spec.next_part_spec()
            if not self._fragmentimages(spec, frag,
                                        int(args['--maxfilecount'])):
                self._log.info("no images to move")

        newtarname = None

        tardest = config.storage_node(args['--dest'])

        if tardest and not args['--rsync']:
            newtarname = self._altdest(tardest, frag, args["--verifycifs"])

        if not newtarname:
            newtarname = frag.tarfilename

        if self._zip_files(newtarname, frag):
            if args['--rsync'] and tardest:
                self._log.info("Using rsync to move %s to %s",
                               newtarname, tardest)
                destname = self._altdest(tardest, frag, args["--verifycifs"])
                if destname is None:
                    self._log.warning("Alternate Destination is blank")
                else:
                    rsynccmd = RsyncCmd.Move(newtarname, destname)
                    rsynccmd.run()
                    rsynccmd = RsyncCmd.Move(frag.donefilename,
                                             os.path.dirname(destname))
                    rsynccmd.run()
            elif args['--rsync']:
                self._log.error(
                    "rsync flag must be used in conjunction with dest")
            return True

        self._log.warning("No images found at %s/%s/%d", spec.device,
                          spec.label, frag.partnum)
        return True

    def _altdest(self, tardest, spec, verifycifs):
        basepath = os.path.join(tardest, spec.device)
        if not verifycifs or self._is_mounted(tardest):
            if not os.path.isdir(basepath):
                os.makedirs(basepath)
            newtarname = os.path.join(basepath,
                                      os.path.basename(spec.tarfilename))
            return newtarname
        else:
            self._log.error("Warning. Expected mount path is not mounted.")
            return None

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
                RsyncCmd(fname, destpath, args['--move']).run()

    def _ls(self, config, args):
        """ List the bundles accessible by this node."""

        if args['--node']:
            nodes = [{args['--node'], config['storage_nodes'][args['--node']]}]
        else:
            nodes = config['storage_nodes'].items()

        bundles = {}
        for key, path in nodes:
            bundles[key] = self._get_bundles(path, args['--device'],
                                             args['--label'])

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

    @staticmethod
    def _is_mounted(path):
        while os.path.dirname(path) != path:
            if os.path.ismount(path):
                return True
            path = os.path.dirname(path)
        return False

MODULE = ("bundle", BundleModule)
