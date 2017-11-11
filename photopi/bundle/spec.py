""" Defines classes to interact with Bundles. """
import logging
import os
import re

class BundleSpec:
    """ Represents a bundle of images. """
    def __init__(self, device, label):
        self._log = logging.getLogger(
            "{}.{}".format(self.__class__.__module__, self.__class__.__name__))
        self._device = device
        self._label = label

    @property
    def label(self):
        """ The label of this spec. """
        return self._label

    @property
    def device(self):
        """ The device of this spec. """
        return self._device

class BundleSort:
    """ Collection of methods for extracting elements of filenames. """

    @staticmethod
    def get_label(filename):
        """ Extract the label from a filename. """
        fname = os.path.basename(filename)
        match = re.search(r'(\d+-\d+-\d+)', fname)
        return match.group(1)
