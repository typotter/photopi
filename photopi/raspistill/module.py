import os, time

from photopi.raspistill.cmd import RaspistillCmd
from photopi.core.photopi import get_label_or_default, get_base_dir, get_remote_dir, get_device
from photopi.timelapse.spec import TimelapseSpec

class RaspistillModule():

    def __init__(self):
        self._threads = []
        pass
    
    def main(self, args):
        if args["test"]:
            return self._do_test(args)
        if args["tl"]:
           return self._do_timelapse(args)


    def _do_timelapse(self, args):
        spec = TimelapseSpec(device=get_device(args), label=get_label_or_default(args), base=get_base_dir(args), remote=get_remote_dir(args))

        lastimage = spec.getLastImageNumber()
        if lastimage == -1:
            leadoff = 0
        else:
            leadoff = 100 - (lastimage % 100) + lastimage

        cmd = RaspistillCmd.Timelapse(
            label=spec.label,
            path=os.path.join(get_base_dir(args), spec.device),
            interval=args['--interval'],
            timeout=args['--timeout'],
            filestart=leadoff)

        os.makedirs(cmd.path, exist_ok=True)
  
        return self._run_spec(cmd)


    def _do_test(self, args):
        spec = RaspistillCmd.Test(path=get_base_dir(args))

        return self._run_spec(spec)

    def _run_spec(self, spec):
        spec.start()

        while True:
            time.sleep(1)
            if not spec.is_alive():
                break

        print(str(spec.output))
        print(str(spec.err))

        return spec.returncode == 0

def get_module():
    return RaspistillModule()
