from datetime import datetime
import fnmatch, os, shutil, subprocess, tarfile

from photopi.core.borg import Borg
from photopi.core.photopi import get_label_or_default, get_base_dir, get_remote_dir
from photopi.timelapse.spec import TimelapseSpec
from photopi.timelapse.cmd import MencoderCmd

class TimelapseModule(Borg):
    def __init__(self):
        Borg.__init__(self)

    def main(self, args):
        label = args['--label']
        if not label:
            label = datetime.now().strftime("%Y-%m-%d")

        spec = TimelapseSpec(device=args["--device"], label=label, base=get_base_dir(args), remote=get_remote_dir(args))

        if args["load"]:
            return self.load_timelapse(spec)

        if args["make"]:
            return self.make_timelapse(spec, args['--name'])

        if args["load"]:
            return self.load_timelapse(spec)

        if args["zip"]:
            return self._do_zip(spec, maxfiles=int(args["--maxfilecount"]))

        return false


    def _do_zip(self, spec, maxfiles=1000):
        images = spec.listImages()

        filestomove = images[:maxfiles]

        s = spec.getNextPartSpec()
        dest = s.getDir()
        os.mkdir(dest)

        for f in filestomove:
            shutil.move(f, dest)

        newtarname = s.getTarName()

        newtar = tarfile.open(newtarname, "w|gz")

        movedfiles = s.listImages()

        print("Zipping images")
        for f in movedfiles:
            newtar.add(f, os.path.basename(f))

        newtar.close()
        print("Zipped {} files".format(len(movedfiles)))

        lastnum = s.getLastImageNum()

        print("removing files")
        for f in movedfiles:
            os.remove(f)
        print("Done zipping part {}".format(s.partnum))

        donefile = s.getDonefile()

        f = open(donefile, "w")
        f.write(str(lastnum))
        f.close()

        return True

    def make_timelapse(self, spec, video):

        print("making {}/{}".format(spec.device, spec.label))

        dest_avi = spec.getAviFname(video)

        cmd = MencoderCmd.AllFiles(spec.getExtractDir(), dest_avi)

        cmd.start()

        while not cmd.is_alive():
            time.sleep(1)

        return cmd.returncode == 0


    def load_timelapse(self, spec):

        archives = spec.listArchives()

        print("Found {} archives".format(len(archives)))

        imagefiles = []

        extract_dest = spec.getExtractDir()

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

    def store_timelapse_archives(args):
        device = args['--device']
        label = get_label(args)
        print("Storing {}/{}".format(device, label))
        
        base_dir = get_base_dir(args)
        remote_dir = get_remote_dir(args)
        archives = get_archives(device, label, base_dir=base_dir)

        print("{} archives to store".format(len(archives)))

        dest_dir = os.path.join(remote_dir, device)

        moved = 0
        for fname in archives:
            print("moving {}".format(fname))
            bn = os.path.basename(fname)
            destfn = os.path.join(dest_dir, bn)
            print("dest fn" + destfn)
            if os.path.isfile(destfn):
                print("{} exists, checking size".format(bn))
                ds = os.stat(fname).st_size
                bs = os.stat(destfn).st_size
                if bs == ds:
                  print("Skipping")
                  continue

            shutil.move(fname, dest_dir)
            moved = moved + 1

        print("Moved {}".format(moved))


def get_module():
    return TimelapseModule()
