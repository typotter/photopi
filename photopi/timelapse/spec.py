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

    def __init__(self, device, label, base=None, remote=None):
        self.device = device
        self.label = label
        self._base = self._baseorcwd(base)
        self._remote = remote

    def __str__(self):
        return str(self.__dict__)

    def getExtractDir(self):
        return os.path.join(self._base, self.device, self.label)

    def getPartSpec(self, partnum):
        return TimelapsePartSpec(self.device, self.label, partnum, self._base, self)

    def getLastPartSpec(self):
        n = self.getLastPartNumber()
        if n == 0:
            return None
        return self.getPartSpec(n)

    def getNextPartSpec(self):
        n = self.getLastPartNumber()
        return self.getPartSpec(n + 1)

    def listImages(self, part=None):
        """ List the images for this timelapse spec."""
        if part is not None:
            pattern = os.path.join(self.device, self.label, "p{}".format(part), "image*.jpg")
        else:
            pattern = os.path.join(self.device, self.label, "image*.jpg")

        images = self._get_files(pattern, self._base, self._remote)
        return sorted(images, key=get_image_number)

    def listWorkingFiles(self):
        pattern = os.path.join(self._base, self.device, self.label + "*")
        return glob.glob(pattern)

    def listArchives(self):
        """ List the archives for this timelapse spec."""
        pattern = os.path.join(self.device, self.label) + "*.tar.gz"
        archives = self._get_files(pattern, self._base, self._remote)
        return sorted(archives, key=get_partfile_number)

    def getLastPartNumber(self):
        pattern = os.path.join(self.device, self.label, "p*/")
        ps = self._get_files(pattern, self._base, None)
        if len(ps) == 0:
            return 0
        pss = sorted(ps, key=get_partdir_number)
        return get_partdir_number(pss[-1])

    def _baseorcwd(self, base):
        if not base:
            return os.getcwd()
        return base

    def getAviFname(self, videoname):
        return os.path.join(self._base,"{}-{}-timelapse-{}.avi".format(self.device, self.label, videoname))

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
    def __init__(self, device, label, partnum, base, tlspec=None):
        self.device = device
        self.label = label
        self.partnum = partnum
        self.parent = tlspec
        self._base = base

    def getDir(self):
        return os.path.join(self._base, self.device, self.label, "p{}".format(self.partnum))

    def getTarName(self):
        return os.path.join(self._base, self.device, "{}.{}.p{}.tar.gz".format(self.label, self.device, self.partnum))

    def listImages(self):
        return self.parent.listImages(part=self.partnum)

    def getDonefile(self):
        return os.path.join(self._base, self.device, "{}.{}.p{}.done".format(self.label, self.device, self.partnum))

    def getLastImageNum(self):
        df = self.getDonefile()
        if os.path.isfile(df):
            f = open(df, 'r')
            num = f.read()
            return int(num)
        images = self.listImages()
        if len(images) > 0:
            return get_image_number(images[-1])
        if self.partnum == 0:
            return 0
        prevpart = self.parent.getPartSpec(self.partnum - 1)
        if prevpart is not None:
            return prevpart.getLastImageNum()

        return None
