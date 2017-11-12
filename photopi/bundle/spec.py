""" Defines classes to interact with Bundles. """
import glob
import logging
import os
import re

class BundleSpec:
    """ The group of images with the same label. """
    def __init__(self, device, label, base):
        self._log = logging.getLogger(
            "{}.{}".format(self.__class__.__module__, self.__class__.__name__))
        self._device = device
        self._label = label
        self._base = base

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
                self._log.debug("Checking for %s", partspec.donefilename)
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
        return set(list(map(BundleSort.partfile_number, self.archives())) +
                   list(map(BundleSort.partdir_number, self.partdirs())))

    def images(self, part=None):
        """ List the images for this bundle. """
        if part is not None:
            pattern = os.path.join(self.device, self.label, "p{}".format(part),
                                   "image*.jpg")
        else:
            pattern = os.path.join(self.device, self.label, "image*.jpg")

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

    def is_done(self):
        """ Indicates whether this fragment's archive has been written. """
        return os.path.isfile(self.donefilename)

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
            return 0
        prevpart = self.parent.part_spec(self.partnum - 1)
        if prevpart is not None:
            return prevpart.get_last_image_number()

        return None


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
        match = re.search(r'p(\d+)', fname)
        return int(match.group(1))

    @staticmethod
    def partdir_number(fname):
        """ Extract the part number from a directory. """
        match = re.search(r'\/p(\d+)', fname)
        return int(match.group(1))
