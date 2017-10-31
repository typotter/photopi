from datetime import datetime
import fnmatch, os, tarfile

from photopi.core.borg import Borg
from photopi.core.photopi import get_label_or_default, get_base_dir
from photopi.timelapse.spec import TimelapseSpec

def get_remote_dir(args):
    rem = None
    if 'PHOTOPI_REMOTE_TIMELAPSE' in os.environ:
        rem = os.environ['PHOTOPI_REMOTE_TIMELAPSE']
    elif args['--remote']:
        rem = args['--remote']
    else:
        return None

    if ";" in rem:
        return rem.split(";")
    else:
        return rem

class TimelapseModule(Borg):
    def __init__(self):
        Borg.__init__(self)

    def main(self, args):
        spec = TimelapseSpec(device=args["--device"], label=get_label_or_default(args))

        if args["load"]:
            return self.load_timelapse(spec, base=get_base_dir(args), remote=get_remote_dir(args))
        return false


    def load_timelapse(self, spec, base=None, remote=None):

        archives = spec.listArchives(base=base, remote=remote)

        print("Loading archives for {}/{}".format(spec.device, spec.label))

        print("Found {} archives".format(len(archives)))

        imagefiles = []

        extract_dest = os.path.join(base, spec.device, spec.label)

        for fname in archives:
            tarf = tarfile.open(fname, "r:gz")

            # extract
            print("extracting {}".format(fname))
            try:
                tarf.extractall(extract_dest)
            except IOError as e:
                print("I/O error({0}): {1}".format(e.errno, e.strerror))

        matches = []
        duplicates = []
        for root, dirnames, filenames in os.walk(extract_dest):
            for filename in fnmatch.filter(filenames, '*.jpg'):
                dest_fname = os.path.join(extract_dest, filename)
                src = os.path.join(root, filename)
                fs = os.stat(src).st_size
                if fs == 0:
                    print("{} is empty; skipping".format(filename))
                    continue
                if dest_fname in matches:
                    print("duplicate filename: {}".format(filename))
                    duplicates.append(src)
                elif os.path.isfile(dest_fname):
                    print("File {} exists, skipping".format(filename))
                    matches.append(dest_fname)
                else:
                  match = src
                  shutil.move(match, extract_dest)
                  matches.append(dest_fname)

        if len(matches) > 0:

            f = open(os.path.join(extract_dest, "files.txt"), "w")
            for m in matches:
                f.write(m)
                f.write("\n")
            f.close()

            f = open(os.path.join(extract_dest, "duplicates.txt"), "w")

            if len(duplicates) > 0:
                print("Warning! You have duplicate image filenames. Run `photopi fixtars` to fix")
         
            for m in duplicates:
                f.write(m)
                f.write("\n")
            f.close()

        print("Extracted {} files".format(len(matches)))

        return len(duplicates) == 0


def get_module():
    return TimelapseModule()
