import glob, os, re

def get_partfile_number(fname):
    fname = os.path.basename(fname)
    m = re.search('p(\d+)', fname)

    return int(m.group(1))

def get_partdir_number(fname):
    m = re.search('\/p(\d+)', fname)

    return int(m.group(1))

def get_image_number(fname):
    fname = os.path.basename(fname)
    m = re.search('image(\d+)', fname)

    return int(m.group(1))

class TimelapseSpec():
    """ Timelapse data packet. """
    def __init__(self, device, label):
        self.device = device
        self.label = label

    def __str__(self):
        return str(self.__dict__)

    def getExtractDir(self, base=None):
        return os.path.join(self._baseorcwd(base), self.device, self.label)

    def getPartSpec(self, partnum):
        return TimelapsePartSpec(self.device, self.label, partnum, self)

    def getLastPartSpec(self, base=None):
        n = self.getLastPartNumber(base)
        if n == 0:
            return None
        return self.getPartSpec(n)

    def getNextPartSpec(self, base=None):
        n = self.getLastPartNumber(base)
        return self.getPartSpec(n + 1)

    def listImages(self, base=None, part=None, remote=None):
        """ List the images for this timelapse spec."""
        if part is not None:
            pattern = os.path.join(self.device, self.label, "p{}".format(part), "image*.jpg")
        else:
            pattern = os.path.join(self.device, self.label, "image*.jpg")

        images = self._get_files(pattern, base, remote)
        return sorted(images, key=get_image_number)

    def listArchives(self, base=None, remote=None):
        """ List the archives for this timelapse spec."""
        pattern = os.path.join(self.device, self.label) + "*.tar.gz"
        archives = self._get_files(pattern, base, remote)
        return sorted(archives, key=get_partfile_number)

    def getLastPartNumber(self, base=None):
        pattern = os.path.join(self.device, self.label, "p*/")
        ps = self._get_files(pattern, base, None)
        if len(ps) == 0:
            return 0
        pss = sorted(ps, key=get_partdir_number)
        return get_partdir_number(pss[-1])

    def _baseorcwd(self, base):
        if not base:
            return os.getcwd()
        return base

    def _get_files(self, pattern, base, remote):
        if not base:
            base = os.getcwd()

        files = glob.glob(os.path.join(base, pattern))

        if isinstance(remote, str):
            files += glob.glob(os.path.join(remote, pattern))
        elif remote is not None:
            for r in remote:
                files += glob.glob(os.path.join(r, pattern))
        return files

class TimelapsePartSpec():
    def __init__(self, device, label, partnum, tlspec=None):
        self.device = device
        self.label = label
        self.partnum = partnum
        self.parent = tlspec

    def getDir(self, base=None):
        if not base:
            base = os.getcwd()
        return os.path.join(base, self.device, self.label, "p{}".format(self.partnum))

    def getTarName(self, base=None):
        return os.path.join(base, self.device, "{}.{}.p{}.tar.gz".format(self.label, self.device, self.partnum))

    def listImages(self, base=None):
        return self.parent.listImages(base=base, part=self.partnum)

    def getDonefile(self, base=None):
        return os.path.join(base, self.device, "{}.{}.p{}.done".format(self.label, self.device, self.partnum))

    def getLastImageNum(self, base=None):
        df = self.getDonefile(base)
        if os.path.isfile(df):
            f = open(df, 'r')
            num = f.read()
            return int(num)
        images = self.listImages(base)
        if len(images) > 0:
            return get_image_number(images[-1])
        if self.partnum == 0:
            return 0
        prevpart = self.parent.getPartSpec(self.partnum - 1)
        if prevpart is not None:
            return prevpart.getLastImageNum(base)

        return None
