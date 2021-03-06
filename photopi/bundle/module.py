""" Defines the Module for working with bundles of images. """

from datetime import datetime
import fnmatch
import logging
import os
import shutil
import tarfile
import zlib

from photopi.core.borg import Borg
from photopi.core.cmd import RsyncCmd
from photopi.bundle.spec import BundleSort, BundleSpec, BundleSpecPart

class BundleModule(Borg):
    """ Module for working with bundles of images. """
    def __init__(self):
        Borg.__init__(self)
        self._log = logging.getLogger(
            "{}.{}".format(self.__class__.__module__, self.__class__.__name__))

    def main(self, args, config, prefs=None):
        """ Determines which command to run and runs it. """
        self._log.debug(args)
        self._log.debug(config)

        if args['ls']:
            return self._ls(config, args)

        if args['fetch']:
            return self._fetch(config, args)

        if args['zip']:
            if args['orphans']:
                return self._ziporphans(config, args)
            return self._zip(config, args)

        if args['expand']:
            return self._expand(config, args)

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

    def _expand(self, config, args):
        spec = BundleSpec.FromArgsAndConfig(args, config)
        return self.expand(spec, config)

    def expand(self, spec, config):
        """ Expand the archives for the specified bundle to swap storage. """
        self._log.info("Expanding %s/%s", spec.device, spec.label)

        archives = spec.archives()
        self._log.debug("Found %d archives", len(archives))

        extract_dest = os.path.join(config.swap_path, spec.device, spec.label)
        extract_tmp = os.path.join(extract_dest, "tmp")

        if not os.path.isdir(extract_tmp):
            os.makedirs(extract_tmp)

        for fname in archives:
            try:
                tarf = tarfile.open(fname, "r:gz")

                # extract
                self._log.debug("extracting %s", fname)

                tarf.extractall(extract_tmp)
            except IOError as err:
                self._log.error("I/O error(%s): %s", err.errno, err.strerror)
            except EOFError as err:
                self._log.error("EOF error")
                self._log.error(err)
            except zlib.error as err:
                self._log.error("error")
                self._log.error(err)
            except tarfile.ReadError as err:
                self._log.error("error")
                self._log.error(err)

        matches = []
        duplicates = []
        for root, _, filenames in os.walk(extract_tmp):
            for filename in fnmatch.filter(filenames, "*.jpg"):
                dest_fname = os.path.join(extract_dest, filename)
                src = os.path.join(root, filename)
                filesize = os.stat(src).st_size
                if filesize == 0:
                    self._log.info("%s is empty; skipping", filename)
                    continue
                if dest_fname in matches:
                    self._log.info("duplicate filename: %s", filename)
                    duplicates.append(src)
                elif os.path.isfile(dest_fname):
                    self._log.info("File %s exists, skipping", filename)
                else:
                    match = src
                    shutil.move(match, extract_dest)
                    matches.append(dest_fname)

        self._log.info("Extracted %d files", len(matches))

        return True

    def _ziporphans(self, config, args):
        nodes = self._nodelist(args, config)
        if not nodes:
            return False

        device_lim = args['--device']
        label_lim = args['--label']

        for key, path in sorted(nodes):
            for device in sorted(os.listdir(path)):
                dev = os.path.join(path, device)
                if not os.path.isdir(dev) or (device_lim and device != device_lim):
                    continue

                for label in sorted(os.listdir(dev)):
                    ldir = os.path.join(dev, label)
                    if not os.path.isdir(ldir) or (label_lim and label != label_lim):
                        continue
                    spec = BundleSpec(device, label, path)

                    for p in spec.parts():
                        part = spec.part_spec(p)

                        if len(part.images()) > 0:
                            self._log.info("Zip %s/%s/%s", device, label, p)
                            self._zipster(spec, args, config, part=p)

                    while len(spec.images()) > 0:
                        self._log.info("Zip new bundle %s/%s",
                                       device, label)         
                        self._zipster(spec, args, config)
        return True  
  

    def _zip(self, config, args):
        spec = BundleSpec.FromArgsAndConfig(args, config)
        if not spec:
            return False
        self._log.debug("Zipping Bundle %s/%s", spec.device, spec.label)


        return self._zipster(spec, args, config, part=args['--part'])

    def _zipster(self, spec, args, config, part=None):
        if args['--dry']:
            self._log.info("Not zipping; dry run %s/%s", spec, part)
            return True

        frag = None

        if part:
            frag = spec.part_spec(int(part))
        else:
            frag = spec.next_part_spec()
            maxfiles = int(args['--maxfilecount']) if args['--maxfilecount'] else 1000
            if not self._fragmentimages(spec, frag, maxfiles):
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

    def fetch(self, bundles, destpath, done=False, move=False):
        """ Moves archives in bundle(s) to `dest`. """
        if isinstance(bundles, BundleSpec):
            bundles = [bundles]

        self._log.debug(bundles)

        self._log.info("Fetching bundles to %s", destpath)

        for spec in bundles:
            fetchdest = os.path.join(destpath, spec.device)
            if not os.path.isdir(fetchdest):
                os.makedirs(fetchdest)
            for fname in spec.archives(done=done):
                RsyncCmd(fname, fetchdest, move).run()
                if done:
                    donefile = os.path.join(
                        os.path.dirname(fname), 
                        BundleSpecPart.donefile_from_tarname(fname))
                    RsyncCmd(donefile, fetchdest, move).run()

        return True

    def _fetch(self, config, args):
        srcnode = args['--src']
        self._log.info("Fetching bundles from %s", srcnode)

        srcpath = config.storage_node(srcnode)
        if srcpath is None:
            self._log.error("Invalid src node")
            return False

        destpath = config.storage_node(
            args['--dest'] if args['--dest'] else "local")
        if destpath is None:
            self._log.error("Invalid dest node")
            return False

        bundles = self._get_bundles(srcpath, args['--device'], args['--label'])

        specs = self._get_specs(bundles, srcpath)

        return self.fetch(specs, destpath,
                          done=args['--done'], move=args['--move'])

    def filter_bundles(self, args, config):
        """
        Dict of node-device-labels for bundles matching criteria in args.
        """
        nodes = self._nodelist(args, config)
        if not nodes:
            return False

        bundles = {}
        for key, path in sorted(nodes):
            if os.path.isdir(path):
                bundles[key] = self._get_bundles(path, args['--device'],
                                                 args['--label'])

        self._log.debug("bundles found %s", bundles)
        return bundles

    def _nodelist(self, args, config):
        """ List of (nodename, nodepath) tuples. """
        node = args['--node']
        if node:
            nodepath = config.storage_node(node)
            if not nodepath:
                self._log.warning("node [%s] is not configured", args['--node'])
                return None
            return [(node, nodepath)]

        return config['storage_nodes'].items()

    def _ls(self, config, args):
        """ List the bundles accessible by this node."""

        bundles = self.filter_bundles(args, config)

        tupled = []
        for key, bundle in bundles.items():
            print(key)
            for device, labels in bundle.items():
                print("\t{}".format(device))
                for label in sorted(labels):
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

    def _get_bundles(self, path, device_lim=None, label_lim=None):

        archives = {}
        for device in sorted(os.listdir(path)):
            self._log.debug(device)
            dev = os.path.join(path, device)
            self._log.debug("Checking %s", dev)
            if not os.path.isdir(dev) or (device_lim and device != device_lim):
                continue
            archives[device] = []
            self._log.debug("Is Dir")
            for _, _, files in os.walk(os.path.join(path, device)):
                self._log.debug(files)
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
