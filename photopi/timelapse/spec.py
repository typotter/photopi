import glob, os, re

def get_partfile_number(fname):
    fname = os.path.basename(fname)
    m = re.search('p(\d+)', fname)

    return int(m.group(1))

class TimelapseSpec():
    """ Timelapse data packet. """
    def __init__(self, device, label):
        self.device = device
        self.label = label

    def __str__(self):
        return str(self.__dict__)

    def listArchives(self, base=None, remote=None):
        """ List the archives for this timelapse spec."""
        pattern = os.path.join(self.device, self.label) + "*.tar.gz"

        if not base:
            base = os.getcwd()

        archives = glob.glob(os.path.join(base, pattern))

        if isinstance(remote, str):
            archives += glob.glob(os.path.join(remote, pattern))
        elif remote is not None:
            for r in remote:
                archives += glob.glob(os.path.join(r, pattern))
        return sorted(archives, key=get_partfile_number)

