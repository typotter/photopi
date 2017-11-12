""" Defines classes to interact with Bundles. """
import glob
import logging
import os
import re

class BundleSpec:
    """ Represents a bundle of images. """
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

    def archives(self):
        """ List of archive filenames for this bundle. """
        partarchs = glob.glob(
            os.path.join(self._base, self._device,
                         "{}.*.tar.gz".format(self._label)))
        return partarchs

    def partdirs(self):
        """ List of fragment directories which exist for this bundle. """
        return glob.glob(
            os.path.join(self._base, self._device, self._label, "p*/"))

    def parts(self):
        """ Set of part numbers that exist for this bundle. """
        return set(list(map(BundleSort.partfile_number, self.archives())) +
                   list(map(BundleSort.partdir_number, self.partdirs())))

class BundleSort:
    """ Collection of methods for extracting elements of filenames. """

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
