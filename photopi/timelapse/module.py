from datetime import datetime
import fnmatch, os, shutil, subprocess, tarfile

from photopi.core.borg import Borg
from photopi.core.photopi import get_label_or_default, get_base_dir, get_remote_dir, get_device
from photopi.core.cmd import RsyncCmd
from photopi.timelapse.spec import TimelapseSpec
from photopi.timelapse.cmd import MencoderCmd

def _is_mounted(path):
    while os.path.dirname(path) != path:
        if os.path.ismount(path):
            return True
        path = os.path.dirname(path)
    return False

class TimelapseModule(Borg):
    def __init__(self):
        Borg.__init__(self)

    def main(self, args):
        label = args["--label"]
        if not label:
            label = datetime.now().strftime("%Y-%m-%d")

        spec = TimelapseSpec(device=get_device(args), label=label, base=get_base_dir(args), remote=get_remote_dir(args))

        if args["load"]:
            return self.load_timelapse(spec)

        if args["make"]:
            return self.make_timelapse(spec, args["--name"])

        if args["store"]:
            return self.store_timelapse_archives(spec, args["--dest"])

        if args["zip"]:
            return self._do_zip(spec, maxfiles=args["--maxfilecount"], tardest=args["--dest"], verifycifs = args["--verifycifs"], rsync = args["--rsync"])

        if args["clean"]:
            return self.clean_timelapse_temp(spec)

        return self._tl_suite(spec, args)

    def _prompt(self, prompt):
        ans = str(input(prompt + "Y/n? "))
        return ans == 'y' or ans == 'Y' or ans == ''

    def _tl_suite(self, spec, args):
        loaded = self.load_timelapse(spec)
        if loaded:
            print("Making Video")
            made = self.make_timelapse(spec, args["--name"])
            if made:
                print("Video Made")
                self._prompt("Store and clean working files?")
                stored = self.store_timelapse_archives(spec, args["--dest"])
                if stored:
                    cleaned = self.clean_timelapse_temp(spec)
                    if cleaned:
                        print("Working files cleaned")
                    else:
                        print("Problem cleaning working files")
                else:
                    print("Problem storing archives")
            else:
                print("Problem making video")
        else:
            print("Duplicate frames exist")

        return True

    def _do_zip(self, spec, maxfiles=1000, tardest=None, verifycifs=False, rsync=False):
        if maxfiles is not None:
            maxfiles = int(maxfiles)
        else:
            maxfiles = 1000

        images = spec.listImages()

        filestomove = images[:maxfiles]

        s = spec.getNextPartSpec()
        dest = s.getDir()
        os.mkdir(dest)

        for f in filestomove:
            shutil.move(f, dest)

        newtarname = None

<<<<<<< HEAD
        if tardest and not rsync:
            newtarname = self._altdest(tardest, spec, verifiycifs)
=======
        if tardest:
            basepath = os.path.join(tardest, s.device)
            if not verifycifs or os.path.ismount(tardest):
                if not os.path.isdir(basepath):
                    os.makedirs(basepath)
                newtarname = os.path.join(basepath, os.path.basename(s.getTarName()))
>>>>>>> draft verifycifs

        if not newtarname:
            newtarname = s.getTarName()


        newtar = tarfile.open(newtarname, "w|gz")

        movedfiles = s.listImages()

        print("Zipping {} images".format(len(movedfiles)))
        for f in movedfiles:
            bn = os.path.basename(f)
            print("adding {}".format(bn))
            newtar.add(f, bn)

        newtar.close()
        print("Zipped {} files".format(len(movedfiles)))

        lastnum = s.getLastImageNumber()

        print("removing files")
        for f in movedfiles:
            os.remove(f)
        print("Done zipping part {}".format(s.partnum))

        donefile = s.getDonefile()

        f = open(donefile, "w")
        f.write(str(lastnum))
        f.close()

        if rsync and tardest:
            print("Using rsync to move {} to {}".format(newtarname, tardest))
            destname = self._altdest(tardest, s, verifycifs) 
            if destname is None:
                print("Alternate Destination is blank")
            else:
                rsynccmd = RsyncCmd.Move(newtarname, destname)
                rsynccmd.run()
        elif rsync:
            print("rsync flag must be used in conjunction with dest")

        return True

    def _altdest(self, tardest, spec, verifycifs):
        basepath = os.path.join(tardest, spec.device)
        if not verifycifs or _is_mounted(tardest):
            if not os.path.isdir(basepath):
                os.makedirs(basepath)
            newtarname = os.path.join(basepath, os.path.basename(spec.getTarName()))
            return newtarname
        else:
            print("Warning. Expected network mount.")
            return None


    def make_timelapse(self, spec, video):
        print("making {}/{}".format(spec.device, spec.label))

        dest_avi = spec.getAviFname(video)

        cmd = MencoderCmd.AllFiles(spec.getExtractDir(), dest_avi)

        cmd.start()

        while not cmd.is_alive():
            time.sleep(1)

        return cmd.returncode == 0 or cmd.returncode == None

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
            except EOFError as e:
                print("EOF error")
                print(e)

        matches = []
        duplicates = []
        for root, dirnames, filenames in os.walk(extract_dest):
            for filename in fnmatch.filter(filenames, "*.jpg"):
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

    def store_timelapse_archives(self, spec, dest):
        print("Storing {}/{}".format(spec.device, spec.label))
        
        archives = spec.listArchives()

        print("{} archives to store".format(len(archives)))

        dest_dir = os.path.join(dest, spec.device)

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

        return True

    def clean_timelapse_temp(self, spec):
        print("Cleaning {}/{}".format(spec.device, spec.label))

        files = spec.listWorkingFiles()

        print("Removing {} files and directories".format(len(files)))
        for f in files:
            if os.path.isdir(f):
               shutil.rmtree(f)
            else:
                os.remove(f)

        print("Done removing working files")

        return True


def get_module():
    return TimelapseModule()
