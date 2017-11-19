""" Defines classes to interact with Bundles. """
from datetime import datetime
import glob
import logging
import os
import re

class BundleSpec:
    def FromArgsAndConfig(args, config):
        log = logging.getLogger("BundleSpec.FromArgsAndConfig")
        label = args["--label"]
        if not label:
            label = datetime.now().strftime("%Y-%m-%d")

        node = args["--node"] if args["--node"] else "local"
        srcpath = config.storage_node(node)
        if srcpath is None:
            log.error("Invalid node")
            return None


        device = args['--device']
        if not device:
            device = config.device_id

        return BundleSpec(device, label, srcpath)


    """ The group of images with the same label. """
    def __init__(self, device, label, base):
        self._log = logging.getLogger(
            "{}.{}".format(self.__class__.__module__, self.__class__.__name__))
        self._device = device
        self._label = label
        self._base = base

    def __str__(self):
        return '{}/{}/{}'.format(self._base, self._device, self._label)

    def clone(self, base):
        """ Clones this spec for a different node. """
        return BundleSpec(self.device, self.label, base)

    @property
    def label(self):
        """ The label of this spec. """
        return self._label

    @property
    def device(self):
        """ The device of this spec. """
        return self._device

    def part_spec(self, partnum):
        """ Gets the spec for the bundle fragment. """
        return BundleSpecPart(
            self.device, self.label, partnum, self._base, self)

    @property
    def path(self):
        """ The path where images for this bundle are located. """
        return os.path.join(self._base, self._device, self._label)

    def last_part_spec(self):
        """ Gets the last fragment of this bundle. """
        num = self.last_part_number()
        if num == 0:
            return None
        return self.part_spec(num)

    def next_part_spec(self):
        """ The next fragment that this bundle would use. """
        num = self.last_part_number()
        return self.part_spec(num + 1)

    def archives(self, done=False):
        """ List of archive filenames for this bundle. """
        partarchs = sorted(glob.glob(
            os.path.join(self._base, self._device,
                         "{}.*.tar.gz".format(self._label))),
                           key=BundleSort.partfile_number)
        self._log.debug(partarchs)

        if done:
            donearchives = []
            for archive in partarchs:
                partnum = BundleSort.partfile_number(archive)
                self._log.debug(partnum)
                partspec = self.part_spec(partnum)
                self._log.debug("Checking for %s %s", archive,
                                partspec.donefilename)
                if partspec.is_done():
                    donearchives.append(archive)
            return donearchives

        return partarchs

    def partdirs(self):
        """ List of fragment directories which exist for this bundle. """
        return glob.glob(
            os.path.join(self._base, self._device, self._label, "p*/"))

    def parts(self):
        """ Set of part numbers that exist for this bundle. """
        return sorted(list(set(
            list(map(BundleSort.partfile_number, self.archives())) +
            list(map(BundleSort.partdir_number, self.partdirs())))))

    def last_part_number(self):
        """ Last fragment number for this bundle. """
        parts = self.parts()
        if not parts:
            return 0
        return parts[-1]

    def last_image_number(self):
        """ Last image number in the bundle. """
        if self.last_part_number() == 0:
            images = self.images()
            if images:
                return BundleSort.image_number(images[-1])
            return -1
        return self.last_part_spec().last_image_number()


    def images(self, part=None):
        """ List the images for this bundle. """
        if part is not None:
            pattern = os.path.join(self.device, self.label, "p{}".format(part),
                                   "image*.jpg")
        else:
            pattern = os.path.join(self.device, self.label, "image*.jpg")
        self._log.debug(os.path.join(self._base, pattern))
        images = glob.glob(os.path.join(self._base, pattern))
        return sorted(images, key=BundleSort.image_number)


class BundleSpecPart:
    """ Represents a fragment of a bundle. """
    def __init__(self, device, label, partnum, base, parent=None):
        self.device = device
        self.label = label
        self.partnum = partnum
        self.parent = parent
        self._base = base

    @property
    def tarfilename(self):
        """ Filename of zipped tarball of images for this fragment. """
        return self._fname("{}.tar.gz")

    @property
    def donefilename(self):
        """ Filename for marking this fragment as complete. """
        return self._fname(".{}.done")

    @staticmethod
    def donefile_from_tarname(tarname):
        return ".{}.done".format(BundleSpecPart.filebase(tarname))

    @staticmethod
    def filebase(fname):
        match = re.search(r'\.?(.+)\.(tar\.gz)|(done)', fname)
        return int(match.group(1))

    def is_done(self):
        """ Indicates whether this fragment's archive has been written. """
        return os.path.isfile(self.donefilename)

    def dirname(self):
        """ Directory where the images in this bundle are stored. """
        return os.path.join(self._base, self.device, self.label,
                            "p{}".format(self.partnum))

    def _fname(self, pattern):
        return os.path.join(self._base, self.device,
                            pattern.format(
                                "{}.{}.p{}".format(
                                    self.label, self.device, self.partnum)))

    def images(self):
        """ List of images in this fragment. """
        return self.parent.images(part=self.partnum)

    def last_image_number(self):
        """ Last image number in the bundle. """
        donefile = self.donefilename
        if os.path.isfile(donefile):
            stream = open(donefile, 'r')
            num = stream.read()
            return int(num)
        images = self.images()
        if images:
            return BundleSort.image_number(images[-1])
        if self.partnum == 0:
            return -1
        prevpart = self.parent.part_spec(self.partnum - 1)
        if prevpart is not None:
            return prevpart.get_last_image_number()

        return -1


class BundleSort:
    """ Collection of methods for extracting elements of filenames. """

    @staticmethod
    def image_number(fname):
        """ Extract the image number from a filename. """
        fname = os.path.basename(fname)
        match = re.search(r'image(\d+)', fname)
        return int(match.group(1))

    @staticmethod
    def get_label(filename):
        """ Extract the label from a filename. """
        fname = os.path.basename(filename)
        match = re.search(r'(\d+-\d+-\d+)', fname)
        return match.group(1)

    @staticmethod
    def partfile_number(fname):
        """ Extract the part number from a filename. """
        fname = os.path.basename(fname)
        match = re.search(r'p(\d+)\.tar\.gz', fname)
        return int(match.group(1))

    @staticmethod
    def partdir_number(fname):
        """ Extract the part number from a directory. """
        match = re.search(r'\/p(\d+)', fname)
        return int(match.group(1))
